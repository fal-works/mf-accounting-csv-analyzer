"""common.py のユニットテスト。"""

from datetime import date

from common import SKIP_ACCOUNTS_COMMON, month_key, parse_amount, parse_date


class TestParseDate:
    def test_valid(self):
        assert parse_date("2025/01/15") == date(2025, 1, 15)

    def test_padded(self):
        assert parse_date("  2025/01/15  ") == date(2025, 1, 15)

    def test_invalid(self):
        assert parse_date("invalid") is None

    def test_empty(self):
        assert parse_date("") is None


class TestMonthKey:
    def test_basic(self):
        assert month_key(date(2025, 1, 15)) == "2025/01"

    def test_december(self):
        assert month_key(date(2025, 12, 31)) == "2025/12"


class TestParseAmount:
    def test_valid(self):
        assert parse_amount("12345") == 12345

    def test_zero(self):
        assert parse_amount("0") == 0

    def test_invalid(self):
        assert parse_amount("abc") is None

    def test_empty(self):
        assert parse_amount("") is None

    def test_none(self):
        assert parse_amount(None) is None


class TestSkipAccountsCommon:
    def test_is_frozenset(self):
        assert isinstance(SKIP_ACCOUNTS_COMMON, frozenset)

    def test_contains_expected(self):
        for name in ["事業主貸", "事業主借", "元入金", "現金", "普通預金"]:
            assert name in SKIP_ACCOUNTS_COMMON
