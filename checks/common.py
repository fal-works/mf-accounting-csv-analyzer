"""仕訳帳CSVの共通読み込みユーティリティ。"""

import csv
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple

from checks.journal_columns import JOURNAL_COLUMNS


class CheckResult(NamedTuple):
    """チェック関数の戻り値。"""
    warnings: int
    skipped: bool = False
    reason: str = ""


class DataFileError(Exception):
    """データファイルの読み込みエラー。"""


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


# 資産・負債・資本など、経費分析系チェックでスキップする勘定科目の共通セット
SKIP_ACCOUNTS_COMMON: frozenset[str] = frozenset({
    "事業主貸", "事業主借", "元入金",
    "現金", "普通預金", "売掛金", "未払金",
    "機械装置", "工具器具備品",
})
