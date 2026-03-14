"""check_vendor_consistency.py のテスト。"""

from check_vendor_consistency import check_vendor_consistency
from conftest import make_simple_row


class TestCheckVendorConsistency:
    def test_consistent(self, capsys):
        rows = [
            make_simple_row(
                "1", "2025/01/15", "通信費", "普通預金", "5000",
                debit_vendor="NTT", debit_tax="課税仕入 10%",
            ),
            make_simple_row(
                "2", "2025/02/15", "通信費", "普通預金", "5000",
                debit_vendor="NTT", debit_tax="課税仕入 10%",
            ),
        ]
        check_vendor_consistency(rows)
        out = capsys.readouterr().out
        assert "OK" in out

    def test_inconsistent(self, capsys):
        rows = [
            make_simple_row(
                "1", "2025/01/15", "通信費", "普通預金", "5000",
                debit_vendor="NTT", debit_tax="課税仕入 10%",
            ),
            make_simple_row(
                "2", "2025/02/15", "通信費", "普通預金", "5000",
                debit_vendor="NTT", debit_tax="課税仕入 10%",
            ),
            make_simple_row(
                "3", "2025/03/15", "通信費", "普通預金", "5000",
                debit_vendor="NTT", debit_tax="課税仕入 10%",
            ),
            make_simple_row(
                "4", "2025/04/15", "消耗品費", "普通預金", "5000",
                debit_vendor="NTT", debit_tax="課税仕入 10%",
            ),
        ]
        check_vendor_consistency(rows)
        out = capsys.readouterr().out
        assert "WARN" in out
        assert "NTT" in out
