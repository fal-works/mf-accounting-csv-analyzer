#!/usr/bin/env python3
"""勘定科目と摘要の一貫性チェック。

使い方:
    python check_consistency.py <仕訳帳.csv> [<仕訳帳.csv> ...]

チェック内容:
  同じ摘要に対して異なる勘定科目が使われているケースを検出する。
  過去の仕訳パターンと異なる科目選択は、人為的な科目選択ミスの可能性がある。
  複数年度のファイルを渡すことで、年度横断での一貫性を確認できる。

出力:
  摘要ごとに使われた勘定科目の組み合わせと、少数派の取引を警告として表示する。
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_journal, print_header, print_ok, print_warning


def check_consistency(all_rows: list[dict]) -> None:
    """摘要と勘定科目の組み合わせの一貫性をチェックする。"""
    print_header("勘定科目×摘要 一貫性チェック")

    # 摘要 → {勘定科目: [取引情報]} を借方・貸方それぞれで集計
    # 空の摘要は対象外（パターン判定できない）
    debit_map: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    credit_map: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    for row in all_rows:
        summary = row["摘要"].strip()
        if not summary:
            continue

        tx_info = f"No.{row['取引No']} ({row['取引日']})"

        if row["借方勘定科目"]:
            debit_map[summary][row["借方勘定科目"]].append(tx_info)
        if row["貸方勘定科目"]:
            credit_map[summary][row["貸方勘定科目"]].append(tx_info)

    warnings = 0

    for side_label, mapping in [("借方", debit_map), ("貸方", credit_map)]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="勘定科目と摘要の一貫性チェック")
    parser.add_argument("journals", nargs="+", help="仕訳帳CSVファイルのパス（複数可）")
    args = parser.parse_args()

    all_rows: list[dict] = []
    for path in args.journals:
        all_rows.extend(load_journal(path))

    check_consistency(all_rows)


if __name__ == "__main__":
    main()
