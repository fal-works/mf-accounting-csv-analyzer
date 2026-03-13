"""check_duplicates.py のテスト。"""

from check_duplicates import check_duplicate_entries
from conftest import make_simple_row


class TestCheckDuplicates:
    def test_no_duplicates(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A"),
            make_simple_row("2", "2025/01/16", "消耗品費", "普通預金", "3000", summary="B"),
        ]
        check_duplicate_entries(rows)
        out = capsys.readouterr().out
        assert "OK" in out

    def test_duplicate_detected(self, capsys):
        row = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        dup = make_simple_row("2", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        check_duplicate_entries([row, dup])
        out = capsys.readouterr().out
        assert "WARNING" in out

    def test_same_tx_no_not_flagged(self, capsys):
        """同一取引No内の複合仕訳は重複としない。"""
        row1 = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        row2 = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        check_duplicate_entries([row1, row2])
        out = capsys.readouterr().out
        assert "OK" in out
