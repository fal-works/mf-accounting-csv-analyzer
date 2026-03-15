"""analysis.summaries.runner のテスト。"""

import csv
import sys
from pathlib import Path

import pytest

from analysis.common import DataFileError
from analysis.journal_columns import JOURNAL_COLUMNS, TX_NO
from analysis.summaries.runner import discover_summaries, main, run_all
from tests.conftest import make_simple_row

JOURNAL_FILE = "仕訳帳.csv"


def _write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestDiscoverSummaries:
    def test_discovers_known_summaries(self):
        summaries = discover_summaries()
        names = [name for name, _fn, _m in summaries]

        assert "account_summary" in names
        assert "monthly_trend" in names
        assert "revenue_by_client" in names
        assert "vendor_summary" in names
        assert "tax_summary" in names
        assert "runner" not in names

    def test_multi_year_flag(self):
        summaries = discover_summaries()
        summary_map = {name: multi_year for name, _fn, multi_year in summaries}

        assert summary_map["account_summary"] is False
        assert summary_map["monthly_trend"] is False
        assert summary_map["revenue_by_client"] is False


class TestRunAll:
    def test_run_with_only(self, tmp_path, monkeypatch):
        journal = tmp_path / "2025" / JOURNAL_FILE
        journal.parent.mkdir()
        _write_csv(
            [make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000")],
            journal,
        )

        seen: list[str] = []

        def account_summary(rows):
            seen.append(f"account:{len(rows)}")

        def vendor_summary(rows):
            seen.append(f"vendor:{len(rows)}")

        monkeypatch.setattr(
            "analysis.summaries.runner.discover_summaries",
            lambda: [
                ("account_summary", account_summary, False),
                ("vendor_summary", vendor_summary, False),
            ],
        )

        executed = run_all(2025, data_dir=str(tmp_path), only={"account_summary"})

        assert executed == ["account_summary"]
        assert seen == ["account:1"]

    def test_run_with_skip(self, tmp_path, monkeypatch):
        journal = tmp_path / "2025" / JOURNAL_FILE
        journal.parent.mkdir()
        _write_csv(
            [make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000")],
            journal,
        )

        seen: list[str] = []

        monkeypatch.setattr(
            "analysis.summaries.runner.discover_summaries",
            lambda: [
                ("account_summary", lambda rows: seen.append(f"account:{len(rows)}"), False),
                ("vendor_summary", lambda rows: seen.append(f"vendor:{len(rows)}"), False),
            ],
        )

        executed = run_all(2025, data_dir=str(tmp_path), skip={"vendor_summary"})

        assert executed == ["account_summary"]
        assert seen == ["account:1"]

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

        def single_year_summary(rows):
            seen["single"] = [row[TX_NO] for row in rows]

        def multi_year_summary(rows):
            seen["multi"] = [row[TX_NO] for row in rows]

        monkeypatch.setattr(
            "analysis.summaries.runner.discover_summaries",
            lambda: [
                ("account_summary", single_year_summary, False),
                ("cross_year_summary", multi_year_summary, True),
            ],
        )

        executed = run_all(2025, years=2, data_dir=str(tmp_path))

        assert executed == ["account_summary", "cross_year_summary"]
        assert seen["single"] == ["2025"]
        assert seen["multi"] == ["2024", "2025"]

    def test_uses_selected_journals_without_rediscovery(self, tmp_path, monkeypatch):
        journal = tmp_path / "2025" / JOURNAL_FILE
        journal.parent.mkdir()
        _write_csv(
            [make_simple_row("2025", "2025/02/01", "通信費", "普通預金", "1000")],
            journal,
        )

        monkeypatch.setattr(
            "analysis.summaries.runner.select_journals",
            lambda *args, **kwargs: pytest.fail("select_journals should not be called"),
        )
        monkeypatch.setattr(
            "analysis.summaries.runner.discover_summaries",
            lambda: [("account_summary", lambda rows: None, False)],
        )

        executed = run_all(
            2025,
            selected_journals={2025: journal},
        )

        assert executed == ["account_summary"]

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
    def test_runs_and_prints_period(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "analysis.summaries.runner.select_journals",
            lambda target_year, *, years=3, data_dir="data": {
                2023: Path("data/2023/仕訳帳.csv"),
                2024: Path("data/2024/仕訳帳.csv"),
                2025: Path("data/2025/仕訳帳.csv"),
            },
        )
        monkeypatch.setattr("analysis.summaries.runner.run_all", lambda *args, **kwargs: ["account_summary"])
        monkeypatch.setattr(sys, "argv", ["runner.py", "--target", "2025"])

        main()

        out = capsys.readouterr().out
        assert "対象年度: 2025  期間: 2023-2025 (3年分)" in out

    def test_exits_one_on_data_file_error(self, monkeypatch):
        monkeypatch.setattr(
            "analysis.summaries.runner.select_journals",
            lambda target_year, *, years=3, data_dir="data": {2025: Path("data/2025/仕訳帳.csv")},
        )
        monkeypatch.setattr(
            "analysis.summaries.runner.run_all",
            lambda *args, **kwargs: (_ for _ in ()).throw(DataFileError("broken")),
        )
        monkeypatch.setattr(sys, "argv", ["runner.py", "--target", "2025"])

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1

    def test_list_exits_zero(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "analysis.summaries.runner.discover_summaries",
            lambda: [("account_summary", lambda _rows: None, False)],
        )
        monkeypatch.setattr(sys, "argv", ["runner.py", "--list"])

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 0
        assert "account_summary (単年度)" in capsys.readouterr().out
