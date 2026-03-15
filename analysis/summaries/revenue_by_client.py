#!/usr/bin/env python3
"""仕訳帳の売上高を取引先別に集計したサマリーを出力する。"""

from collections import defaultdict

from analysis.common import parse_amount, run_summary_cli
from analysis.journal_columns import (
    CREDIT_ACCOUNT,
    CREDIT_AMOUNT,
    CREDIT_VENDOR,
    DEBIT_ACCOUNT,
    DEBIT_AMOUNT,
    DEBIT_VENDOR,
)

MULTI_YEAR = False

NO_CLIENT_LABEL = "（取引先未入力）"
REVENUE_ACCOUNT = "売上高"


def summarize_revenue_by_client(
    all_rows: list[dict[str, str]],
) -> list[tuple[str, int, int]]:
    """売上高の取引先ごとの件数・合計を返す。"""
    client_count: dict[str, int] = defaultdict(int)
    client_total: dict[str, int] = defaultdict(int)

    for row in all_rows:
        if row[CREDIT_ACCOUNT].strip() == REVENUE_ACCOUNT:
            amount = parse_amount(row[CREDIT_AMOUNT])
            if amount is not None:
                client = row[CREDIT_VENDOR].strip() or NO_CLIENT_LABEL
                client_count[client] += 1
                client_total[client] += amount

        if row[DEBIT_ACCOUNT].strip() == REVENUE_ACCOUNT:
            amount = parse_amount(row[DEBIT_AMOUNT])
            if amount is not None:
                client = row[DEBIT_VENDOR].strip() or NO_CLIENT_LABEL
                client_count[client] += 1
                client_total[client] -= amount

    clients = sorted(client_count, key=lambda client: (client == NO_CLIENT_LABEL, client))
    return [
        (client, client_count[client], client_total[client])
        for client in clients
    ]


def print_summary(all_rows: list[dict[str, str]]) -> None:
    """TSV 形式で売上先別サマリーを標準出力する。"""
    print("[売上先別サマリー]")
    print("取引先\t件数\t合計")
    for client, count, total in summarize_revenue_by_client(all_rows):
        print(f"{client}\t{count}\t{total}")
    print()


def main() -> None:
    run_summary_cli(print_summary, "仕訳帳の売上高取引先別サマリー")


if __name__ == "__main__":
    main()
