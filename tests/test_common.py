"""common.py のユニットテスト。"""

from datetime import date
from pathlib import Path

import pytest

from analysis.common import (
    SKIP_ACCOUNTS_COMMON,
    CheckResult,
    DataFileError,
    month_key,
    parse_amount,
    parse_date,
    read_csv,
    run_check_cli,
)


class TestParseDate:
    def test_valid(self):
        assert parse_date("2025/01/15") == date(2025, 1, 15)

    def test_padded(self):
        assert parse_date("  2025/01/15  ") == date(2025, 1, 15)

    def test_invalid(self):
        assert parse_date("invalid") is None

    def test_empty(self):
        assert parse_date("") is None


class TestMonthKey:
    def test_basic(self):
        assert month_key(date(2025, 1, 15)) == "2025/01"

    def test_december(self):
        assert month_key(date(2025, 12, 31)) == "2025/12"


class TestParseAmount:
    def test_valid(self):
        assert parse_amount("12345") == 12345

    def test_zero(self):
        assert parse_amount("0") == 0

    def test_invalid(self):
        assert parse_amount("abc") is None

    def test_empty(self):
        assert parse_amount("") is None

    def test_none(self):
        assert parse_amount(None) is None


class TestSkipAccountsCommon:
    def test_is_frozenset(self):
        assert isinstance(SKIP_ACCOUNTS_COMMON, frozenset)

    def test_contains_expected(self):
        for name in ["事業主貸", "事業主借", "元入金", "現金", "普通預金"]:
            assert name in SKIP_ACCOUNTS_COMMON


class TestCheckResult:
    def test_defaults(self):
        r = CheckResult(3)
        assert r.warnings == 3
        assert r.skipped is False
        assert r.reason == ""

    def test_skipped(self):
        r = CheckResult(0, skipped=True, reason="データ不足")
        assert r.warnings == 0
        assert r.skipped is True
        assert r.reason == "データ不足"


class TestDataFileError:
    def test_raises_on_missing_file(self):
        with pytest.raises(DataFileError):
            read_csv("/tmp/nonexistent_file_for_test.csv")


class TestRunCheckCli:
    def test_single_file_passes_loaded_rows(self, monkeypatch):
        seen = []

        monkeypatch.setattr("analysis.common.load_journal", lambda _path: [{"id": "1"}])
        monkeypatch.setattr("sys.argv", ["prog", "dummy.csv"])

        def fake_check(rows):
            seen.append(rows)
            return CheckResult(0)

        run_check_cli(fake_check, "single")

        assert seen == [[{"id": "1"}]]

    def test_multi_file_combines_rows(self, monkeypatch):
        monkeypatch.setattr(
            "analysis.common.load_journal",
            lambda path: [{"path": Path(path).name}],
        )
        monkeypatch.setattr("sys.argv", ["prog", "a.csv", "b.csv"])

        seen = []

        def fake_check(rows):
            seen.append(rows)
            return CheckResult(0)

        run_check_cli(fake_check, "multi", multi_file=True)

        assert seen == [[{"path": "a.csv"}, {"path": "b.csv"}]]
