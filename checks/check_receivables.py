#!/usr/bin/env python3
"""売掛金・未払金の滞留チェック。

使い方:
    python check_receivables.py <仕訳帳.csv>

チェック内容:
  売掛金の計上後に入金（消込）がされているか、
  未払金の計上後に支払（消込）がされているかを検証する。

  売掛金: 借方に計上 → 貸方で消込
  未払金: 貸方に計上 → 借方で消込

  年末時点で残高が残っている場合、翌年度の期首仕訳で引き継がれるため、
  年度内で完全に消込されていなくても直ちにエラーとはしない。
  ただし、計上と消込の差額（年末残高）を表示し、確認を促す。

出力:
  売掛金・未払金の計上合計・消込合計・差額（年末残高）。
  消込漏れの可能性がある場合は警告。
"""

import argparse
import sys
from collections import defaultdict

from checks.common import CheckResult, DataFileError, load_journal, month_key, parse_amount, parse_date, print_header, print_ok, print_warning

MULTI_YEAR = False


def check_receivables(rows: list[dict]) -> CheckResult:
    """売掛金・未払金の消込状況をチェックする。"""

    targets = {
        "売掛金": {"increase_side": "借方", "decrease_side": "貸方"},
        "未払金": {"increase_side": "貸方", "decrease_side": "借方"},
    }

    warnings = 0

    for account, config in targets.items():
        print_header(f"{account} 滞留チェック")

        inc_side = config["increase_side"]
        dec_side = config["decrease_side"]

        # 月別の増減を追跡
        monthly_increase: dict[str, int] = defaultdict(int)
        monthly_decrease: dict[str, int] = defaultdict(int)

        for row in rows:
            d = parse_date(row["取引日"])
            if d is None:
                continue
            mk = month_key(d)

            # 増加（売掛金なら借方計上、未払金なら貸方計上）
            if row[f"{inc_side}勘定科目"] == account:
                amt = parse_amount(row[f"{inc_side}金額(円)"])
                if amt is not None:
                    monthly_increase[mk] += amt

            # 減少（売掛金なら貸方消込、未払金なら借方消込）
            if row[f"{dec_side}勘定科目"] == account:
                amt = parse_amount(row[f"{dec_side}金額(円)"])
                if amt is not None:
                    monthly_decrease[mk] += amt

        total_increase = sum(monthly_increase.values())
        total_decrease = sum(monthly_decrease.values())
        balance = total_increase - total_decrease

        if total_increase == 0 and total_decrease == 0:
            print_ok(f"{account}取引なし")
            continue

        print(f"計上={total_increase:,} 消込={total_decrease:,} 残高={balance:,}")

        # 月別の推移を表示
        all_months = sorted(set(monthly_increase.keys()) | set(monthly_decrease.keys()))
        if all_months:
            print("月\t計上\t消込\t累積残高")
            running = 0
            for m in all_months:
                inc = monthly_increase.get(m, 0)
                dec = monthly_decrease.get(m, 0)
                running += inc - dec
                print(f"{m}\t{inc}\t{dec}\t{running}")

        if balance < 0:
            print_warning(f"{account}消込超過 差額{balance:,}円 計上漏れの可能性")
            warnings += 1
        elif balance > 0:
            print(f"年末残高{balance:,}円→翌年繰越")

    return CheckResult(warnings)


def main() -> None:
    parser = argparse.ArgumentParser(description="売掛金・未払金の滞留チェック")
    parser.add_argument("journal", help="仕訳帳CSVファイルのパス")
    args = parser.parse_args()

    try:
        journal = load_journal(args.journal)
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    result = check_receivables(journal)

    if result.warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
