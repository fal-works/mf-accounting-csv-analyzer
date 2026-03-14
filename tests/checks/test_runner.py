"""runner.py のテスト。"""

import sys

import pytest

from analysis.common import CheckResult, DataFileError
from analysis.checks.runner import discover_checks, main, run_all

import csv
import tempfile
from pathlib import Path

from analysis.journal_columns import JOURNAL_COLUMNS
from conftest import make_simple_row


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


class TestRunAll:
    def test_run_with_only(self, capsys):
        """--only で絞り込めること。"""
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000",
                            debit_tax="課税仕入 10%", credit_tax="対象外"),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            tmp = Path(f.name)
            writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
            writer.writeheader()
            writer.writerow(rows[0])

        results = run_all([str(tmp)], only={"check_tax"})
        assert "check_tax" in results
        assert len(results) == 1

    def test_run_with_skip(self, capsys):
        """--skip で除外できること。"""
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000",
                            debit_tax="課税仕入 10%", credit_tax="対象外"),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            tmp = Path(f.name)
            writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
            writer.writeheader()
            writer.writerow(rows[0])

        results = run_all([str(tmp)], skip={"check_tax"})
        assert "check_tax" in results
        assert results["check_tax"].skipped is True


class TestMain:
    def test_returns_zero_when_warnings_exist(self, monkeypatch, capsys):
        monkeypatch.setattr("analysis.checks.runner.run_all", lambda *args, **kwargs: {
            "check_tax": CheckResult(2),
        })
        monkeypatch.setattr(sys, "argv", ["runner.py", "dummy.csv"])

        main()

        out = capsys.readouterr().out
        assert "警告合計: 2件" in out

    def test_exits_one_on_data_file_error(self, monkeypatch):
        def raise_data_error(*args, **kwargs):
            raise DataFileError("broken")

        monkeypatch.setattr("analysis.checks.runner.run_all", raise_data_error)
        monkeypatch.setattr(sys, "argv", ["runner.py", "dummy.csv"])

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
