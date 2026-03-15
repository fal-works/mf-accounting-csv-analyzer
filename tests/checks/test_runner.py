"""runner.py のテスト。"""

import csv
import sys
from pathlib import Path

import pytest

from analysis.checks.runner import discover_checks, discover_journals, main, run_all
from analysis.common import CheckResult, DataFileError
from analysis.journal_columns import TX_NO, JOURNAL_COLUMNS
from conftest import make_simple_row

JOURNAL_FILE = "仕訳帳.csv"


def _write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestDiscoverChecks:
    def test_discovers_known_checks(self):
        checks = discover_checks()
        names = [name for name, _fn, _m in checks]
        assert "check_tax" in names
        assert "check_dates" in names
        assert "check_yoy" in names
        assert "check_outliers" not in names

    def test_multi_year_flag(self):
        checks = discover_checks()
        check_map = {name: multi for name, _fn, multi in checks}
        assert check_map["check_yoy"] is True
        assert check_map["check_dates"] is False


class TestDiscoverJournals:
    def test_discovers_year_directories(self, tmp_path):
        journal_2024 = tmp_path / "2024" / JOURNAL_FILE
        journal_2025 = tmp_path / "2025" / JOURNAL_FILE
        journal_2024.parent.mkdir()
        journal_2025.parent.mkdir()
        _write_csv([], journal_2024)
        _write_csv([], journal_2025)

        discovered = discover_journals(str(tmp_path))

        assert discovered == {
            2024: journal_2024,
            2025: journal_2025,
        }

    def test_ignores_non_year_directories(self, tmp_path):
        invalid_journal = tmp_path / "latest" / JOURNAL_FILE
        invalid_journal.parent.mkdir()
        _write_csv([], invalid_journal)

        with pytest.raises(DataFileError):
            discover_journals(str(tmp_path))

    def test_raises_when_no_journal_found(self, tmp_path):
        with pytest.raises(DataFileError):
            discover_journals(str(tmp_path))


