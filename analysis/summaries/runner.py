#!/usr/bin/env python3
"""サマリーツールの自動検出・一括実行ランナー。"""

import argparse
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Callable

import analysis.summaries as summaries
from analysis.common import DataFileError, load_journal, parse_date, select_journals
from analysis.journal_columns import TX_DATE


def discover_summaries() -> list[tuple[str, Callable, bool]]:
    """analysis.summaries 以下のサマリーツールを検出する。"""
    found: list[tuple[str, Callable, bool]] = []

    for info in pkgutil.iter_modules(summaries.__path__, summaries.__name__ + "."):
        module_name = info.name
        short_name = module_name.split(".")[-1]

        if short_name in {"__init__", "runner"} or short_name.startswith("tmp_"):
            continue

        mod = importlib.import_module(module_name)
        summary_fn = getattr(mod, "print_summary", None)
        if not callable(summary_fn):
            continue

        multi_year = getattr(mod, "MULTI_YEAR", False)
        found.append((short_name, summary_fn, multi_year))

    return sorted(found, key=lambda x: x[0])


def run_all(
    target_year: int,
    *,
    years: int = 3,
    data_dir: str = "data",
    selected_journals: dict[int, Path] | None = None,
    only: set[str] | None = None,
    skip: set[str] | None = None,
    pretty: bool = False,
) -> list[str]:
    """全サマリーツールを実行し、実行したツール名のリストを返す。"""
    skip = skip or set()

    available = discover_summaries()
    if only is not None:
        available = [(n, fn, m) for n, fn, m in available if n in only]

    selected_journals = selected_journals or select_journals(
        target_year,
        years=years,
        data_dir=data_dir,
    )

    all_rows: list[dict[str, str]] = []
    for path in selected_journals.values():
        all_rows.extend(load_journal(path))

    target_rows = [
        row for row in all_rows
        if (d := parse_date(row[TX_DATE])) is not None and d.year == target_year
    ]

    executed: list[str] = []
    for name, summary_fn, multi_year in available:
        if name in skip:
            continue

        rows = all_rows if multi_year else target_rows
        summary_fn(rows, pretty=pretty)
        executed.append(name)

    return executed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="サマリーツール一括実行ランナー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
期間選択:
  --target を指定すると、data/ 以下から必要なデータを自動選定する。
  現状のサマリーツールは単年度だが、将来の複数年度ツールに備えて
  --years も指定できる。

ツール名の確認:
  --list で表示される名前を --only / --skip に指定する。""",
    )
    parser.add_argument("--target", type=int, help="分析対象年度")
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="複数年度比較の期間（対象年度を含む年数、デフォルト: 3）",
    )
    parser.add_argument("--only", help="実行するツール名（カンマ区切り）")
    parser.add_argument("--skip", help="スキップするツール名（カンマ区切り）")
    parser.add_argument("--pretty", action="store_true", help="人間向け整形出力")
    parser.add_argument(
        "--list",
        action="store_true",
        help="利用可能なサマリーツール一覧を表示して終了",
    )
    args = parser.parse_args()

    if args.list:
        for name, _fn, multi_year in discover_summaries():
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
        print(
            f"対象年度: {args.target}  期間: "
            f"{selected_years[0]}-{selected_years[-1]} ({len(selected_years)}年分)"
        )
        print()
        run_all(
            args.target,
            years=args.years,
            selected_journals=selected_journals,
            only=only,
            skip=skip,
            pretty=args.pretty,
        )
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
