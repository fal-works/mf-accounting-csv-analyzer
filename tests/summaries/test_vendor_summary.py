"""vendor_summary.py のテスト。"""

import csv
import sys
from pathlib import Path

import pytest

from analysis.common import load_target_rows
from analysis.journal_columns import JOURNAL_COLUMNS, TX_NO
from analysis.summaries.vendor_summary import MULTI_YEAR, main, print_summary, summarize_vendors
from tests.conftest import make_simple_row


def _write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_summarize_vendors_basic():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1200", debit_vendor="NTT"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "3600", debit_vendor="NTT"),
        make_simple_row("3", "2025/01/25", "消耗品費", "普通預金", "800", debit_vendor="Amazon"),
    ]

    result = summarize_vendors(rows)

    assert result == [
        ("Amazon", 1, 800),
        ("NTT", 2, 4800),
    ]


def test_summarize_vendors_counts_both_sides():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000",
                        debit_vendor="NTT", credit_vendor="みずほ銀行"),
    ]

    result = summarize_vendors(rows)

    assert result == [
        ("NTT", 1, 1000),
        ("みずほ銀行", 1, 1000),
    ]


def test_summarize_vendors_uses_summary_for_empty_vendor():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000", summary="インターネット利用料"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "2000", debit_vendor="NTT"),
    ]

    result = summarize_vendors(rows)

    assert len(result) == 2
    assert result[0][0] == "NTT"
    assert result[1] == ("摘要: インターネット利用料", 1, 1000)


def test_summarize_vendors_truncates_long_summary():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "500",
                        summary="これは二十文字を超える長い摘要テキストです。カットされるはず。"),
    ]

    result = summarize_vendors(rows)

    assert len(result) == 1
    label = result[0][0]
    assert label.startswith("摘要: ")
    assert label.endswith("…")


def test_summarize_vendors_skips_row_without_vendor_and_summary():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "500"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "1000", debit_vendor="NTT"),
    ]

    result = summarize_vendors(rows)

    assert result == [("NTT", 1, 1000)]


def test_summarize_vendors_summary_label_sorted_last():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "500", summary="回線料金"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "1000", debit_vendor="Amazon"),
        make_simple_row("3", "2025/01/25", "通信費", "普通預金", "2000", debit_vendor="NTT"),
    ]

    result = summarize_vendors(rows)

    assert [v for v, *_ in result] == ["Amazon", "NTT", "摘要: 回線料金"]


def test_summarize_vendors_includes_credit_vendor():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000", credit_vendor="みずほ銀行"),
    ]

    result = summarize_vendors(rows)

    assert len(result) == 1
    assert result[0] == ("みずほ銀行", 1, 1000)


def test_summarize_vendors_empty():
    assert summarize_vendors([]) == []


def test_print_summary_outputs_tsv(capsys):
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000", debit_vendor="NTT"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "2000", debit_vendor="NTT"),
        make_simple_row("3", "2025/01/25", "新聞図書費", "普通預金", "1500", debit_vendor="Amazon"),
    ]

    print_summary(rows)
    out = capsys.readouterr().out.strip().splitlines()

    assert out[0] == "[取引先別サマリー]"
    assert out[1] == "取引先\t件数\t合計"
    assert out[2] == "Amazon\t1\t1500"
    assert out[3] == "NTT\t2\t3000"


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
