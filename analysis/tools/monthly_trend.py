#!/usr/bin/env python3
"""仕訳帳の勘定科目別・月別金額推移を出力する。"""

import argparse
import sys
from collections import defaultdict

from analysis.common import (
    DataFileError,
    SKIP_ACCOUNTS_COMMON,
    load_journal,
    month_key,
    parse_amount,
    parse_date,
    select_journals,
)
from analysis.journal_columns import SIDES, TX_DATE


def summarize_monthly(
    all_rows: list[dict[str, str]],
) -> tuple[list[str], dict[str, dict[str, int]]]:
    """勘定科目ごとの月別合計を返す。

    Returns:
        (sorted_months, {科目: {月キー: 合計}})
    """
    account_monthly: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    months: set[str] = set()

    for row in all_rows:
        d = parse_date(row[TX_DATE])
        if d is None:
            continue
        mk = month_key(d)
        months.add(mk)

        for side in SIDES:
            account = row[side.account]
            if not account or account in SKIP_ACCOUNTS_COMMON:
                continue
            amount = parse_amount(row[side.amount])
            if amount is None or amount <= 0:
                continue
            account_monthly[account][mk] += amount

    sorted_months = sorted(months)
    result: dict[str, dict[str, int]] = {}
    for account in sorted(account_monthly):
        result[account] = dict(account_monthly[account])

    return sorted_months, result


def print_monthly(all_rows: list[dict[str, str]]) -> None:
    """TSV 形式で月別推移を標準出力する。"""
    sorted_months, account_monthly = summarize_monthly(all_rows)
    if not sorted_months:
        return

    print("[月次推移]")
    print("科目\t" + "\t".join(sorted_months))
    for account in sorted(account_monthly):
        monthly = account_monthly[account]
        values = [str(monthly.get(m, 0)) for m in sorted_months]
        print(f"{account}\t" + "\t".join(values))
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
    parser = argparse.ArgumentParser(description="仕訳帳の勘定科目別・月別金額推移")
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

    print_monthly(all_rows)


if __name__ == "__main__":
    main()
