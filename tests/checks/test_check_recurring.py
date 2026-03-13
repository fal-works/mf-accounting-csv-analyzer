"""check_recurring.py のテスト。"""

from check_recurring import check_recurring
from conftest import make_simple_row


class TestCheckRecurring:
    def _make_recurring(self, year: int = 2025, missing_months: set[int] | None = None):
        """12ヶ月分の経費行を生成。missing_months で指定した月は除外。"""
        missing = missing_months or set()
        rows = []
        for m in range(1, 13):
            if m not in missing:
                rows.append(make_simple_row(
                    str(m), f"{year}/{m:02d}/15", "通信費", "普通預金", "5000",
                ))
            # 月の存在を保証するため別科目の行を入れる
            rows.append(make_simple_row(
                str(m + 100), f"{year}/{m:02d}/20", "消耗品費", "普通預金", "1000",
            ))
        return rows

    def test_all_months_present(self, capsys):
        rows = self._make_recurring()
        check_recurring(rows)
        out = capsys.readouterr().out
        assert "OK" in out or "毎月計上" in out

    def test_missing_month(self, capsys):
        rows = self._make_recurring(missing_months={6})
        check_recurring(rows)
        out = capsys.readouterr().out
        assert "WARNING" in out
        assert "2025/06" in out
