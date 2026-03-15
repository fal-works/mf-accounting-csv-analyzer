#!/usr/bin/env python3
"""仕訳帳の取引先別金額サマリーを出力する。"""

from collections import defaultdict

from analysis.common import (
    parse_amount,
    run_summary_cli,
)
from analysis.journal_columns import DEBIT_SIDE, SIDES

MULTI_YEAR = False

NO_VENDOR_LABEL = "（取引先未入力）"


def summarize_vendors(
    all_rows: list[dict[str, str]],
) -> list[tuple[str, int, int]]:
    """取引先ごとの件数・合計を返す。

    借方・貸方の両方の取引先を集計対象とする。
    取引先が空の行は「（取引先未入力）」として集計する。
    """
    vendor_count: dict[str, int] = defaultdict(int)
    vendor_total: dict[str, int] = defaultdict(int)

    for row in all_rows:
        found = False
        for side in SIDES:
            vendor = row[side.vendor].strip()
            if not vendor:
                continue
            amount = parse_amount(row[side.amount])
            if amount is None or amount <= 0:
                continue
            vendor_count[vendor] += 1
            vendor_total[vendor] += amount
            found = True
        if not found:
            # どちらのサイドにも取引先がない行は固定ラベルで集計する。
            # 借方・貸方は同額のため、借方金額のみ使用する。
            amount = parse_amount(row[DEBIT_SIDE.amount]) or 0
            if amount <= 0:
                continue
            vendor_count[NO_VENDOR_LABEL] += 1
            vendor_total[NO_VENDOR_LABEL] += amount

    vendors = sorted(vendor_count, key=lambda v: (v == NO_VENDOR_LABEL, v))
    return [
        (vendor, vendor_count[vendor], vendor_total[vendor])
        for vendor in vendors
    ]


def print_summary(all_rows: list[dict[str, str]]) -> None:
    """TSV 形式で取引先別サマリーを標準出力する。"""
    print("[取引先別サマリー]")
    print("取引先\t件数\t合計")
    for vendor, count, total in summarize_vendors(all_rows):
        print(f"{vendor}\t{count}\t{total}")
    print()


def main() -> None:
    run_summary_cli(print_summary, "仕訳帳の取引先別金額サマリー")


if __name__ == "__main__":
    main()
