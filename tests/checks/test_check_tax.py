"""check_tax.py のテスト。"""

from checks.check_tax import check_tax_categories
from conftest import make_simple_row


class TestCheckTax:
    def test_valid_entries(self, capsys):
        rows = [
            make_simple_row(
                "1", "2025/01/15", "通信費", "普通預金", "5000",
                debit_tax="課税仕入 10%", credit_tax="対象外",
            ),
            make_simple_row(
                "2", "2025/01/20", "売掛金", "売上高", "100000",
                debit_tax="対象外", credit_tax="課税売上 10% 五種",
            ),
        ]
        warnings = check_tax_categories(rows)
        assert warnings.warnings == 0

    def test_invalid_tax_category(self, capsys):
        rows = [
            make_simple_row(
                "1", "2025/01/15", "通信費", "普通預金", "5000",
                debit_tax="不明な区分", credit_tax="対象外",
            ),
        ]
        warnings = check_tax_categories(rows)
        assert warnings.warnings > 0
        out = capsys.readouterr().out
        assert "不明な区分" in out

    def test_non_taxable_account_with_tax(self, capsys):
        """非課税科目に課税区分が付いていればエラー。"""
        rows = [
            make_simple_row(
                "1", "2025/01/15", "事業主貸", "普通預金", "5000",
                debit_tax="課税仕入 10%", credit_tax="対象外",
            ),
        ]
        warnings = check_tax_categories(rows)
        assert warnings.warnings > 0

    def test_unlisted_expense_account_with_sales_tax(self, capsys):
        """明示列挙されていない経費科目でも売上系税区分を検出する。"""
        rows = [
            make_simple_row(
                "1", "2025/01/15", "旅費交通費", "普通預金", "5000",
                debit_tax="課税売上 10% 五種", credit_tax="対象外",
            ),
        ]
        warnings = check_tax_categories(rows)
        assert warnings.warnings > 0
        out = capsys.readouterr().out
        assert "旅費交通費" in out
        assert "課税売上 10% 五種" in out
