"""tax_summary.py のテスト。"""

import csv
import sys
from pathlib import Path

import pytest

from analysis.common import load_target_rows
from analysis.journal_columns import JOURNAL_COLUMNS, TX_NO
from analysis.tools.tax_summary import MULTI_YEAR, main, print_summary, summarize_tax
from tests.conftest import make_simple_row


def _write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_summarize_tax_basic():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1200",
                        debit_tax="課対仕入10%", credit_tax="対象外"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "3600",
                        debit_tax="課対仕入10%", credit_tax="対象外"),
        make_simple_row("3", "2025/01/25", "消耗品費", "普通預金", "800",
                        debit_tax="課対仕入10%", credit_tax="対象外"),
    ]

    result = summarize_tax(rows)

    # 借方: 課対仕入10% x3, 貸方: 対象外 x3
    assert ("課対仕入10%", "借方", 3, 5600) in result
    assert ("対象外", "貸方", 3, 5600) in result


def test_summarize_tax_skips_empty_tax():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000",
                        debit_tax="課対仕入10%"),
    ]

    result = summarize_tax(rows)

    assert len(result) == 1
    assert result[0][0] == "課対仕入10%"


def test_summarize_tax_separates_sides():
    """同じ税区分でも借方・貸方で別に集計される。"""
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000",
                        debit_tax="対象外", credit_tax="対象外"),
    ]

    result = summarize_tax(rows)

    assert len(result) == 2
    debit = [r for r in result if r[1] == "借方"][0]
    credit = [r for r in result if r[1] == "貸方"][0]
    assert debit == ("対象外", "借方", 1, 1000)
    assert credit == ("対象外", "貸方", 1, 1000)


def test_summarize_tax_empty():
    assert summarize_tax([]) == []


def test_print_summary_outputs_tsv(capsys):
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000",
                        debit_tax="課対仕入10%", credit_tax="対象外"),
        make_simple_row("2", "2025/01/20", "売上高", "普通預金", "5000",
                        debit_tax="対象外", credit_tax="課税売上10%"),
    ]

    print_summary(rows)
    out = capsys.readouterr().out.strip().splitlines()

    assert out[0] == "[税区分別サマリー]"
    assert out[1] == "税区分\t借方/貸方\t件数\t合計"
    # ソート順で結果を確認
    taxes = [line.split("\t")[0] for line in out[2:]]
    assert "課対仕入10%" in taxes
    assert "対象外" in taxes


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
