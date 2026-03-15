"""仕訳帳CSVの共通読み込みユーティリティ。"""

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Callable, NamedTuple

from analysis.journal_columns import JOURNAL_COLUMNS, TX_DATE

_JOURNAL_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "schema" / "journal.json").read_text(encoding="utf-8")
)
_JOURNAL_SAVE_NAME = _JOURNAL_SCHEMA["saveName"]


class CheckResult(NamedTuple):
    """チェック関数の戻り値。"""
    warnings: int
    skipped: bool = False
    reason: str = ""


class DataFileError(Exception):
    """データファイルの読み込みエラー。"""


class ResolvedJournals(NamedTuple):
    """CLI から解決した仕訳帳パス群。"""
    target_year: int | None
    target_path: Path | None
    paths: list[Path]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """UTF-8のCSVファイルを読み込み、辞書のリストとして返す。"""
    path = Path(path)
    if not path.exists():
        raise DataFileError(f"ファイルが見つかりません: {path}")
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_journal(path: str | Path) -> list[dict[str, str]]:
    """仕訳帳CSVを読み込む。"""
    rows = read_csv(path)
    if not rows:
        return rows
    missing_columns = [column for column in JOURNAL_COLUMNS if column not in rows[0]]
    if missing_columns:
        raise DataFileError(f"仕訳帳CSVの必須カラムが不足しています: {', '.join(missing_columns)}")
    return rows


def discover_journals(data_dir: str = "data") -> dict[int, Path]:
    """data/{年度}/仕訳帳.csv を自動検出し、{年度: パス} を返す。"""
    journals: dict[int, Path] = {}

    for path in sorted(Path(data_dir).glob(f"*/{_JOURNAL_SAVE_NAME}")):
        try:
            year = int(path.parent.name)
        except ValueError:
            continue
        journals[year] = path

    if not journals:
        raise DataFileError(f"仕訳帳CSVが見つかりません: {data_dir}/*/{_JOURNAL_SAVE_NAME}")

    return journals


def select_journals(target_year: int, *, years: int = 3, data_dir: str = "data") -> dict[int, Path]:
    """対象年度と比較期間から使用する仕訳帳を選定する。"""
    if years < 1:
        raise DataFileError("--years には 1 以上を指定してください")

    discovered = discover_journals(data_dir)
    if target_year not in discovered:
        raise DataFileError(f"対象年度の仕訳帳CSVが見つかりません: {target_year}")

    start_year = target_year - years + 1
    selected = {
        year: path
        for year, path in discovered.items()
        if start_year <= year <= target_year
    }
    return dict(sorted(selected.items()))


def add_journal_args(parser: argparse.ArgumentParser, *, allow_multiple_paths: bool = True) -> None:
    """仕訳帳CLIで共通利用する引数を追加する。"""
    nargs = "*" if allow_multiple_paths else "?"
    help_text = "仕訳帳CSVファイルのパス（複数可）" if allow_multiple_paths else "仕訳帳CSVファイルのパス"
    parser.add_argument("journals", nargs=nargs, help=help_text)
    parser.add_argument("--target", type=int, help="分析対象年度")
    parser.add_argument("--years", type=int, default=3, help="比較期間の年数（デフォルト: 3）")


def resolve_journals(args: argparse.Namespace, parser: argparse.ArgumentParser) -> ResolvedJournals:
    """argparse の結果から仕訳帳パスを解決する。"""
    journals = [Path(path) for path in args.journals]

    if args.target is not None and journals:
        parser.error("--target と仕訳帳CSVファイルのパスは同時に指定できません")
    if args.target is None and not journals:
        parser.error("--target または仕訳帳CSVファイルのパスを指定してください")

    if args.target is not None:
        selected = select_journals(args.target, years=args.years)
        return ResolvedJournals(args.target, selected[args.target], list(selected.values()))

    return ResolvedJournals(None, None, journals)


def load_target_rows(target_year: int, *, years: int = 3, data_dir: str = "data") -> list[dict[str, str]]:
    """比較期間をロードしつつ、対象年度の仕訳だけを返す。"""
    all_rows: list[dict[str, str]] = []
    for path in select_journals(target_year, years=years, data_dir=data_dir).values():
        all_rows.extend(load_journal(path))

    return [
        row for row in all_rows
        if (d := parse_date(row[TX_DATE])) is not None and d.year == target_year
    ]


def run_check_cli(
    check_fn: Callable[[list[dict[str, str]]], CheckResult],
    description: str,
    *,
    multi_file: bool = False,
) -> None:
    """標準的なチェックCLIを実行する。"""
    parser = argparse.ArgumentParser(description=description)
    add_journal_args(parser, allow_multiple_paths=multi_file)
    args = parser.parse_args()

    try:
        resolved = resolve_journals(args, parser)
        if multi_file:
            rows: list[dict[str, str]] = []
            for path in resolved.paths:
                rows.extend(load_journal(path))
        else:
            path = resolved.target_path if resolved.target_path is not None else resolved.paths[0]
            rows = load_journal(path)
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    check_fn(rows)


def print_header(title: str) -> None:
    """チェック結果のヘッダーを出力する。"""
    print(f"\n[{title}]")


def print_ok(message: str) -> None:
    print(f"OK: {message}")


def print_warning(message: str) -> None:
    print(f"WARN: {message}")


def print_error(message: str) -> None:
    print(f"ERR: {message}")


def parse_date(value: str) -> date | None:
    """'YYYY/MM/DD' 形式の日付文字列をパースする。"""
    try:
        return datetime.strptime(value.strip(), "%Y/%m/%d").date()
    except (ValueError, AttributeError):
        return None


def month_key(d: date) -> str:
    """date から 'YYYY/MM' 形式の月キーを返す。"""
    return f"{d.year}/{d.month:02d}"


def parse_amount(value: str) -> int | None:
    """金額文字列を int に変換する。変換できなければ None。"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def median(values: list[int]) -> float:
    """中央値を計算する。空リストは受け付けない。"""
    s = sorted(values)
    n = len(s)
    if n == 0:
        raise ValueError("median() requires at least one value")
    if n % 2 == 1:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2


# 資産・負債・資本など、経費分析系チェックでスキップする勘定科目の共通セット
SKIP_ACCOUNTS_COMMON: frozenset[str] = frozenset({
    "事業主貸", "事業主借", "元入金",
    "現金", "普通預金", "売掛金", "未払金",
    "機械装置", "工具器具備品",
})
