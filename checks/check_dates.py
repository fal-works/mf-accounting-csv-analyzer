#!/usr/bin/env python3
"""仕訳帳の売上計上漏れチェック。

使い方:
    uv run python check_dates.py <仕訳帳.csv>

チェック内容:
  1. 売上高の計上がない月がないか（入力忘れの検出）
"""

import argparse
import sys

from checks.common import CheckResult, DataFileError, load_journal, month_key, parse_date, print_header, print_ok, print_warning
from checks.journal_columns import CREDIT_ACCOUNT, TX_DATE

MULTI_YEAR = False


def check_monthly_sales(rows: list[dict]) -> CheckResult:
    """月次の売上計上チェック。売上高がない月を警告する。"""
    print_header("月次売上計上チェック")

    months_with_sales: set[str] = set()
    all_months: set[str] = set()

    for row in rows:
        d = parse_date(row[TX_DATE])
        if d is None:
            continue
        mk = month_key(d)
        all_months.add(mk)

        if row[CREDIT_ACCOUNT] == "売上高":
            months_with_sales.add(mk)

    if all_months:
        year = int(min(all_months).split("/")[0])
        expected_months = {f"{year}/{m:02d}" for m in range(1, 13)}
    else:
        expected_months = set()

    missing = sorted(expected_months - months_with_sales)
    if missing:
        print_warning(f"売上高の計上なし: {', '.join(missing)}")
        return CheckResult(1)
    else:
        print_ok("毎月売上計上あり")
        return CheckResult(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の売上計上漏れチェック")
    parser.add_argument("journal", help="仕訳帳CSVファイルのパス")
    args = parser.parse_args()

    try:
        journal = load_journal(args.journal)
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    check_monthly_sales(journal)


if __name__ == "__main__":
    main()