class TestRunAll:
    def test_run_with_only(self, tmp_path):
        """--only で絞り込めること。"""
        journal = tmp_path / "2025" / JOURNAL_FILE
        journal.parent.mkdir()
        _write_csv(
            [
                make_simple_row(
                    "1",
                    "2025/01/15",
                    "通信費",
                    "普通預金",
                    "5000",
                    debit_tax="課税仕入 10%",
                    credit_tax="対象外",
                )
            ],
            journal,
        )

        results = run_all(2025, data_dir=str(tmp_path), only={"check_tax"})
        assert "check_tax" in results
        assert len(results) == 1

    def test_run_with_skip(self, tmp_path):
        """--skip で除外できること。"""
        journal = tmp_path / "2025" / JOURNAL_FILE
        journal.parent.mkdir()
        _write_csv(
            [
                make_simple_row(
                    "1",
                    "2025/01/15",
                    "通信費",
                    "普通預金",
                    "5000",
                    debit_tax="課税仕入 10%",
                    credit_tax="対象外",
                )
            ],
            journal,
        )

        results = run_all(2025, data_dir=str(tmp_path), skip={"check_tax"})
        assert "check_tax" in results
        assert results["check_tax"].skipped is True

    def test_routes_target_rows_and_multi_year_rows(self, tmp_path, monkeypatch):
        paths = {
            2024: tmp_path / "2024" / JOURNAL_FILE,
            2025: tmp_path / "2025" / JOURNAL_FILE,
        }
        for year, path in paths.items():
            path.parent.mkdir()
            _write_csv(
                [make_simple_row(str(year), f"{year}/01/15", "通信費", "普通預金", "1000")],
                path,
            )

        seen: dict[str, list[str]] = {}

        def single_year_check(rows):
            seen["single"] = [row[TX_NO] for row in rows]
            return CheckResult(len(rows))

        def multi_year_check(rows):
            seen["multi"] = [row[TX_NO] for row in rows]
            return CheckResult(len(rows))

        monkeypatch.setattr(
            "analysis.checks.runner.discover_checks",
            lambda: [
                ("check_single", single_year_check, False),
                ("check_multi", multi_year_check, True),
            ],
        )

        results = run_all(2025, years=2, data_dir=str(tmp_path))

        assert seen["single"] == ["2025"]
        assert seen["multi"] == ["2024", "2025"]
        assert results["check_single"] == CheckResult(1)
        assert results["check_multi"] == CheckResult(2)

    def test_respects_years_window(self, tmp_path, monkeypatch):
        for year in (2022, 2023, 2024, 2025):
            journal = tmp_path / str(year) / JOURNAL_FILE
            journal.parent.mkdir()
            _write_csv(
                [make_simple_row(str(year), f"{year}/02/01", "通信費", "普通預金", "1000")],
                journal,
            )

        seen: dict[str, list[str]] = {}

        def multi_year_check(rows):
            seen["multi"] = [row[TX_NO] for row in rows]
            return CheckResult(len(rows))

        monkeypatch.setattr(
            "analysis.checks.runner.discover_checks",
            lambda: [("check_multi", multi_year_check, True)],
        )

        run_all(2025, years=3, data_dir=str(tmp_path))

        assert seen["multi"] == ["2023", "2024", "2025"]

    def test_uses_selected_journals_without_rediscovery(self, tmp_path, monkeypatch):
        journal = tmp_path / "2025" / JOURNAL_FILE
        journal.parent.mkdir()
        _write_csv(
            [make_simple_row("2025", "2025/02/01", "通信費", "普通預金", "1000")],
            journal,
        )

        monkeypatch.setattr(
            "analysis.checks.runner.select_journals",
            lambda *args, **kwargs: pytest.fail("select_journals should not be called"),
        )
        monkeypatch.setattr(
            "analysis.checks.runner.discover_checks",
            lambda: [("check_single", lambda rows: CheckResult(len(rows)), False)],
        )

        results = run_all(
            2025,
            selected_journals={2025: journal},
        )

        assert results["check_single"] == CheckResult(1)

    def test_raises_when_target_year_missing(self, tmp_path):
        journal = tmp_path / "2024" / JOURNAL_FILE
        journal.parent.mkdir()
        _write_csv(
            [make_simple_row("1", "2024/01/15", "通信費", "普通預金", "1000")],
            journal,
        )

        with pytest.raises(DataFileError):
            run_all(2025, data_dir=str(tmp_path))


class TestMain:
    def test_returns_zero_when_warnings_exist(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "analysis.checks.runner.select_journals",
            lambda target_year, *, years=3, data_dir="data": {
                2023: Path("data/2023/仕訳帳.csv"),
                2024: Path("data/2024/仕訳帳.csv"),
                2025: Path("data/2025/仕訳帳.csv"),
            },
        )
        monkeypatch.setattr("analysis.checks.runner.run_all", lambda *args, **kwargs: {
            "check_tax": CheckResult(2),
        })
        monkeypatch.setattr(sys, "argv", ["runner.py", "--target", "2025"])

        main()

        out = capsys.readouterr().out
        assert "対象年度: 2025  期間: 2023-2025 (3年分)" in out
        assert "警告合計: 2件" in out

    def test_exits_one_on_data_file_error(self, monkeypatch):
        def raise_data_error(*args, **kwargs):
            raise DataFileError("broken")

        monkeypatch.setattr("analysis.checks.runner.run_all", raise_data_error)
        monkeypatch.setattr(
            "analysis.checks.runner.select_journals",
            lambda target_year, *, years=3, data_dir="data": {2025: Path("data/2025/仕訳帳.csv")},
        )
        monkeypatch.setattr(sys, "argv", ["runner.py", "--target", "2025"])

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1

    def test_list_exits_zero(self, monkeypatch):
        monkeypatch.setattr("analysis.checks.runner.discover_checks", lambda: [
            ("check_tax", lambda _rows: CheckResult(0), False),
        ])
        monkeypatch.setattr(sys, "argv", ["runner.py", "--list"])

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 0
