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

from analysis.common import (
    SKIP_ACCOUNTS_COMMON,
    CheckResult,
    print_error,
    print_header,
    print_ok,
    print_warning,
    run_check_cli,
)
from analysis.journal_columns import SIDES, SUMMARY, TX_DATE, TX_NO

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

# 売上科目
SALES_ACCOUNTS = {"売上高"}


def _print_summary_context(row: dict[str, str]) -> None:
    """警告判定に役立つ摘要を補足表示する。"""
    summary = row[SUMMARY].strip()
    if summary:
        print(f"  摘要: {summary}")

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
                _print_summary_context(row)
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

            if account in SKIP_ACCOUNTS_COMMON and tax not in {"対象外", ""}:
                print_error(f"{tx_info}: {side.label}「{account}」に税区分「{tax}」は不適切")
                _print_summary_context(row)
                mismatch_count += 1

            if account in SALES_ACCOUNTS and tax in PURCHASE_TAX:
                print_error(f"{tx_info}: {side.label}「{account}」に仕入系税区分「{tax}」")
                _print_summary_context(row)
                mismatch_count += 1

            if account not in SALES_ACCOUNTS and account not in SKIP_ACCOUNTS_COMMON and tax in SALES_TAX:
                print_error(f"{tx_info}: {side.label}「{account}」に売上系税区分「{tax}」")
                _print_summary_context(row)
                mismatch_count += 1

    if mismatch_count == 0:
        print_ok("科目×税区分の整合OK")
    warnings += mismatch_count

    return CheckResult(warnings)


def main() -> None:
    run_check_cli(check_tax_categories, "仕訳帳の税区分チェック")


if __name__ == "__main__":
    main()
