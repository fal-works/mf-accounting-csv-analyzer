"""check_receivables.py のテスト。"""

from checks.check_receivables import check_receivables
from conftest import make_simple_row


class TestCheckReceivables:
    def test_balanced(self, capsys):
        """計上と消込が一致していれば残高0。"""
        rows = [
            make_simple_row("1", "2025/01/15", "売掛金", "売上高", "100000"),
            make_simple_row("2", "2025/02/15", "普通預金", "売掛金", "100000"),
        ]
        result = check_receivables(rows)
        out = capsys.readouterr().out
        assert "100,000" in out
        # 差額0 → 繰越の表示なし
        assert "繰り越" not in out
        assert result.warnings == 0

    def test_outstanding_balance(self, capsys):
        """消込が不足していれば繰越残高表示。"""
        rows = [
            make_simple_row("1", "2025/01/15", "売掛金", "売上高", "100000"),
            make_simple_row("2", "2025/01/20", "売掛金", "売上高", "200000"),
            make_simple_row("3", "2025/02/15", "普通預金", "売掛金", "100000"),
        ]
        result = check_receivables(rows)
        out = capsys.readouterr().out
        assert "翌年繰越" in out
        assert result.warnings == 0

    def test_no_transactions(self, capsys):
        """売掛金・未払金の取引がなければ OK。"""
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000"),
        ]
        result = check_receivables(rows)
        out = capsys.readouterr().out
        assert "OK" in out
        assert result.warnings == 0
