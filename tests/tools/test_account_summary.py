"""account_summary.py のテスト。"""

import csv
import sys
from pathlib import Path

import pytest

from analysis.common import load_target_rows, median
from analysis.journal_columns import JOURNAL_COLUMNS, TX_NO
from analysis.tools.account_summary import MULTI_YEAR, main, print_summary, summarize_accounts
from tests.conftest import make_simple_row


def _write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_summarize_accounts_excludes_skip_accounts():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1200"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "3600"),
        make_simple_row("3", "2025/01/25", "消耗品費", "普通預金", "800"),
        make_simple_row("4", "2025/01/31", "普通預金", "売掛金", "999999"),
    ]

    assert summarize_accounts(rows) == [
        ("消耗品費", 1, 800, 800.0, 800.0, 800, 800),
        ("通信費", 2, 4800, 2400.0, 2400.0, 1200, 3600),
    ]


def test_print_summary_outputs_tsv(capsys):
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "2000"),
        make_simple_row("3", "2025/01/25", "新聞図書費", "普通預金", "1500"),
    ]

    print_summary(rows)
    out = capsys.readouterr().out.strip().splitlines()

    assert out[0] == "[勘定科目別サマリー]"
    assert out[1] == "科目\t件数\t合計\t平均\t中央値\t最小\t最大"
    assert out[2] == "新聞図書費\t1\t1500\t1500\t1500\t1500\t1500"
    assert out[3] == "通信費\t2\t3000\t1500\t1500\t1000\t2000"


def test_median_handles_even_and_odd_counts():
    assert median([1, 9, 5]) == 5.0
    assert median([1, 9, 5, 7]) == 6.0


def test_load_target_rows_includes_only_target_year(tmp_path):
    journal_2024 = tmp_path / "2024" / "仕訳帳.csv"
    journal_2025 = tmp_path / "2025" / "仕訳帳.csv"
    journal_2024.parent.mkdir()
    journal_2025.parent.mkdir()
    _write_csv([make_simple_row("2024", "2024/12/31", "通信費", "普通預金", "1000")], journal_2024)
    _write_csv(
        [
            make_simple_row("cross", "2024/12/31", "消耗品費", "普通預金", "500"),
            make_simple_row("2025", "2025/01/10", "通信費", "普通預金", "2000"),
        ],
        journal_2025,
    )

    rows = load_target_rows(2025, years=2, data_dir=str(tmp_path))

    assert [row[TX_NO] for row in rows] == ["2025"]


def test_main_rejects_target_and_paths_together(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--target", "2025", "dummy.csv"])

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 2


def test_multi_year_is_false():
    assert MULTI_YEAR is False
