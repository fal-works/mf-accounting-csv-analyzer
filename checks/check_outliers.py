#!/usr/bin/env python3
"""仕訳帳の異常値（外れ値）チェック。

使い方:
    uv run python check_outliers.py <仕訳帳.csv> [<仕訳帳.csv> ...]

チェック内容:
  勘定科目ごとに金額の分布を分析し、通常と大きく異なる金額の取引を検出する。
  桁間違い（例: 33,000円 → 330,000円）などの入力ミスの発見に有効。

出力:
  科目ごとの統計情報（件数・平均・中央値・最大・最小）と外れ値の一覧。
  外れ値の判定は中央値からの乖離倍率による。
"""

import argparse
import sys
from collections import defaultdict

from checks.common import SKIP_ACCOUNTS_COMMON, CheckResult, DataFileError, load_journal, parse_amount, print_header, print_ok, print_warning
from checks.journal_columns import CREDIT_ACCOUNT, CREDIT_AMOUNT, DEBIT_ACCOUNT, DEBIT_AMOUNT, TX_DATE, TX_NO

MULTI_YEAR = True

# 外れ値とみなす中央値からの乖離倍率（中央値の N 倍以上）
OUTLIER_THRESHOLD = 5.0

# 統計を取る最低件数（少なすぎると判定できない）
MIN_SAMPLES = 3

# 金額のばらつきが本質的に大きく、外れ値検出に適さない科目
# （事業主勘定・資産負債の残高科目など）
SKIP_ACCOUNTS = SKIP_ACCOUNTS_COMMON


def median(values: list[int]) -> float:
    """中央値を計算する。"""
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2


def check_outliers(all_rows: list[dict]) -> CheckResult:
    """勘定科目ごとの金額の外れ値を検出する。"""
    print_header("金額の異常値チェック")

    # 勘定科目ごとに金額を収集
    # 借方・貸方を統合（科目が同じなら同じ性質の取引）
    account_amounts: dict[str, list[tuple[int, str]]] = defaultdict(list)

    for row in all_rows:
        tx_info = f"No.{row[TX_NO]} ({row[TX_DATE]})"

        for side, acct_col, amt_col in [
            ("借方", DEBIT_ACCOUNT, DEBIT_AMOUNT),
            ("貸方", CREDIT_ACCOUNT, CREDIT_AMOUNT),
        ]:
            account = row[acct_col]
            if not account:
                continue
            amount = parse_amount(row[amt_col])
            if amount is None or amount == 0:
                continue
            account_amounts[account].append((amount, f"{tx_info} {side}"))

    warnings = 0

    for account in sorted(account_amounts.keys()):
        entries = account_amounts[account]
        if account in SKIP_ACCOUNTS:
            continue
        if len(entries) < MIN_SAMPLES:
            continue

        amounts = [a for a, _ in entries]
        med = median(amounts)

        if med == 0:
            continue

        for amount, tx_info in entries:
            ratio = amount / med
            if ratio >= OUTLIER_THRESHOLD or (ratio > 0 and ratio <= 1 / OUTLIER_THRESHOLD):
                print_warning(
                    f"「{account}」{amount:,}円 (中央値{med:,.0f}円の{ratio:.1f}倍) {tx_info}"
                )
                warnings += 1

    if warnings == 0:
        print_ok("異常値なし")

    return CheckResult(warnings)


def print_summary(all_rows: list[dict]) -> None:
    """勘定科目ごとの金額サマリーをCSV形式で標準出力に出力する。"""
    print_header("勘定科目別 金額サマリー")

    account_amounts: dict[str, list[int]] = defaultdict(list)
    for row in all_rows:
        for acct_col, amt_col in [
            (DEBIT_ACCOUNT, DEBIT_AMOUNT),
            (CREDIT_ACCOUNT, CREDIT_AMOUNT),
        ]:
            account = row[acct_col]
            if not account:
                continue
            amount = parse_amount(row[amt_col])
            if amount is None or amount <= 0:
                continue
            account_amounts[account].append(amount)

    print("科目\t件数\t合計\t平均\t中央値\t最小\t最大")
    for account in sorted(account_amounts.keys()):
        amounts = account_amounts[account]
        n = len(amounts)
        total = sum(amounts)
        avg = total / n
        med = median(amounts)
        lo = min(amounts)
        hi = max(amounts)
        print(f"{account}\t{n}\t{total}\t{avg:.0f}\t{med:.0f}\t{lo}\t{hi}")


def main() -> None:
    parser = argparse.ArgumentParser(description="仕訳帳の異常値チェック")
    parser.add_argument("journals", nargs="+", help="仕訳帳CSVファイルのパス（複数可）")
    parser.add_argument("--summary", action="store_true", help="科目別サマリーも表示")
    args = parser.parse_args()

    try:
        all_rows: list[dict] = []
        for path in args.journals:
            all_rows.extend(load_journal(path))
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    result = check_outliers(all_rows)

    if args.summary:
        print_summary(all_rows)

    if result.warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
