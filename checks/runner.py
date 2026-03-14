#!/usr/bin/env python3
"""チェックスクリプトの自動検出・一括実行ランナー。

使い方:
    python -m checks.runner <仕訳帳.csv> [<仕訳帳.csv> ...]

オプション:
    --only NAME[,NAME]   指定したチェックのみ実行（例: --only check_tax,check_dates）
    --skip NAME[,NAME]   指定したチェックをスキップ
    --list               利用可能なチェック一覧を表示して終了

チェックの自動検出:
  checks/ 以下の check_*.py モジュールを自動検出する。
  モジュールレベルで ENABLED = False を設定すると自動検出から除外される。
"""

import argparse
import importlib
import pkgutil
import sys
from typing import Callable

import checks
from checks.common import CheckResult, DataFileError, load_journal, print_header


def discover_checks() -> list[tuple[str, Callable, bool]]:
    """checks/ 以下の check_*.py を検出し、(名前, チェック関数, multi_year) のリストを返す。

    モジュールに ENABLED = False が設定されている場合はスキップする。
    """
    found: list[tuple[str, Callable, bool]] = []

    for info in pkgutil.iter_modules(checks.__path__, checks.__name__ + "."):
        module_name = info.name
        short_name = module_name.split(".")[-1]  # e.g. "check_tax"

        if not short_name.startswith("check_"):
            continue

        mod = importlib.import_module(module_name)

        if not getattr(mod, "ENABLED", True):
            continue

        # チェック関数を探す: check_* という名前の callable
        check_fn = None
        for attr_name in dir(mod):
            if attr_name.startswith("check_"):
                candidate = getattr(mod, attr_name)
                if callable(candidate):
                    check_fn = candidate
                    break

        if check_fn is None:
            continue

        multi_year = getattr(mod, "MULTI_YEAR", False)
        found.append((short_name, check_fn, multi_year))

    return sorted(found, key=lambda x: x[0])


def run_all(
    journal_paths: list[str],
    *,
    only: set[str] | None = None,
    skip: set[str] | None = None,
) -> dict[str, CheckResult]:
    """全チェックを一括実行し、{チェック名: CheckResult} を返す。"""
    skip = skip or set()

    available = discover_checks()
    if only is not None:
        available = [(n, fn, m) for n, fn, m in available if n in only]

    # データ読み込み
    all_rows: list[dict] = []
    for path in journal_paths:
        all_rows.extend(load_journal(path))

    results: dict[str, CheckResult] = {}

    for name, check_fn, multi_year in available:
        if name in skip:
            results[name] = CheckResult(0, skipped=True, reason="--skip で除外")
            continue

        if multi_year and len(journal_paths) < 2:
            # 複数年度チェックだがデータが1年度分しかない場合はそのまま実行
            # （チェック関数自体がスキップを判断する）
            pass

        results[name] = check_fn(all_rows)

    return results


def print_summary(results: dict[str, CheckResult]) -> None:
    """全チェックの結果サマリーを出力する。"""
    print_header("チェック結果サマリー")

    total_warnings = 0
    skipped_count = 0

    for name, result in results.items():
        if result.skipped:
            reason = f" ({result.reason})" if result.reason else ""
            print(f"  SKIP: {name}{reason}")
            skipped_count += 1
        elif result.warnings > 0:
            print(f"  WARN: {name} — 警告 {result.warnings}件")
            total_warnings += result.warnings
        else:
            print(f"    OK: {name}")

    print()
    executed = len(results) - skipped_count
    print(f"実行: {executed}件  スキップ: {skipped_count}件  警告合計: {total_warnings}件")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="チェックスクリプト一括実行ランナー",
    )
    parser.add_argument("journals", nargs="*", help="仕訳帳CSVファイルのパス（複数可）")
    parser.add_argument("--only", help="実行するチェック名（カンマ区切り）")
    parser.add_argument("--skip", help="スキップするチェック名（カンマ区切り）")
    parser.add_argument("--list", action="store_true", help="利用可能なチェック一覧を表示")
    args = parser.parse_args()

    if args.list:
        available = discover_checks()
        for name, _fn, multi_year in available:
            label = "複数年度" if multi_year else "単年度"
            print(f"  {name} ({label})")
        sys.exit(0)

    if not args.journals:
        parser.error("仕訳帳CSVファイルを指定してください")

    only = set(args.only.split(",")) if args.only else None
    skip = set(args.skip.split(",")) if args.skip else None

    try:
        results = run_all(args.journals, only=only, skip=skip)
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print_summary(results)

    total_warnings = sum(r.warnings for r in results.values())
    if total_warnings > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
