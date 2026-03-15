#!/usr/bin/env python3
"""仕訳帳の税区分別金額サマリーを出力する。"""

from collections import defaultdict

from analysis.common import (
    format_pretty,
    format_tsv,
    parse_amount,
    run_summary_cli,
)
from analysis.journal_columns import SIDES

MULTI_YEAR = False


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


def print_summary(all_rows: list[dict[str, str]], *, pretty: bool = False) -> None:
    """税区分別サマリーを標準出力する。"""
    print("[税区分別サマリー]")
    headers = ["税区分", "借方/貸方", "件数", "合計"]
    rows = [
        [tax, side_label, str(count), str(total)]
        for tax, side_label, count, total in summarize_tax(all_rows)
    ]
    formatter = format_pretty if pretty else format_tsv
    print(formatter(headers, rows))
    print()


def main() -> None:
    run_summary_cli(print_summary, "仕訳帳の税区分別金額サマリー")


if __name__ == "__main__":
    main()
