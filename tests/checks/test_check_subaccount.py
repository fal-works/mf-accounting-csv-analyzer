"""check_subaccount.py のテスト。"""

from analysis.checks.check_subaccount import check_subaccount
from tests.conftest import make_row, make_simple_row


class TestCheckSubaccount:
    def test_no_warning_when_subaccount_always_present(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", debit_sub="携帯"),
            make_simple_row("2", "2025/02/15", "通信費", "普通預金", "5000", debit_sub="固定回線"),
        ]

        result = check_subaccount(rows)
        out = capsys.readouterr().out

        assert "OK" in out
        assert result.warnings == 0

    def test_no_warning_when_subaccount_always_absent(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000"),
            make_simple_row("2", "2025/02/15", "通信費", "普通預金", "5000"),
        ]

        result = check_subaccount(rows)
        out = capsys.readouterr().out

        assert "OK" in out
        assert result.warnings == 0

    def test_warns_when_subaccount_usage_is_mixed(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", debit_sub="携帯"),
            make_simple_row("2", "2025/02/15", "通信費", "普通預金", "5000", debit_sub="固定回線"),
            make_simple_row("3", "2025/03/15", "通信費", "普通預金", "5000"),
        ]

        result = check_subaccount(rows)
        out = capsys.readouterr().out

        assert "WARN" in out
        assert "借方「通信費」" in out
        assert "No.3 (2025/03/15)" in out
        assert result.warnings > 0

    def test_warns_when_present_and_absent_counts_are_tied(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "普通預金", "5000", debit_sub="携帯"),
            make_simple_row("2", "2025/02/15", "通信費", "普通預金", "5000", debit_sub="固定回線"),
            make_simple_row("3", "2025/03/15", "通信費", "普通預金", "5000"),
            make_simple_row("4", "2025/04/15", "通信費", "普通預金", "5000"),
        ]

        result = check_subaccount(rows)
        out = capsys.readouterr().out

        assert "WARN" in out
        assert "補助科目あり 2件 / なし 2件" in out
        assert "少数派=なし" in out
        assert "No.3 (2025/03/15)" in out
        assert "No.4 (2025/04/15)" in out
        assert result.warnings == 1

    def test_skips_common_skip_accounts(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "現金", "売上高", "5000", debit_sub="財布"),
            make_simple_row("2", "2025/02/15", "現金", "売上高", "5000"),
        ]

        result = check_subaccount(rows)
        out = capsys.readouterr().out

        assert "OK" in out
        assert result.warnings == 0

    def test_checks_debit_and_credit_independently(self, capsys):
        rows = [
            make_simple_row("1", "2025/01/15", "通信費", "売上高", "5000", credit_sub="EC"),
            make_simple_row("2", "2025/02/15", "通信費", "売上高", "5000", credit_sub="EC"),
            make_simple_row("3", "2025/03/15", "通信費", "売上高", "5000"),
        ]

        result = check_subaccount(rows)
        out = capsys.readouterr().out

        assert "WARN" in out
        assert "貸方「売上高」" in out
        assert "借方「通信費」" not in out
        assert result.warnings == 1

    def test_ignores_blank_account_rows(self, capsys):
        rows = [
            make_row(),
            make_simple_row("2", "2025/02/15", "通信費", "普通預金", "5000", debit_sub="携帯"),
        ]

        result = check_subaccount(rows)
        out = capsys.readouterr().out

        assert "OK" in out
        assert result.warnings == 0
