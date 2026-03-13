"""check_yoy.py のテスト。"""

from check_yoy import check_yoy
from conftest import make_simple_row


class TestCheckYoY:
    def _make_two_years(self, amounts_2024: int, amounts_2025: int):
        """2年分の通信費行を生成。"""
        rows = []
        for m in range(1, 13):
            rows.append(make_simple_row(
                str(m), f"2024/{m:02d}/15", "通信費", "普通預金", str(amounts_2024),
                debit_tax="課税仕入 10%", credit_tax="対象外",
            ))
            rows.append(make_simple_row(
                str(m + 12), f"2025/{m:02d}/15", "通信費", "普通預金", str(amounts_2025),
                debit_tax="課税仕入 10%", credit_tax="対象外",
            ))
        return rows

    def test_no_change(self, capsys):
        rows = self._make_two_years(5000, 5000)
        check_yoy(rows)
        out = capsys.readouterr().out
        assert "OK" in out

    def test_large_change(self, capsys):
        rows = self._make_two_years(5000, 50000)
        check_yoy(rows)
        out = capsys.readouterr().out
        assert "WARNING" in out
        assert "通信費" in out

    def test_single_year_warns(self, capsys):
        """1年分だけではデータ不足の警告。"""
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000"),
        ]
        check_yoy(rows)
        out = capsys.readouterr().out
        assert "最低2年度" in out
