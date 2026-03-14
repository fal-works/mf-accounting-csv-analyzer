#!/usr/bin/env python3
"""勘定科目と摘要の一貫性チェック。

使い方:
    uv run python check_consistency.py <仕訳帳.csv> [<仕訳帳.csv> ...]

チェック内容:
  同じ摘要に対して異なる勘定科目が使われているケースを検出する。
  過去の仕訳パターンと異なる科目選択は、人為的な科目選択ミスの可能性がある。
  複数年度のファイルを渡すことで、年度横断での一貫性を確認できる。

出力:
  摘要ごとに使われた勘定科目の組み合わせと、少数派の取引を警告として表示する。
"""

from collections import defaultdict

from checks.common import CheckResult, print_header, print_ok, print_warning, run_check_cli
from checks.journal_columns import SIDES, SUMMARY, TX_DATE, TX_NO

MULTI_YEAR = True


def check_consistency(all_rows: list[dict]) -> CheckResult:
    """摘要と勘定科目の組み合わせの一貫性をチェックする。"""
    print_header("勘定科目×摘要 一貫性チェック")

    # 摘要 → {勘定科目: [取引情報]} を借方・貸方それぞれで集計
    # 空の摘要は対象外（パターン判定できない）
    maps = {
        side.label: defaultdict(lambda: defaultdict(list))
        for side in SIDES
    }

    for row in all_rows:
        summary = row[SUMMARY].strip()
        if not summary:
            continue

        tx_info = f"No.{row[TX_NO]} ({row[TX_DATE]})"

        for side in SIDES:
            account = row[side.account]
            if account:
                maps[side.label][summary][account].append(tx_info)

    warnings = 0

    for side_label, mapping in maps.items():
        for summary, accounts in sorted(mapping.items()):
            if len(accounts) <= 1:
                continue

            # 最も多い科目を「主パターン」とし、それ以外を警告
            sorted_accounts = sorted(accounts.items(), key=lambda x: -len(x[1]))
            main_account, main_txs = sorted_accounts[0]
            total = sum(len(txs) for txs in accounts.values())

            for account, txs in sorted_accounts[1:]:
                # 少数派のみ警告（1件 vs 多数など）
                ratio = len(txs) / total
                if ratio < 0.5:
                    examples = txs[:3]
                    suffix = f" 他{len(txs)-3}件" if len(txs) > 3 else ""
                    print_warning(
                        f"{side_label} 摘要「{summary}」: "
                        f"主={main_account}({len(main_txs)}件) "
                        f"他={account}({len(txs)}件) "
                        f"{', '.join(examples)}{suffix}"
                    )
                    warnings += 1

    if warnings == 0:
        print_ok("科目の揺れなし")

    return CheckResult(warnings)


def main() -> None:
    run_check_cli(check_consistency, "勘定科目と摘要の一貫性チェック", multi_file=True)


if __name__ == "__main__":
    main()
