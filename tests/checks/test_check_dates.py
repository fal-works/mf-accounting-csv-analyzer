"""check_dates.py のテスト。"""

from checks.check_dates import check_monthly_sales
from conftest import make_simple_row


class TestCheckDates:
    def _make_monthly_sales(self, year: int = 2025, missing_months: set[int] | None = None):
        """12ヶ月分の売上行を生成。missing_months で指定した月は除外。"""
        missing = missing_months or set()
        rows = []
        for m in range(1, 13):
            if m in missing:
                rows.append(make_simple_row(
                    str(m), f"{year}/{m:02d}/15", "通信費", "普通預金", "5000",
                ))
            else:
                rows.append(make_simple_row(
                    str(m), f"{year}/{m:02d}/15", "売掛金", "売上高", "100000",
                ))
        return rows

    def test_no_missing(self, capsys):
        rows = self._make_monthly_sales()
        result = check_monthly_sales(rows)
        out = capsys.readouterr().out
        assert "OK" in out
        assert result.warnings == 0

    def test_missing_months(self, capsys):
        rows = self._make_monthly_sales(missing_months={3, 7})
        result = check_monthly_sales(rows)
        out = capsys.readouterr().out
        assert "2025/03" in out
        assert "2025/07" in out
        assert "WARN" in out
        assert result.warnings > 0
