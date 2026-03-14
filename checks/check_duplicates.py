#!/usr/bin/env python3
"""仕訳帳の重複仕訳チェック。

使い方:
    uv run python check_duplicates.py <仕訳帳.csv>

チェック内容:
  1. 同一日・同一科目・同一金額・同一摘要の仕訳が複数存在しないか（二重入力の検出）
"""

import argparse
import sys
from collections import defaultdict

from checks.common import CheckResult, DataFileError, load_journal, print_header, print_ok, print_warning
from checks.journal_columns import (
    CREDIT_ACCOUNT,
    CREDIT_AMOUNT,
    CREDIT_SUBACCOUNT,
    CREDIT_TAX,
    CREDIT_VENDOR,
    DEBIT_ACCOUNT,
    DEBIT_AMOUNT,
    DEBIT_SUBACCOUNT,
    DEBIT_TAX,
    DEBIT_VENDOR,
    SUMMARY,
    TX_DATE,
    TX_NO,
)

MULTI_YEAR = False


def check_duplicate_entries(rows: list[dict]) -> CheckResult:
    """同一内容の仕訳が重複していないかチェックする。"""
    print_header("重複仕訳チェック")

    entry_key = lambda row: (
        row[TX_DATE],
        row[DEBIT_ACCOUNT],
        row[DEBIT_SUBACCOUNT],
        row[DEBIT_VENDOR],
        row[DEBIT_TAX],
        row[DEBIT_AMOUNT],
        row[CREDIT_ACCOUNT],
        row[CREDIT_SUBACCOUNT],
        row[CREDIT_VENDOR],
        row[CREDIT_TAX],
        row[CREDIT_AMOUNT],
        row[SUMMARY],
    )

    counts: dict[tuple, list[str]] = defaultdict(list)
    for row in rows:
        key = entry_key(row)
        counts[key].append(row[TX_NO])

    warnings = 0
    for key, tx_nos in counts.items():
        if len(tx_nos) > 1:
            unique_nos = sorted(set(tx_nos), key=int)
            # 同一取引No内の複合仕訳は正常なので除外
            if len(unique_nos) > 1:
                date_str = key[0]
                debit_account = key[1]
                summary = key[11]
                print_warning(
                    f"類似仕訳: 取引No {', '.join(unique_nos)} "
                    f"({date_str} {debit_account} {summary})"
                )
                warnings += 1

    if warnings == 0:
        print_ok("重複なし")

    return CheckResult(warnings)


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の重複仕訳チェック")
    parser.add_argument("journal", help="仕訳帳CSVファイルのパス")
    args = parser.parse_args()

    try:
        journal = load_journal(args.journal)
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    result = check_duplicate_entries(journal)

    if result.warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
