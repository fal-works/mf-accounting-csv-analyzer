"""check_consistency.py のテスト。"""

from analysis.checks.check_consistency import check_consistency
from tests.conftest import make_simple_row


class TestCheckConsistency:
    def test_consistent(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="電話代"),
            make_simple_row("2", "2025/02/15", "通信費", "普通預金", "5000", summary="電話代"),
        ]
        result = check_consistency(rows)
        out = capsys.readouterr().out
        assert "OK" in out
        assert result.warnings == 0

    def test_inconsistent(self, capsys):
        """同じ摘要に異なる科目が使われていれば警告。"""
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="電話代"),
            make_simple_row("2", "2025/02/15", "通信費", "普通預金", "5000", summary="電話代"),
            make_simple_row("3", "2025/03/15", "通信費", "普通預金", "5000", summary="電話代"),
            make_simple_row("4", "2025/04/15", "消耗品費", "普通預金", "5000", summary="電話代"),
        ]
        result = check_consistency(rows)
        out = capsys.readouterr().out
        assert "WARN" in out
        assert "電話代" in out
        assert result.warnings > 0
