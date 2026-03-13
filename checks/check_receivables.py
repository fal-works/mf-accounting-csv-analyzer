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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_journal, month_key, parse_amount, parse_date, print_header, print_ok, print_warning


def check_receivables(rows: list[dict]) -> None:
    """売掛金・未払金の消込状況をチェックする。"""

    targets = {
        "売掛金": {"increase_side": "借方", "decrease_side": "貸方"},
        "未払金": {"increase_side": "貸方", "decrease_side": "借方"},
    }

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
            print_ok(f"{account}の取引はありません")
            continue

        print(f"  計上合計: {total_increase:>14,d}円")
        print(f"  消込合計: {total_decrease:>14,d}円")
        print(f"  差額残高: {balance:>14,d}円")

        # 月別の推移を表示
        all_months = sorted(set(monthly_increase.keys()) | set(monthly_decrease.keys()))
        if all_months:
            print()
            print(f"  {'月':>8s} {'計上':>12s} {'消込':>12s} {'累積残高':>12s}")
            print(f"  {'-'*8} {'-'*12} {'-'*12} {'-'*12}")
            running = 0
            for m in all_months:
                inc = monthly_increase.get(m, 0)
                dec = monthly_decrease.get(m, 0)
                running += inc - dec
                print(f"  {m:>8s} {inc:>12,d} {dec:>12,d} {running:>12,d}")

        # 年末残高が期首残高（1月の増加分の一部）と一致しない場合に警告
        if balance < 0:
            print_warning(
                f"{account}の消込が計上を上回っています（差額: {balance:,}円）。"
                "計上漏れの可能性があります"
            )
        elif balance > 0:
            # 残高がある場合は情報として表示（翌年繰越の可能性がある）
            print(f"\n  ※ 年末残高 {balance:,}円は翌年度に繰り越されます")


def main() -> None:
    parser = argparse.ArgumentParser(description="売掛金・未払金の滞留チェック")
    parser.add_argument("journal", help="仕訳帳CSVファイルのパス")
    args = parser.parse_args()

    journal = load_journal(args.journal)
    check_receivables(journal)
    print()


if __name__ == "__main__":
    main()
