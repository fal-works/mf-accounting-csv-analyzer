#!/usr/bin/env python3
"""仕訳帳の取引先別サマリーを出力する。"""

from collections import defaultdict

from analysis.common import (
    format_pretty,
    format_tsv,
    parse_amount,
    run_summary_cli,
)
from analysis.journal_columns import DEBIT_SIDE, SIDES

MULTI_YEAR = False

NO_VENDOR_LABEL = "（取引先未入力）"


def summarize_vendors(
    all_rows: list[dict[str, str]],
) -> list[tuple[str, int, list[str]]]:
    """取引先ごとの件数・関連勘定科目一覧を返す。

    借方・貸方の両方の取引先を集計対象とする。
    取引先が空の行は「（取引先未入力）」として集計する。
    """
    vendor_count: dict[str, int] = defaultdict(int)
    vendor_accounts: dict[str, set[str]] = defaultdict(set)

    for row in all_rows:
        found = False
        for side in SIDES:
            vendor = row[side.vendor].strip()
            if not vendor:
                continue
            amount = parse_amount(row[side.amount])
            if amount is None or amount <= 0:
                continue
            vendor_count[vendor] += 1
            account = row[side.account].strip()
            if account:
                vendor_accounts[vendor].add(account)
            found = True
        if not found:
            # どちらのサイドにも取引先がない行は固定ラベルで集計する。
            # 借方・貸方は同額のため、借方金額のみ使用する。
            amount = parse_amount(row[DEBIT_SIDE.amount]) or 0
            if amount <= 0:
                continue
            vendor_count[NO_VENDOR_LABEL] += 1
            account = row[DEBIT_SIDE.account].strip()
            if account:
                vendor_accounts[NO_VENDOR_LABEL].add(account)

    vendors = sorted(vendor_count, key=lambda v: (v == NO_VENDOR_LABEL, v))
    return [
        (vendor, vendor_count[vendor], sorted(vendor_accounts[vendor]))
        for vendor in vendors
    ]


def print_summary(all_rows: list[dict[str, str]], *, pretty: bool = False) -> None:
    """取引先別サマリーを標準出力する。"""
    print("[取引先別サマリー]")
    headers = ["取引先", "件数", "勘定科目"]
    rows = []
    for vendor, count, accounts in summarize_vendors(all_rows):
        accounts_display = "（省略）" if vendor == NO_VENDOR_LABEL else ", ".join(accounts)
        rows.append([vendor, str(count), accounts_display])
    formatter = format_pretty if pretty else format_tsv
    print(formatter(headers, rows))
    print()


def main() -> None:
    run_summary_cli(print_summary, "仕訳帳の取引先別サマリー")


if __name__ == "__main__":
    main()
