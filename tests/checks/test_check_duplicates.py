"""check_duplicates.py のテスト。"""

from analysis.checks.check_duplicates import check_duplicate_entries
from conftest import make_simple_row


class TestCheckDuplicates:
    def test_no_duplicates(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A"),
            make_simple_row("2", "2025/01/16", "消耗品費", "普通預金", "3000", summary="B"),
        ]
        result = check_duplicate_entries(rows)
        out = capsys.readouterr().out
        assert "OK" in out
        assert result.warnings == 0

    def test_duplicate_detected(self, capsys):
        row = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        dup = make_simple_row("2", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        result = check_duplicate_entries([row, dup])
        out = capsys.readouterr().out
        assert "WARN" in out
        assert result.warnings > 0

    def test_duplicate_prints_single_memo_context(self, capsys):
        row = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A", memo="一括支払い分")
        dup = make_simple_row("2", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        result = check_duplicate_entries([row, dup])
        out = capsys.readouterr().out
        assert "メモ: 一括支払い分" in out
        assert "他に異なるメモあり" not in out
        assert result.warnings == 1

    def test_duplicate_prints_memo_with_difference_note(self, capsys):
        row = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A", memo="3ヶ月分のうち1回目")
        dup = make_simple_row("2", "2025/01/15", "通信費", "普通預金", "5000", summary="A", memo="分割計上あり")
        result = check_duplicate_entries([row, dup])
        out = capsys.readouterr().out
        assert "メモ: 3ヶ月分のうち1回目 (他に異なるメモあり)" in out
        assert result.warnings == 1

    def test_same_tx_no_not_flagged(self, capsys):
        """同一取引No内の複合仕訳は重複としない。"""
        row1 = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        row2 = make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", summary="A")
        result = check_duplicate_entries([row1, row2])
        out = capsys.readouterr().out
        assert "OK" in out
        assert result.warnings == 0
