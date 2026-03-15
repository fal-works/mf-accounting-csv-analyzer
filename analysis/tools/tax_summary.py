#!/usr/bin/env python3
"""仕訳帳の税区分別金額サマリーを出力する。"""

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


def summarize_tax(
    all_rows: list[dict[str, str]],
) -> list[tuple[str, str, int, int]]:
    """税区分ごとの件数・合計を、借方・貸方それぞれで返す。

    Returns:
        [(税区分, 借方/貸方, 件数, 合計), ...]
    """
    # (税区分, 借方/貸方ラベル) -> 金額リスト
    tax_amounts: dict[tuple[str, str], list[int]] = defaultdict(list)

    for row in all_rows:
        for side in SIDES:
            tax = row[side.tax].strip()
            if not tax:
                continue
            amount = parse_amount(row[side.amount])
            if amount is None or amount <= 0:
                continue
            tax_amounts[(tax, side.label)].append(amount)

    summaries: list[tuple[str, str, int, int]] = []
    for (tax, side_label) in sorted(tax_amounts):
        amounts = tax_amounts[(tax, side_label)]
        total = sum(amounts)
        count = len(amounts)
        summaries.append((tax, side_label, count, total))

    return summaries


def print_summary(all_rows: list[dict[str, str]]) -> None:
    """TSV 形式で税区分別サマリーを標準出力する。"""
    print("[税区分別サマリー]")
    print("税区分\t借方/貸方\t件数\t合計")
    for tax, side_label, count, total in summarize_tax(all_rows):
        print(f"{tax}\t{side_label}\t{count}\t{total}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の税区分別金額サマリー")
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
