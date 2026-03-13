"""check_outliers.py のテスト。"""

from check_outliers import check_outliers
from conftest import make_simple_row


class TestCheckOutliers:
    def test_no_outliers(self, capsys):
        rows = [
            make_simple_row(str(i), f"2025/01/{i+1:02d}", "通信費", "普通預金", "5000")
            for i in range(5)
        ]
        check_outliers(rows)
        out = capsys.readouterr().out
        assert "OK" in out

    def test_outlier_detected(self, capsys):
        rows = [
            make_simple_row(str(i), f"2025/01/{i+1:02d}", "通信費", "普通預金", "5000")
            for i in range(5)
        ]
        # 桁違いの金額を追加
        rows.append(make_simple_row("99", "2025/02/01", "通信費", "普通預金", "500000"))
        check_outliers(rows)
        out = capsys.readouterr().out
        assert "WARNING" in out
        assert "500,000" in out

    def test_skip_accounts_ignored(self, capsys):
        """SKIP_ACCOUNTS に含まれる科目は検査対象外。"""
        rows = [
            make_simple_row(str(i), f"2025/01/{i+1:02d}", "普通預金", "売掛金", "100000")
            for i in range(5)
        ]
        rows.append(make_simple_row("99", "2025/02/01", "普通預金", "売掛金", "9999999"))
        check_outliers(rows)
        out = capsys.readouterr().out
        assert "OK" in out
