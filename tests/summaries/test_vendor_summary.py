"""vendor_summary.py のテスト。"""

import sys

import pytest

from analysis.common import load_target_rows
from analysis.journal_columns import TX_NO
from analysis.summaries.vendor_summary import MULTI_YEAR, NO_VENDOR_LABEL, main, print_summary, summarize_vendors
from tests.conftest import make_simple_row, write_csv


def test_summarize_vendors_basic():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1200", debit_vendor="NTT"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "3600", debit_vendor="NTT"),
        make_simple_row("3", "2025/01/25", "消耗品費", "普通預金", "800", debit_vendor="Amazon"),
    ]

    result = summarize_vendors(rows)

    assert result == [
        ("Amazon", 1, ["消耗品費"]),
        ("NTT", 2, ["通信費"]),
    ]


def test_summarize_vendors_counts_both_sides():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000",
                        debit_vendor="NTT", credit_vendor="みずほ銀行"),
    ]

    result = summarize_vendors(rows)

    assert result == [
        ("NTT", 1, ["通信費"]),
        ("みずほ銀行", 1, ["普通預金"]),
    ]


def test_summarize_vendors_uses_fixed_label_for_empty_vendor():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "2000", debit_vendor="NTT"),
    ]

    result = summarize_vendors(rows)

    assert len(result) == 2
    assert result[0][0] == "NTT"
    assert result[1] == (NO_VENDOR_LABEL, 1, ["通信費"])


def test_summarize_vendors_fixed_label_sorted_last():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "500"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "1000", debit_vendor="Amazon"),
        make_simple_row("3", "2025/01/25", "通信費", "普通預金", "2000", debit_vendor="NTT"),
    ]

    result = summarize_vendors(rows)

    assert [v for v, *_ in result] == ["Amazon", "NTT", NO_VENDOR_LABEL]


def test_summarize_vendors_includes_credit_vendor():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000", credit_vendor="みずほ銀行"),
    ]

    result = summarize_vendors(rows)

    assert len(result) == 1
    assert result[0] == ("みずほ銀行", 1, ["普通預金"])


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
    assert out[1] == "取引先\t件数\t勘定科目"
    assert out[2] == "Amazon\t1\t新聞図書費"
    assert out[3] == "NTT\t2\t通信費"


def test_print_summary_omits_accounts_for_no_vendor_label(capsys):
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000"),
    ]

    print_summary(rows)
    out = capsys.readouterr().out.strip().splitlines()

    assert out[2] == f"{NO_VENDOR_LABEL}\t1\t（省略）"


def test_print_summary_outputs_multiple_accounts_for_same_vendor(capsys):
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000", debit_vendor="NTT"),
        make_simple_row("2", "2025/01/20", "消耗品費", "未払金", "2000", debit_vendor="NTT"),
    ]

    print_summary(rows)
    out = capsys.readouterr().out.strip().splitlines()

    assert out[2] == "NTT\t2\t消耗品費, 通信費"


def test_load_target_rows_includes_only_target_year(tmp_path):
    journal_2024 = tmp_path / "2024" / "仕訳帳.csv"
    journal_2025 = tmp_path / "2025" / "仕訳帳.csv"
    journal_2024.parent.mkdir()
    journal_2025.parent.mkdir()
    write_csv([make_simple_row("2024", "2024/12/31", "通信費", "普通預金", "1000")], journal_2024)
    write_csv(
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
