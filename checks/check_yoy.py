#!/usr/bin/env python3
"""勘定科目の年度間比較チェック。

使い方:
    python check_yoy.py <仕訳帳.csv> <仕訳帳.csv> ...

チェック内容:
  勘定科目別の年間合計を年度間で比較し、大幅な増減を検出する。
  計上漏れや二重計上の発見に有効。
  最低2年度分のデータが必要。

出力:
  年度間で大幅に変動した科目の一覧と、年度別の集計表。
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import SKIP_ACCOUNTS_COMMON, load_journal, parse_amount, parse_date, print_header, print_ok, print_warning

# 前年比でこの倍率以上の変動を警告
CHANGE_THRESHOLD = 2.0

# 変動額がこの金額以下なら無視（小額の変動はノイズ）
MIN_CHANGE_AMOUNT = 10000


def check_yoy(all_rows: list[dict]) -> None:
    """年度間の勘定科目別合計を比較する。"""

    # 年度 × 科目 → 合計金額を集計
    # 借方に出現すれば借方合計、貸方に出現すれば貸方合計として集計
    yearly: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in all_rows:
        d = parse_date(row["取引日"])
        if d is None:
            continue

        for acct_col, amt_col in [
            ("借方勘定科目", "借方金額(円)"),
            ("貸方勘定科目", "貸方金額(円)"),
        ]:
            account = row[acct_col]
            if not account:
                continue
            amount = parse_amount(row[amt_col])
            if amount is None:
                continue
            yearly[d.year][account] += amount

    years = sorted(yearly.keys())
    if len(years) < 2:
        print_header("年度間比較チェック")
        print_warning("比較には最低2年度分のデータが必要です")
        return

    # --- 変動チェック ---
    print_header("年度間 大幅変動チェック")

    all_accounts = sorted(set().union(*(yearly[y].keys() for y in years)))

    # 資産・負債・資本の期首残高科目は変動が自然なので除外
    skip_accounts = SKIP_ACCOUNTS_COMMON

    warnings = 0
    for account in all_accounts:
        if account in skip_accounts:
            continue

        for i in range(1, len(years)):
            prev_year = years[i - 1]
            curr_year = years[i]
            prev_amt = yearly[prev_year].get(account, 0)
            curr_amt = yearly[curr_year].get(account, 0)

            if prev_amt == 0 and curr_amt == 0:
                continue

            diff = curr_amt - prev_amt

            if abs(diff) < MIN_CHANGE_AMOUNT:
                continue

            if prev_amt == 0:
                print_warning(
                    f"「{account}」が{curr_year}年に新規出現: "
                    f"{curr_amt:,}円 ({prev_year}年は0円)"
                )
                warnings += 1
            elif curr_amt == 0:
                print_warning(
                    f"「{account}」が{curr_year}年に消滅: "
                    f"0円 ({prev_year}年は{prev_amt:,}円)"
                )
                warnings += 1
            else:
                ratio = curr_amt / prev_amt
                if ratio >= CHANGE_THRESHOLD or ratio <= 1 / CHANGE_THRESHOLD:
                    direction = "増加" if diff > 0 else "減少"
                    print_warning(
                        f"「{account}」が{prev_year}→{curr_year}で大幅{direction}: "
                        f"{prev_amt:,}円 → {curr_amt:,}円 ({ratio:.1f}倍)"
                    )
                    warnings += 1

    if warnings == 0:
        print_ok("年度間で大幅な変動はありません")
    else:
        print_warning(f"{warnings}件の大幅変動があります（事業変化による場合もあります）")

    # --- 年度別集計表 ---
    print_header("年度別 勘定科目合計")
    header = f"  {'科目':<14s}" + "".join(f" {y:>12d}" for y in years)
    print(header)
    print(f"  {'-'*14}" + "".join(f" {'-'*12}" for _ in years))
    for account in all_accounts:
        vals = "".join(f" {yearly[y].get(account, 0):>12,d}" for y in years)
        print(f"  {account:<14s}{vals}")


def main() -> None:
    parser = argparse.ArgumentParser(description="勘定科目の年度間比較チェック")
    parser.add_argument("journals", nargs="+", help="仕訳帳CSVファイルのパス（複数可・年度順推奨）")
    args = parser.parse_args()

    all_rows: list[dict] = []
    for path in args.journals:
        all_rows.extend(load_journal(path))

    check_yoy(all_rows)
    print()


if __name__ == "__main__":
    main()
