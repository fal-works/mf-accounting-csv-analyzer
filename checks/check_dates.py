#!/usr/bin/env python3
"""仕訳帳の売上計上漏れチェック。

使い方:
    python check_dates.py <仕訳帳.csv>

チェック内容:
  1. 売上高の計上がない月がないか（入力忘れの検出）
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_journal, month_key, parse_date, print_header, print_ok, print_warning


def check_monthly_sales(rows: list[dict]) -> None:
    """月次の売上計上チェック。売上高がない月を警告する。"""
    print_header("月次売上計上チェック")

    months_with_sales: set[str] = set()
    all_months: set[str] = set()

    for row in rows:
        d = parse_date(row["取引日"])
        if d is None:
            continue
        mk = month_key(d)
        all_months.add(mk)

        if row["貸方勘定科目"] == "売上高":
            months_with_sales.add(mk)

    if all_months:
        year = int(min(all_months).split("/")[0])
        expected_months = {f"{year}/{m:02d}" for m in range(1, 13)}
    else:
        expected_months = set()

    missing = sorted(expected_months - months_with_sales)
    if missing:
        print_warning(f"売上高の計上なし: {', '.join(missing)}")
    else:
        print_ok("毎月売上計上あり")


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の売上計上漏れチェック")
    parser.add_argument("journal", help="仕訳帳CSVファイルのパス")
    args = parser.parse_args()

    journal = load_journal(args.journal)
    check_monthly_sales(journal)


if __name__ == "__main__":
    main()
