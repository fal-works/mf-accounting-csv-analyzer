"""filter_journal.py のテスト。"""

import csv
import sys
from datetime import date
from pathlib import Path

import pytest

from analysis.journal_columns import CREDIT_AMOUNT, DEBIT_AMOUNT, JOURNAL_COLUMNS
from analysis.filters.filter_journal import (
    FilterCondition,
    MULTI_YEAR,
    filter_rows,
    main,
    match_row,
    print_rows,
)
from tests.conftest import make_simple_row


def _write_csv(rows: list[dict[str, str]], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


@pytest.fixture
def sample_rows() -> list[dict[str, str]]:
    return [
        make_simple_row(
            "1",
            "2025/06/05",
            "旅費交通費",
            "未払金",
            "12000",
            summary="タクシー代",
            debit_sub="国内",
            debit_vendor="東京タクシー",
            debit_tax="課対仕入10%",
        ),
        make_simple_row(
            "2",
            "2025/06/20",
            "通信費",
            "普通預金",
            "5000",
            summary="Amazon Web Services",
            debit_sub="クラウド",
            debit_vendor="Amazon",
            debit_tax="課対仕入10%",
        ),
        make_simple_row(
            "3",
            "2025/07/01",
            "普通預金",
            "売上高",
            "30000",
            summary="Amazon売上入金",
            credit_sub="EC",
            credit_vendor="Amazon",
            credit_tax="課税売上10%",
        ),
    ]


def test_match_row_without_conditions_matches_all(sample_rows):
    assert all(match_row(row, FilterCondition()) for row in sample_rows)


def test_filter_rows_matches_account(sample_rows):
    matched = filter_rows(sample_rows, FilterCondition(account="旅費"))
    assert [row["取引No"] for row in matched] == ["1"]


def test_filter_rows_matches_subaccount(sample_rows):
    matched = filter_rows(sample_rows, FilterCondition(subaccount="クラウド"))
    assert [row["取引No"] for row in matched] == ["2"]


def test_filter_rows_matches_vendor_on_either_side(sample_rows):
    matched = filter_rows(sample_rows, FilterCondition(vendor="Amazon"))
    assert [row["取引No"] for row in matched] == ["2", "3"]


def test_filter_rows_matches_keyword(sample_rows):
    matched = filter_rows(sample_rows, FilterCondition(keyword="タクシー"))
    assert [row["取引No"] for row in matched] == ["1"]


def test_filter_rows_matches_tax(sample_rows):
    matched = filter_rows(sample_rows, FilterCondition(tax="課税売上"))
    assert [row["取引No"] for row in matched] == ["3"]


def test_filter_rows_matches_date_range(sample_rows):
    matched = filter_rows(
        sample_rows,
        FilterCondition(date_from=date(2025, 6, 10), date_to=date(2025, 6, 30)),
    )
    assert [row["取引No"] for row in matched] == ["2"]


def test_filter_rows_matches_amount_range_using_larger_side(sample_rows):
    matched = filter_rows(sample_rows, FilterCondition(amount_min=10000, amount_max=20000))
    assert [row["取引No"] for row in matched] == ["1"]


def test_filter_rows_respects_side_for_account_vendor_and_tax(sample_rows):
    matched = filter_rows(sample_rows, FilterCondition(account="売上", vendor="Amazon", tax="課税売上", side="credit"))
    assert [row["取引No"] for row in matched] == ["3"]


def test_filter_rows_respects_side_for_amount(sample_rows):
    rows = [
        make_simple_row("4", "2025/08/01", "仮払金", "未払金", "1000", summary="base"),
    ]
    rows[0][DEBIT_AMOUNT] = "8000"
    rows[0][CREDIT_AMOUNT] = "1000"

    assert filter_rows(rows, FilterCondition(amount_min=5000)) == [rows[0]]
    assert filter_rows(rows, FilterCondition(amount_min=5000, side="credit")) == []


def test_filter_rows_combines_conditions_with_and(sample_rows):
    matched = filter_rows(
        sample_rows,
        FilterCondition(account="通信費", vendor="Amazon", keyword="Web", amount_min=4000),
    )
    assert [row["取引No"] for row in matched] == ["2"]


def test_print_rows_outputs_tsv(sample_rows, capsys):
    print_rows(sample_rows[:1])
    out = capsys.readouterr().out.strip().splitlines()

    assert out[0] == "取引No\t取引日\t借方勘定科目\t借方補助科目\t借方金額(円)\t貸方勘定科目\t貸方補助科目\t貸方金額(円)\t摘要"
    assert out[1] == "1\t2025/06/05\t旅費交通費\t国内\t12000\t未払金\t\t12000\tタクシー代"
    assert out[2] == "（1件）"


def test_main_rejects_no_filter_condition(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--target", "2025"])

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 2


def test_main_rejects_side_only(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--target", "2025", "--side", "debit"])

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 2


def test_main_filters_target_year_csv(tmp_path, monkeypatch, capsys):
    journal = tmp_path / "data" / "2025" / "仕訳帳.csv"
    journal.parent.mkdir(parents=True)
    _write_csv(
        [
            make_simple_row("1", "2025/06/05", "旅費交通費", "未払金", "12000", summary="タクシー代"),
            make_simple_row("2", "2025/06/20", "通信費", "普通預金", "5000", summary="サーバー代"),
        ],
        journal,
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["prog", "--target", "2025", "--account", "旅費"])

    main()

    out = capsys.readouterr().out.strip().splitlines()
    assert out[0] == "取引No\t取引日\t借方勘定科目\t借方補助科目\t借方金額(円)\t貸方勘定科目\t貸方補助科目\t貸方金額(円)\t摘要"
    assert out[1].startswith("1\t2025/06/05\t旅費交通費")
    assert out[2] == "（1件）"


def test_main_accepts_single_journal_path_argument(tmp_path, monkeypatch, capsys):
    journal = tmp_path / "sample.csv"
    _write_csv(
        [
            make_simple_row("1", "2025/06/05", "旅費交通費", "未払金", "12000", summary="タクシー代"),
            make_simple_row("2", "2025/06/20", "通信費", "普通預金", "5000", summary="サーバー代"),
        ],
        journal,
    )
    monkeypatch.setattr(sys, "argv", ["prog", str(journal), "--account", "通信費"])

    main()

    out = capsys.readouterr().out.strip().splitlines()
    assert out[0] == "取引No\t取引日\t借方勘定科目\t借方補助科目\t借方金額(円)\t貸方勘定科目\t貸方補助科目\t貸方金額(円)\t摘要"
    assert out[1].startswith("2\t2025/06/20\t通信費")
    assert out[2] == "（1件）"


def test_multi_year_is_false():
    assert MULTI_YEAR is False
