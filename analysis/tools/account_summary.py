#!/usr/bin/env python3
"""仕訳帳の勘定科目別金額サマリーを出力する。"""

import argparse
import sys
from collections import defaultdict

from analysis.common import (
    DataFileError,
    SKIP_ACCOUNTS_COMMON,
    load_journal,
    median,
    parse_amount,
    parse_date,
    select_journals,
)
from analysis.journal_columns import SIDES, TX_DATE


def summarize_accounts(all_rows: list[dict[str, str]]) -> list[tuple[str, int, int, float, float, int, int]]:
    """勘定科目ごとの件数・合計・平均・中央値・最小・最大を返す。"""
    account_amounts: dict[str, list[int]] = defaultdict(list)

    for row in all_rows:
        for side in SIDES:
            account = row[side.account]
            if not account or account in SKIP_ACCOUNTS_COMMON:
                continue
            amount = parse_amount(row[side.amount])
            if amount is None or amount <= 0:
                continue
            account_amounts[account].append(amount)

    summaries: list[tuple[str, int, int, float, float, int, int]] = []
    for account in sorted(account_amounts):
        amounts = account_amounts[account]
        total = sum(amounts)
        count = len(amounts)
        summaries.append((
            account,
            count,
            total,
            total / count,
            median(amounts),
            min(amounts),
            max(amounts),
        ))

    return summaries


def print_summary(all_rows: list[dict[str, str]]) -> None:
    """TSV 形式で勘定科目別サマリーを標準出力する。"""
    print("科目\t件数\t合計\t平均\t中央値\t最小\t最大")
    for account, count, total, avg, med, lo, hi in summarize_accounts(all_rows):
        print(f"{account}\t{count}\t{total}\t{avg:.0f}\t{med:.0f}\t{lo}\t{hi}")


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
    parser = argparse.ArgumentParser(description="仕訳帳の勘定科目別金額サマリー")
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
