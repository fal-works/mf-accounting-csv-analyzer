"""runner.py のテスト。"""

from checks.runner import discover_checks, run_all

import csv
import tempfile
from pathlib import Path

from conftest import make_simple_row

# テスト用の最小限CSV
_COLUMNS = [
    "取引No", "取引日",
    "借方勘定科目", "借方補助科目", "借方取引先", "借方税区分", "借方金額(円)",
    "貸方勘定科目", "貸方補助科目", "貸方取引先", "貸方税区分", "貸方金額(円)",
    "摘要", "メモ",
]


def _write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNS)
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
            writer = csv.DictWriter(f, fieldnames=_COLUMNS)
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
            writer = csv.DictWriter(f, fieldnames=_COLUMNS)
            writer.writeheader()
            writer.writerow(rows[0])

        results = run_all([str(tmp)], skip={"check_tax"})
        assert "check_tax" in results
        assert results["check_tax"].skipped is True
