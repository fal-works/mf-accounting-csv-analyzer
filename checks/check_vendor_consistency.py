#!/usr/bin/env python3
"""取引先ごとの勘定科目・税区分の一貫性チェック。

使い方:
    python check_vendor_consistency.py <仕訳帳.csv> [<仕訳帳.csv> ...]

チェック内容:
  同じ借方取引先に対して複数の借方勘定科目や税区分が使われているケースを検出する。
  摘要の表記ゆれで `check_consistency.py` では拾えない科目選択ミスの候補を補足する。

出力:
  取引先ごとに使われた科目・税区分の組み合わせを集計し、少数派パターンを警告する。
"""

import argparse
import sys
from collections import defaultdict

from checks.common import SKIP_ACCOUNTS_COMMON, CheckResult, DataFileError, load_journal, print_header, print_ok, print_warning

MULTI_YEAR = True


def check_vendor_consistency(all_rows: list[dict]) -> CheckResult:
    """借方取引先ごとの科目・税区分の一貫性をチェックする。"""
    print_header("取引先×勘定科目 一貫性チェック")

    vendor_patterns: dict[str, dict[tuple[str, str], list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for row in all_rows:
        vendor = row["借方取引先"].strip()
        account = row["借方勘定科目"].strip()
        tax = row["借方税区分"].strip()
        if not vendor or not account:
            continue
        if account in SKIP_ACCOUNTS_COMMON:
            continue

        tx_info = (
            f"No.{row['取引No']}({row['取引日']}) "
            f"{account} {row['借方金額(円)']}円 {row['摘要'].strip()}"
        )
        vendor_patterns[vendor][(account, tax)].append(tx_info)

    warnings = 0

    for vendor, patterns in sorted(vendor_patterns.items()):
        if len(patterns) <= 1:
            continue

        sorted_patterns = sorted(patterns.items(), key=lambda x: -len(x[1]))
        main_pattern, main_txs = sorted_patterns[0]
        total = sum(len(txs) for txs in patterns.values())

        for pattern, txs in sorted_patterns[1:]:
            ratio = len(txs) / total
            if ratio <= 0.5:
                account, tax = pattern
                main_account, main_tax = main_pattern
                examples = txs[:3]
                suffix = f" 他{len(txs)-3}件" if len(txs) > 3 else ""
                print_warning(
                    f"取引先「{vendor}」: "
                    f"主={main_account}/{main_tax}({len(main_txs)}件) "
                    f"他={account}/{tax}({len(txs)}件) "
                    f"{', '.join(examples)}{suffix}"
                )
                warnings += 1

    if warnings == 0:
        print_ok("取引先×科目の揺れなし")

    return CheckResult(warnings)


def main() -> None:
    parser = argparse.ArgumentParser(description="取引先ごとの勘定科目・税区分の一貫性チェック")
    parser.add_argument("journals", nargs="+", help="仕訳帳CSVファイルのパス（複数可）")
    args = parser.parse_args()

    try:
        all_rows: list[dict] = []
        for path in args.journals:
            all_rows.extend(load_journal(path))
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    result = check_vendor_consistency(all_rows)

    if result.warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
