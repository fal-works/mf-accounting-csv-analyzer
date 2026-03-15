"""revenue_by_client.py のテスト。"""

import sys

import pytest

from analysis.common import load_target_rows
from analysis.journal_columns import TX_NO
from analysis.summaries.revenue_by_client import (
    MULTI_YEAR,
    NO_CLIENT_LABEL,
    main,
    print_summary,
    summarize_revenue_by_client,
)
from tests.conftest import make_simple_row, write_csv


def test_summarize_revenue_by_client_basic():
    rows = [
        make_simple_row("1", "2025/01/10", "売掛金", "売上高", "1200", credit_vendor="デンキヤギ株式会社"),
        make_simple_row("2", "2025/01/20", "売掛金", "売上高", "3600", credit_vendor="デンキヤギ株式会社"),
        make_simple_row("3", "2025/01/25", "売掛金", "売上高", "800", credit_vendor="ピクシブ株式会社"),
    ]

    result = summarize_revenue_by_client(rows)

    assert result == [
        ("デンキヤギ株式会社", 2, 4800),
        ("ピクシブ株式会社", 1, 800),
    ]


def test_summarize_revenue_by_client_uses_fixed_label_for_empty_client():
    rows = [
        make_simple_row("1", "2025/01/10", "売掛金", "売上高", "1000"),
        make_simple_row("2", "2025/01/20", "売掛金", "売上高", "2000", credit_vendor="デンキヤギ株式会社"),
    ]

    result = summarize_revenue_by_client(rows)

    assert result == [
        ("デンキヤギ株式会社", 1, 2000),
        (NO_CLIENT_LABEL, 1, 1000),
    ]


def test_summarize_revenue_by_client_uses_both_credit_and_debit_revenue():
    rows = [
        make_simple_row("1", "2025/01/10", "売上高", "普通預金", "1000", debit_vendor="借方側の取引先"),
        make_simple_row("2", "2025/01/20", "売掛金", "雑収入", "2000", credit_vendor="対象外の取引先"),
        make_simple_row("3", "2025/01/25", "売掛金", "売上高", "3000", credit_vendor="対象の取引先"),
    ]

    result = summarize_revenue_by_client(rows)

    assert result == [
        ("借方側の取引先", 1, -1000),
        ("対象の取引先", 1, 3000),
    ]


def test_summarize_revenue_by_client_subtracts_reversal_from_same_client():
    rows = [
        make_simple_row("1", "2025/01/10", "売掛金", "売上高", "5000", credit_vendor="デンキヤギ株式会社"),
        make_simple_row("2", "2025/01/20", "売上高", "売掛金", "1200", debit_vendor="デンキヤギ株式会社"),
    ]

    result = summarize_revenue_by_client(rows)

    assert result == [("デンキヤギ株式会社", 2, 3800)]


def test_summarize_revenue_by_client_keeps_negative_amount_rows():
    rows = [
        make_simple_row("1", "2025/01/10", "売掛金", "売上高", "-500", credit_vendor="デンキヤギ株式会社"),
        make_simple_row("2", "2025/01/20", "売上高", "売掛金", "-200", debit_vendor="ピクシブ株式会社"),
    ]

    result = summarize_revenue_by_client(rows)

    assert result == [
        ("デンキヤギ株式会社", 1, -500),
        ("ピクシブ株式会社", 1, 200),
    ]


def test_summarize_revenue_by_client_empty():
    assert summarize_revenue_by_client([]) == []


def test_print_summary_outputs_tsv(capsys):
    rows = [
        make_simple_row("1", "2025/01/10", "売掛金", "売上高", "1000", credit_vendor="デンキヤギ株式会社"),
        make_simple_row("2", "2025/01/20", "売上高", "売掛金", "500", debit_vendor="デンキヤギ株式会社"),
        make_simple_row("3", "2025/01/25", "売掛金", "売上高", "1500", credit_vendor="ピクシブ株式会社"),
        make_simple_row("4", "2025/01/30", "売掛金", "売上高", "2000"),
    ]

    print_summary(rows)
    out = capsys.readouterr().out.strip().splitlines()

    assert out[0] == "[売上先別サマリー]"
    assert out[1] == "取引先\t件数\t合計"
    assert out[2] == "デンキヤギ株式会社\t2\t500"
    assert out[3] == "ピクシブ株式会社\t1\t1500"
    assert out[4] == f"{NO_CLIENT_LABEL}\t1\t2000"


def test_load_target_rows_includes_only_target_year(tmp_path):
    journal_2024 = tmp_path / "2024" / "仕訳帳.csv"
    journal_2025 = tmp_path / "2025" / "仕訳帳.csv"
    journal_2024.parent.mkdir()
    journal_2025.parent.mkdir()
    write_csv([make_simple_row("2024", "2024/12/31", "売掛金", "売上高", "1000")], journal_2024)
    write_csv(
        [
            make_simple_row("cross", "2024/12/31", "売掛金", "売上高", "500"),
            make_simple_row("2025", "2025/01/10", "売掛金", "売上高", "2000"),
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
