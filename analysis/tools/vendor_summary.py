#!/usr/bin/env python3
"""仕訳帳の取引先別金額サマリーを出力する。"""

import argparse
import sys
from collections import defaultdict

from analysis.common import (
    DataFileError,
    add_journal_args,
    load_journal,
    load_target_rows,
    parse_amount,
    resolve_journals,
)
from analysis.journal_columns import SIDES


def summarize_vendors(
    all_rows: list[dict[str, str]],
) -> list[tuple[str, int, int]]:
    """取引先ごとの件数・合計を返す。

    取引先が空の行はスキップする。
    借方・貸方の両方の取引先を集計対象とする。
    """
    vendor_count: dict[str, int] = defaultdict(int)
    vendor_total: dict[str, int] = defaultdict(int)

    for row in all_rows:
        for side in SIDES:
            vendor = row[side.vendor].strip()
            if not vendor:
                continue
            amount = parse_amount(row[side.amount])
            if amount is None or amount <= 0:
                continue
            vendor_count[vendor] += 1
            vendor_total[vendor] += amount

    return [
        (vendor, vendor_count[vendor], vendor_total[vendor])
        for vendor in sorted(vendor_count)
    ]


def print_summary(all_rows: list[dict[str, str]]) -> None:
    """TSV 形式で取引先別サマリーを標準出力する。"""
    print("[取引先別サマリー]")
    print("取引先\t件数\t合計")
    for vendor, count, total in summarize_vendors(all_rows):
        print(f"{vendor}\t{count}\t{total}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の取引先別金額サマリー")
    add_journal_args(parser)
    args = parser.parse_args()

    try:
        resolved = resolve_journals(args, parser)
        if resolved.target_year is not None:
            all_rows = load_target_rows(resolved.target_year, years=args.years)
        else:
            all_rows = []
            for path in resolved.paths:
                all_rows.extend(load_journal(path))
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print_summary(all_rows)


if __name__ == "__main__":
    main()
