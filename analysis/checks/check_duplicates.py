#!/usr/bin/env python3
"""仕訳帳の重複仕訳チェック。

使い方:
    uv run python check_duplicates.py <仕訳帳.csv>

チェック内容:
  1. 同一日・同一科目・同一金額・同一摘要の仕訳が複数存在しないか（二重入力の検出）
"""

from collections import defaultdict

from analysis.common import CheckResult, print_header, print_ok, print_warning, run_check_cli
from analysis.journal_columns import (
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
    MEMO,
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

    counts: dict[tuple, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = entry_key(row)
        counts[key].append(row)

    warnings = 0
    for key, grouped_rows in counts.items():
        if len(grouped_rows) > 1:
            unique_nos = sorted({row[TX_NO] for row in grouped_rows}, key=int)
            # 同一取引No内の複合仕訳は正常なので除外
            if len(unique_nos) > 1:
                date_str = key[0]
                debit_account = key[1]
                summary = key[11]
                print_warning(
                    f"類似仕訳: 取引No {', '.join(unique_nos)} "
                    f"({date_str} {debit_account} {summary})"
                )
                memos = []
                for row in grouped_rows:
                    memo = row[MEMO].strip()
                    if memo and memo not in memos:
                        memos.append(memo)
                if memos:
                    memo_suffix = " (他に異なるメモあり)" if len(memos) > 1 else ""
                    print(f"  メモ: {memos[0]}{memo_suffix}")
                warnings += 1

    if warnings == 0:
        print_ok("重複なし")

    return CheckResult(warnings)


def main() -> None:
    run_check_cli(check_duplicate_entries, "仕訳帳の重複仕訳チェック")


if __name__ == "__main__":
    main()
