#!/usr/bin/env python3
"""チェックスクリプトの自動検出・一括実行ランナー。

使い方:
    uv run python -m analysis.checks.runner --target 2025

オプション:
    --target YEAR        分析対象年度
    --years N            比較期間の年数（デフォルト: 3）
    --only NAME[,NAME]   指定したチェックのみ実行（例: --only check_tax,check_dates）
    --skip NAME[,NAME]   指定したチェックをスキップ
    --list               利用可能なチェック一覧を表示して終了

チェックの自動検出:
  analysis/checks/ 以下の check_*.py モジュールを自動検出する。
  モジュールレベルで ENABLED = False を設定すると自動検出から除外される。
"""

import argparse
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Callable

import analysis.checks as checks
from analysis.common import (
    CheckResult,
    DataFileError,
    load_journal,
    parse_date,
    print_header,
    select_journals,
)
from analysis.journal_columns import TX_DATE


def discover_checks() -> list[tuple[str, Callable, bool]]:
    """analysis.checks 以下の check_*.py を検出し、(名前, チェック関数, multi_year) のリストを返す。

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
    target_year: int,
    *,
    years: int = 3,
    data_dir: str = "data",
    selected_journals: dict[int, Path] | None = None,
    only: set[str] | None = None,
    skip: set[str] | None = None,
) -> dict[str, CheckResult]:
    """全チェックを一括実行し、{チェック名: CheckResult} を返す。"""
    skip = skip or set()

    available = discover_checks()
    if only is not None:
        available = [(n, fn, m) for n, fn, m in available if n in only]

    selected_journals = selected_journals or select_journals(
        target_year, years=years, data_dir=data_dir
    )

    all_rows: list[dict] = []
    for path in selected_journals.values():
        all_rows.extend(load_journal(path))

    target_rows = [
        row for row in all_rows
        if (d := parse_date(row[TX_DATE])) is not None and d.year == target_year
    ]

    results: dict[str, CheckResult] = {}

    for name, check_fn, multi_year in available:
        if name in skip:
            results[name] = CheckResult(0, skipped=True, reason="--skip で除外")
            continue

        rows = all_rows if multi_year else target_rows
        results[name] = check_fn(rows)

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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
期間選択:
  --target を指定すると、data/ 以下から必要なデータを自動選定し、
  チェックの種類（単年度/複数年度）に応じて適切な範囲のデータを渡す。
  複数年度比較の期間は --years で変更できるが、デフォルト（3年）で
  通常は十分。全年度横断は事業規模の変動期を含みやすく偽陽性が増える。

チェック名の確認:
  --list で表示される名前を --only / --skip に指定する。""",
    )
    parser.add_argument("--target", type=int, help="分析対象年度")
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="複数年度比較の期間（対象年度を含む年数、デフォルト: 3）",
    )
    parser.add_argument("--only", help="実行するチェック名（カンマ区切り）")
    parser.add_argument("--skip", help="スキップするチェック名（カンマ区切り）")
    parser.add_argument(
        "--list",
        action="store_true",
        help="利用可能なチェック一覧を表示して終了",
    )
    args = parser.parse_args()

    if args.list:
        available = discover_checks()
        for name, _fn, multi_year in available:
            label = "複数年度" if multi_year else "単年度"
            print(f"  {name} ({label})")
        sys.exit(0)

    if args.target is None:
        parser.error("--target を指定してください")

    only = set(args.only.split(",")) if args.only else None
    skip = set(args.skip.split(",")) if args.skip else None

    try:
        selected_journals = select_journals(args.target, years=args.years)
        selected_years = sorted(selected_journals)
        print(f"対象年度: {args.target}  期間: {selected_years[0]}-{selected_years[-1]} ({len(selected_years)}年分)")
        print()
        results = run_all(
            args.target,
            years=args.years,
            selected_journals=selected_journals,
            only=only,
            skip=skip,
        )
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print_summary(results)


if __name__ == "__main__":
    main()
