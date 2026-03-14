#!/usr/bin/env python3
"""定期経費の欠落チェック。

使い方:
    uv run python check_recurring.py <仕訳帳.csv>

チェック内容:
  過去の計上パターンから毎月発生すべき経費を推定し、
  欠落している月を警告する。check_dates.py の売上チェックを一般化したもの。

  「毎月発生すべき」の判定基準:
    年間で10ヶ月以上計上されている科目×補助科目の組み合わせを対象とする。

出力:
  定期的に計上されている経費科目と、欠落月の一覧。
"""

import argparse
import sys
from collections import defaultdict

from checks.common import SKIP_ACCOUNTS_COMMON, CheckResult, DataFileError, load_journal, month_key, parse_date, print_header, print_ok, print_warning
from checks.journal_columns import CREDIT_ACCOUNT, CREDIT_SUBACCOUNT, DEBIT_ACCOUNT, DEBIT_SUBACCOUNT, TX_DATE

MULTI_YEAR = False

# 年間でこの月数以上計上されていれば「定期経費」とみなす
MONTHLY_THRESHOLD = 10

# 経費ではない科目（定期性の判定対象外）
SKIP_ACCOUNTS = SKIP_ACCOUNTS_COMMON | {"売上高"}


def check_recurring(rows: list[dict]) -> CheckResult:
    """定期的な経費の欠落をチェックする。"""
    print_header("定期経費 欠落チェック")

    # (科目, 補助科目) → set of month keys
    # 借方・貸方の両方を見る（経費は通常借方だが念のため）
    account_months: dict[tuple[str, str], set[str]] = defaultdict(set)
    all_months: set[str] = set()

    for row in rows:
        d = parse_date(row[TX_DATE])
        if d is None:
            continue
        mk = month_key(d)
        all_months.add(mk)

        for acct_col, sub_col in [
            (DEBIT_ACCOUNT, DEBIT_SUBACCOUNT),
            (CREDIT_ACCOUNT, CREDIT_SUBACCOUNT),
        ]:
            account = row[acct_col]
            if not account:
                continue
            sub = row[sub_col]
            account_months[(account, sub)].add(mk)

    if not all_months:
        return CheckResult(0, skipped=True, reason="データがありません")

    # 年度を特定（データ中の最頻年）
    year = int(min(all_months).split("/")[0])
    expected_months = {f"{year}/{m:02d}" for m in range(1, 13)}

    warnings = 0
    found_any = False

    for (account, sub), months in sorted(account_months.items()):
        if account in SKIP_ACCOUNTS:
            continue
        # 期待月のうち何月分計上されているか
        covered = months & expected_months
        if len(covered) < MONTHLY_THRESHOLD:
            continue

        found_any = True
        missing = sorted(expected_months - months)
        if missing:
            sub_label = f"({sub})" if sub else ""
            print_warning(
                f"「{account}{sub_label}」欠落: {', '.join(missing)} "
                f"({len(covered)}/12月計上)"
            )
            warnings += 1

    if not found_any:
        print_ok("定期経費パターンなし")
    elif warnings == 0:
        print_ok("定期経費の欠落なし")

    return CheckResult(warnings)


def main() -> None:
    parser = argparse.ArgumentParser(description="定期経費の欠落チェック")
    parser.add_argument("journal", help="仕訳帳CSVファイルのパス")
    args = parser.parse_args()

    try:
        journal = load_journal(args.journal)
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    result = check_recurring(journal)

    if result.warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
