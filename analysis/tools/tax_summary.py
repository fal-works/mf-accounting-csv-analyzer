#!/usr/bin/env python3
"""仕訳帳の税区分別金額サマリーを出力する。"""

import argparse
import sys
from collections import defaultdict

from analysis.common import (
    DataFileError,
    load_journal,
    parse_amount,
    parse_date,
    select_journals,
)
from analysis.journal_columns import SIDES, TX_DATE


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


def load_target_rows(target_year: int, *, years: int = 3, data_dir: str = "data") -> list[dict[str, str]]:
    """対象年度の仕訳のみを読み込む。"""
    all_rows: list[dict[str, str]] = []
    for path in select_journals(target_year, years=years, data_dir=data_dir).values():
        all_rows.extend(load_journal(path))

    return [
        row for row in all_rows
        if (d := parse_date(row[TX_DATE])) is not None and d.year == target_year
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の税区分別金額サマリー")
    parser.add_argument("journals", nargs="*", help="仕訳帳CSVファイルのパス（複数可）")
    parser.add_argument("--target", type=int, help="分析対象年度")
    parser.add_argument("--years", type=int, default=3, help="比較期間の年数（デフォルト: 3）")
    args = parser.parse_args()

    try:
        if args.target is not None and args.journals:
            parser.error("--target と仕訳帳CSVファイルのパスは同時に指定できません")
        if args.target is None and not args.journals:
            parser.error("--target または仕訳帳CSVファイルのパスを指定してください")

        if args.target is not None:
            all_rows = load_target_rows(args.target, years=args.years)
        else:
            all_rows = []
            for path in args.journals:
                all_rows.extend(load_journal(path))
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print_summary(all_rows)


if __name__ == "__main__":
    main()
