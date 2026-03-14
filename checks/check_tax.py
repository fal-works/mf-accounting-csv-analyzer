#!/usr/bin/env python3
"""仕訳帳の税区分チェック。

使い方:
    uv run python check_tax.py <仕訳帳.csv>

チェック内容:
  1. 税区分が既知の有効な値であるか
  2. 売上科目に売上系の税区分、仕入科目に仕入系の税区分が設定されているか
  3. 非課税であるべき科目（事業主貸・事業主借・元入金等）に課税区分が設定されていないか
  4. 借方と貸方で税区分の組み合わせが矛盾していないか
"""

import argparse
import sys

from checks.common import CheckResult, DataFileError, load_journal, print_error, print_header, print_ok, print_warning
from checks.journal_columns import SIDES, TX_DATE, TX_NO

MULTI_YEAR = False

# 有効な税区分
VALID_TAX_CATEGORIES = {
    "",
    "対象外",
    "課税売上 10% 五種",
    "課税仕入 10%",
    "対象外仕入",
}

# 売上系の税区分
SALES_TAX = {"課税売上 10% 五種"}

# 仕入系の税区分
PURCHASE_TAX = {"課税仕入 10%", "対象外仕入"}

# 常に対象外であるべき勘定科目
NON_TAXABLE_ACCOUNTS = {
    "事業主貸", "事業主借", "元入金", "現金", "普通預金", "売掛金", "未払金", "機械装置",
}

# 売上科目
SALES_ACCOUNTS = {"売上高"}

# 仕入・経費科目
EXPENSE_ACCOUNTS = {
    "支払手数料", "水道光熱費", "通信費", "広告宣伝費", "消耗品費",
    "新聞図書費",
}


def check_tax_categories(rows: list[dict]) -> CheckResult:
    """税区分の妥当性をチェックする。"""
    warnings = 0

    # --- チェック1: 有効な税区分かどうか ---
    print_header("税区分の有効値チェック")
    invalid_count = 0
    for row in rows:
        for side in SIDES:
            val = row[side.tax]
            if val not in VALID_TAX_CATEGORIES:
                print_error(
                    f"取引No {row[TX_NO]} ({row[TX_DATE]}): "
                    f"{side.label}に未知の税区分「{val}」"
                )
                invalid_count += 1

    if invalid_count == 0:
        print_ok("税区分すべて有効")
    warnings += invalid_count

    # --- チェック2: 科目と税区分の対応チェック ---
    print_header("科目と税区分の整合性チェック")
    mismatch_count = 0

    for row in rows:
        tx_info = f"取引No {row[TX_NO]} ({row[TX_DATE]})"

        for side in SIDES:
            account = row[side.account]
            tax = row[side.tax]
            if not account or not tax:
                continue

            if account in NON_TAXABLE_ACCOUNTS and tax not in {"対象外", ""}:
                print_error(f"{tx_info}: {side.label}「{account}」に税区分「{tax}」は不適切")
                mismatch_count += 1

            if account in SALES_ACCOUNTS and tax in PURCHASE_TAX:
                print_error(f"{tx_info}: {side.label}「{account}」に仕入系税区分「{tax}」")
                mismatch_count += 1

            if account in EXPENSE_ACCOUNTS and tax in SALES_TAX:
                print_error(f"{tx_info}: {side.label}「{account}」に売上系税区分「{tax}」")
                mismatch_count += 1

    if mismatch_count == 0:
        print_ok("科目×税区分の整合OK")
    warnings += mismatch_count

    return CheckResult(warnings)


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の税区分チェック")
    parser.add_argument("journal", help="仕訳帳CSVファイルのパス")
    args = parser.parse_args()

    try:
        journal = load_journal(args.journal)
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    result = check_tax_categories(journal)

    if result.warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
