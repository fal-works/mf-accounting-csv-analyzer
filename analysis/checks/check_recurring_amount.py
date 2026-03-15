#!/usr/bin/env python3
"""定期課金の金額異常値チェック。

使い方:
    uv run python check_recurring_amount.py <仕訳帳.csv>

チェック内容:
  毎月のように計上される経費について、特定月の金額が
  他月の中央値から大きく乖離していないかをチェックする。
  check_recurring.py が「月の欠落」を検出するのに対し、
  本スクリプトは「計上はあるが金額がおかしい」ケースを検出する。

  判定基準:
    - 年間で MIN_MONTHS 以上の月に計上がある科目×取引先の組み合わせを対象
    - ある月の合計金額が中央値から DEVIATION_RATIO 以上乖離していたら警告

出力:
  金額が中央値から大きく外れた取引の一覧。
"""

from collections import defaultdict

from analysis.common import (
    SKIP_ACCOUNTS_COMMON,
    CheckResult,
    median,
    month_key,
    parse_amount,
    parse_date,
    print_header,
    print_ok,
    print_warning,
    run_check_cli,
)
from analysis.journal_columns import SIDES, SUMMARY, TX_DATE

MULTI_YEAR = False

# この月数以上の計上があれば定期課金とみなす
MIN_MONTHS = 5

# 中央値からの乖離がこの割合を超えたら警告
DEVIATION_RATIO = 0.5

# 経費ではない科目（定期性の判定対象外）
SKIP_ACCOUNTS = SKIP_ACCOUNTS_COMMON | {"売上高"}


def _vendor_key(row: dict, side) -> str:
    """取引先の識別キーを返す。取引先フィールドが空なら摘要の先頭語を代用する。"""
    vendor = row[side.vendor]
    if vendor:
        return vendor
    summary = row[SUMMARY].strip()
    return summary.split()[0] if summary else ""


def check_recurring_amount(rows: list[dict]) -> CheckResult:
    """定期課金の金額異常値をチェックする。"""
    print_header("定期課金 金額異常値チェック")

    # (科目, 補助科目, 取引先キー) → {月キー: [金額, ...]}
    series: dict[tuple[str, str, str], dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for row in rows:
        d = parse_date(row[TX_DATE])
        if d is None:
            continue

        mk = month_key(d)

        for side in SIDES:
            account = row[side.account]
            if not account or account in SKIP_ACCOUNTS:
                continue
            amount = parse_amount(row[side.amount])
            if amount is None or amount == 0:
                continue
            sub = row[side.subaccount]
            vk = _vendor_key(row, side)
            series[(account, sub, vk)][mk].append(amount)

    if not series:
        return CheckResult(0, skipped=True, reason="データがありません")

    warnings = 0
    found_any = False

    for (account, sub, vendor_key), monthly in sorted(series.items()):
        if len(monthly) < MIN_MONTHS:
            continue

        # 月ごとの合計を取る
        monthly_totals = {mk: sum(amounts) for mk, amounts in monthly.items()}
        values = list(monthly_totals.values())
        med = median(values)
        if med == 0:
            continue

        found_any = True

        for mk in sorted(monthly_totals):
            total = monthly_totals[mk]
            ratio = abs(total - med) / med
            if ratio > DEVIATION_RATIO:
                sub_label = f"（{sub}）" if sub else ""
                direction = "過大" if total > med else "過小"
                print_warning(
                    f"「{account}{sub_label}」{vendor_key}: "
                    f"{mk} = {total:,}円（{direction}, "
                    f"中央値 {med:,.0f}円の{total / med:.1f}倍）"
                )
                warnings += 1

    if not found_any:
        print_ok("定期課金パターンなし")
    elif warnings == 0:
        print_ok("定期課金の金額異常値なし")

    return CheckResult(warnings)


def main() -> None:
    run_check_cli(check_recurring_amount, "定期課金の金額異常値チェック")


if __name__ == "__main__":
    main()
