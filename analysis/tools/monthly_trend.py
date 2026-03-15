#!/usr/bin/env python3
"""仕訳帳の勘定科目別・月別金額推移を出力する。"""

import argparse
import sys
from collections import defaultdict

from analysis.common import (
    DataFileError,
    SKIP_ACCOUNTS_COMMON,
    add_journal_args,
    load_journal,
    load_target_rows,
    month_key,
    parse_amount,
    parse_date,
    resolve_journals,
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


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の勘定科目別・月別金額推移")
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

    print_monthly(all_rows)


if __name__ == "__main__":
    main()
