#!/usr/bin/env python3
"""補助科目の有無の揺れをチェックする。"""

from collections import defaultdict

from analysis.common import SKIP_ACCOUNTS_COMMON, CheckResult, print_header, print_ok, print_warning, run_check_cli
from analysis.journal_columns import SIDES, TX_DATE, TX_NO

MULTI_YEAR = False


def check_subaccount(rows: list[dict]) -> CheckResult:
    """同一科目で補助科目あり/なしが混在する少数派パターンを警告する。"""
    print_header("補助科目の付け忘れチェック")

    patterns: dict[str, dict[str, dict[bool, list[str]]]] = {
        side.label: defaultdict(lambda: {True: [], False: []})
        for side in SIDES
    }

    for row in rows:
        tx_info = f"No.{row[TX_NO]} ({row[TX_DATE]})"

        for side in SIDES:
            account = row[side.account].strip()
            if not account or account in SKIP_ACCOUNTS_COMMON:
                continue

            has_subaccount = bool(row[side.subaccount].strip())
            patterns[side.label][account][has_subaccount].append(tx_info)

    warnings = 0

    for side_label, accounts in patterns.items():
        for account, grouped in sorted(accounts.items()):
            has_sub = grouped[True]
            no_sub = grouped[False]

            if not has_sub or not no_sub:
                continue

            if len(no_sub) <= len(has_sub):
                minority = no_sub
                minority_label = "なし"
            else:
                minority = has_sub
                minority_label = "あり"
            examples = ", ".join(minority[:3])
            suffix = f" 他{len(minority) - 3}件" if len(minority) > 3 else ""
            print_warning(
                f"{side_label}「{account}」: "
                f"補助科目あり {len(has_sub)}件 / なし {len(no_sub)}件 "
                f"少数派={minority_label} "
                f"{examples}{suffix}"
            )
            warnings += 1

    if warnings == 0:
        print_ok("補助科目の揺れなし")

    return CheckResult(warnings)


def main() -> None:
    run_check_cli(check_subaccount, "補助科目の付け忘れチェック")


if __name__ == "__main__":
    main()
