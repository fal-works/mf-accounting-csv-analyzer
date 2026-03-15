"""check_recurring_amount.py のテスト。"""

from analysis.checks.check_recurring_amount import check_recurring_amount
from tests.conftest import make_simple_row


class TestCheckRecurringAmount:
    def _make_monthly(
        self,
        year: int = 2025,
        amount: str = "5000",
        *,
        override_months: dict[int, str] | None = None,
        vendor: str = "テスト株式会社",
    ):
        """12ヶ月分の定期課金行を生成。override_months で特定月の金額を差し替え。"""
        overrides = override_months or {}
        rows = []
        for m in range(1, 13):
            amt = overrides.get(m, amount)
            rows.append(make_simple_row(
                str(m), f"{year}/{m:02d}/15", "支払手数料", "普通預金", amt,
                debit_vendor=vendor,
                summary=f"{vendor} サービス利用料",
            ))
        return rows

    def test_stable_amounts(self, capsys):
        """全月が同額なら警告なし。"""
        rows = self._make_monthly()
        result = check_recurring_amount(rows)
        out = capsys.readouterr().out
        assert "OK" in out
        assert result.warnings == 0

    def test_outlier_low(self, capsys):
        """1ヶ月だけ極端に少額なら警告。"""
        rows = self._make_monthly(override_months={8: "100"})
        result = check_recurring_amount(rows)
        out = capsys.readouterr().out
        assert "WARN" in out
        assert "2025/08" in out
        assert "過小" in out
        assert result.warnings == 1

    def test_outlier_high(self, capsys):
        """1ヶ月だけ極端に高額なら警告。"""
        rows = self._make_monthly(override_months={3: "30000"})
        result = check_recurring_amount(rows)
        out = capsys.readouterr().out
        assert "WARN" in out
        assert "2025/03" in out
        assert "過大" in out
        assert result.warnings == 1

    def test_within_threshold(self, capsys):
        """中央値から50%以内の変動なら警告なし。"""
        # 5000 の 50% = 2500〜7500 の範囲内
        rows = self._make_monthly(override_months={6: "3000", 7: "7000"})
        result = check_recurring_amount(rows)
        out = capsys.readouterr().out
        assert "OK" in out
        assert result.warnings == 0

    def test_too_few_months(self, capsys):
        """月数が MIN_MONTHS 未満なら判定対象外。"""
        rows = []
        for m in range(1, 4):  # 3ヶ月分だけ
            rows.append(make_simple_row(
                str(m), f"2025/{m:02d}/15", "支払手数料", "普通預金", "5000",
                debit_vendor="テスト株式会社",
                summary="テスト株式会社 サービス利用料",
            ))
        # 別科目で月の存在を保証
        for m in range(1, 13):
            rows.append(make_simple_row(
                str(m + 100), f"2025/{m:02d}/20", "消耗品費", "普通預金", "1000",
            ))
        result = check_recurring_amount(rows)
        assert result.warnings == 0

    def test_empty_data(self):
        """空データではスキップ。"""
        result = check_recurring_amount([])
        assert result.skipped is True

    def test_vendor_fallback_to_summary(self, capsys):
        """取引先が空でも摘要の先頭語でグループ化できる。"""
        rows = []
        for m in range(1, 13):
            amt = "100" if m == 5 else "10000"
            rows.append(make_simple_row(
                str(m), f"2025/{m:02d}/21", "支払手数料", "普通預金", amt,
                summary="Anthropic, PBC AI利用料",
            ))
        result = check_recurring_amount(rows)
        out = capsys.readouterr().out
        assert "WARN" in out
        assert "2025/05" in out
        assert "Anthropic," in out
        assert result.warnings == 1

    def test_multiple_outliers(self, capsys):
        """複数月が異常値なら複数警告。"""
        rows = self._make_monthly(override_months={2: "200", 11: "50000"})
        result = check_recurring_amount(rows)
        out = capsys.readouterr().out
        assert result.warnings == 2
