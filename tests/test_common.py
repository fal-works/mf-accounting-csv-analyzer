"""common.py のユニットテスト。"""

import argparse
from datetime import date
from pathlib import Path

import pytest

from analysis.common import (
    SKIP_ACCOUNTS_COMMON,
    ResolvedJournals,
    CheckResult,
    DataFileError,
    add_journal_args,
    load_target_rows,
    month_key,
    parse_amount,
    parse_date,
    read_csv,
    resolve_journals,
    run_check_cli,
    run_summary_cli,
)
from analysis.journal_columns import JOURNAL_COLUMNS, TX_NO
from conftest import make_simple_row


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

    def test_single_file_target_loads_only_target_year_file(self, monkeypatch):
        loaded_paths = []
        monkeypatch.setattr(
            "analysis.common.resolve_journals",
            lambda _args, _parser: ResolvedJournals(2025, Path("2025.csv"), [Path("2023.csv"), Path("2025.csv")]),
        )
        monkeypatch.setattr(
            "analysis.common.load_journal",
            lambda path: loaded_paths.append(Path(path).name) or [{"path": Path(path).name}],
        )
        monkeypatch.setattr("sys.argv", ["prog", "--target", "2025"])

        seen = []

        def fake_check(rows):
            seen.append(rows)
            return CheckResult(0)

        run_check_cli(fake_check, "single")

        assert loaded_paths == ["2025.csv"]
        assert seen == [[{"path": "2025.csv"}]]

    def test_multi_file_target_loads_all_selected_files(self, monkeypatch):
        monkeypatch.setattr(
            "analysis.common.resolve_journals",
            lambda _args, _parser: ResolvedJournals(2025, Path("2025.csv"), [Path("2024.csv"), Path("2025.csv")]),
        )
        monkeypatch.setattr(
            "analysis.common.load_journal",
            lambda path: [{"path": Path(path).name}],
        )
        monkeypatch.setattr("sys.argv", ["prog", "--target", "2025"])

        seen = []

        def fake_check(rows):
            seen.append(rows)
            return CheckResult(0)

        run_check_cli(fake_check, "multi", multi_file=True)

        assert seen == [[{"path": "2024.csv"}, {"path": "2025.csv"}]]


class TestRunSummaryCli:
    def test_paths_combines_rows(self, monkeypatch):
        monkeypatch.setattr(
            "analysis.common.load_journal",
            lambda path: [{"path": Path(path).name}],
        )
        monkeypatch.setattr("sys.argv", ["prog", "a.csv", "b.csv"])

        seen = []

        def fake_summary(rows):
            seen.append(rows)

        run_summary_cli(fake_summary, "summary")

        assert seen == [[{"path": "a.csv"}, {"path": "b.csv"}]]

    def test_target_loads_target_year_rows(self, monkeypatch):
        monkeypatch.setattr("analysis.common.load_target_rows", lambda year, years=3: [{"year": str(year), "years": str(years)}])
        monkeypatch.setattr("sys.argv", ["prog", "--target", "2025", "--years", "2"])

        seen = []

        def fake_summary(rows):
            seen.append(rows)

        run_summary_cli(fake_summary, "summary")

        assert seen == [[{"year": "2025", "years": "2"}]]


class TestJournalArgs:
    def test_resolve_journals_rejects_target_and_paths_together(self):
        parser = argparse.ArgumentParser()
        add_journal_args(parser)

        with pytest.raises(SystemExit) as excinfo:
            resolve_journals(parser.parse_args(["--target", "2025", "dummy.csv"]), parser)

        assert excinfo.value.code == 2

    def test_resolve_journals_requires_target_or_path(self):
        parser = argparse.ArgumentParser()
        add_journal_args(parser)

        with pytest.raises(SystemExit) as excinfo:
            resolve_journals(parser.parse_args([]), parser)

        assert excinfo.value.code == 2


class TestLoadTargetRows:
    def test_includes_only_target_year(self, tmp_path):
        journal_2024 = tmp_path / "2024" / "仕訳帳.csv"
        journal_2025 = tmp_path / "2025" / "仕訳帳.csv"
        journal_2024.parent.mkdir()
        journal_2025.parent.mkdir()

        with open(journal_2024, "w", encoding="utf-8", newline="") as f:
            import csv

            writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
            writer.writeheader()
            writer.writerow(make_simple_row("2024", "2024/12/31", "通信費", "普通預金", "1000"))

        with open(journal_2025, "w", encoding="utf-8", newline="") as f:
            import csv

            writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
            writer.writeheader()
            writer.writerow(make_simple_row("cross", "2024/12/31", "消耗品費", "普通預金", "500"))
            writer.writerow(make_simple_row("2025", "2025/01/10", "通信費", "普通預金", "2000"))

        rows = load_target_rows(2025, years=2, data_dir=str(tmp_path))

        assert [row[TX_NO] for row in rows] == ["2025"]
