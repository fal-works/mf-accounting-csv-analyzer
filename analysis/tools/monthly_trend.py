#!/usr/bin/env python3
"""仕訳帳の勘定科目別・月別金額推移を出力する。"""

from collections import defaultdict

from analysis.common import (
    SKIP_ACCOUNTS_COMMON,
    month_key,
    parse_amount,
    parse_date,
    run_summary_cli,
)
from analysis.journal_columns import SIDES, TX_DATE

MULTI_YEAR = False


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


def print_summary(all_rows: list[dict[str, str]]) -> None:
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
    run_summary_cli(print_summary, "仕訳帳の勘定科目別・月別金額推移")


if __name__ == "__main__":
    main()
