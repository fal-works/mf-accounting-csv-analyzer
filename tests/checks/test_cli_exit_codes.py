"""CLI の終了コード仕様テスト。"""

from importlib import import_module

import pytest

from analysis.common import CheckResult, DataFileError

# run_check_cli 経由の標準スクリプト — analysis.common.load_journal だけ patch すればよい
STANDARD_CLI_CASES = [
    ("analysis.checks.check_consistency", "check_consistency", ["dummy.csv"]),
    ("analysis.checks.check_dates", "check_monthly_sales", ["dummy.csv"]),
    ("analysis.checks.check_duplicates", "check_duplicate_entries", ["dummy.csv"]),
    ("analysis.checks.check_receivables", "check_receivables", ["dummy.csv"]),
    ("analysis.checks.check_recurring", "check_recurring", ["dummy.csv"]),
    ("analysis.checks.check_tax", "check_tax_categories", ["dummy.csv"]),
    ("analysis.checks.check_vendor_consistency", "check_vendor_consistency", ["dummy.csv"]),
    ("analysis.checks.check_yoy", "check_yoy", ["dummy.csv"]),
]

# run_summary_cli 経由のサマリーツール
SUMMARY_CLI_CASES = [
    ("analysis.summaries.account_summary", "print_summary", ["dummy.csv"]),
    ("analysis.summaries.account_summary", "print_summary", ["--target", "2025"]),
    ("analysis.summaries.monthly_trend", "print_summary", ["dummy.csv"]),
    ("analysis.summaries.monthly_trend", "print_summary", ["--target", "2025"]),
    ("analysis.summaries.revenue_by_client", "print_summary", ["dummy.csv"]),
    ("analysis.summaries.revenue_by_client", "print_summary", ["--target", "2025"]),
    ("analysis.summaries.tax_summary", "print_summary", ["dummy.csv"]),
    ("analysis.summaries.tax_summary", "print_summary", ["--target", "2025"]),
    ("analysis.summaries.vendor_summary", "print_summary", ["dummy.csv"]),
    ("analysis.summaries.vendor_summary", "print_summary", ["--target", "2025"]),
]


@pytest.mark.parametrize(("module_name", "check_func_name", "argv_tail"), STANDARD_CLI_CASES)
def test_standard_main_returns_zero_when_warnings_exist(monkeypatch, module_name, check_func_name, argv_tail):
    module = import_module(module_name)

    monkeypatch.setattr("analysis.common.load_journal", lambda _path: [])
    monkeypatch.setattr(module, check_func_name, lambda _rows: CheckResult(2))
    monkeypatch.setattr("sys.argv", ["prog", *argv_tail])

    module.main()


@pytest.mark.parametrize(("module_name", "check_func_name", "argv_tail"), STANDARD_CLI_CASES)
def test_standard_main_exits_one_on_data_file_error(monkeypatch, module_name, check_func_name, argv_tail):
    module = import_module(module_name)

    def raise_data_error(_path):
        raise DataFileError("broken")

    monkeypatch.setattr("analysis.common.load_journal", raise_data_error)
    monkeypatch.setattr(module, check_func_name, lambda _rows: CheckResult(0))
    monkeypatch.setattr("sys.argv", ["prog", *argv_tail])

    with pytest.raises(SystemExit) as excinfo:
        module.main()

    assert excinfo.value.code == 1


@pytest.mark.parametrize(("module_name", "check_func_name", "argv_tail"), SUMMARY_CLI_CASES)
def test_summary_main_returns_zero_when_warnings_exist(monkeypatch, module_name, check_func_name, argv_tail):
    module = import_module(module_name)

    monkeypatch.setattr("analysis.common.load_journal", lambda _path: [])
    monkeypatch.setattr(module, check_func_name, lambda _rows, *, pretty=False: None)
    monkeypatch.setattr("sys.argv", ["prog", *argv_tail])

    module.main()


@pytest.mark.parametrize(("module_name", "check_func_name", "argv_tail"), SUMMARY_CLI_CASES)
def test_summary_main_exits_one_on_data_file_error(monkeypatch, module_name, check_func_name, argv_tail):
    module = import_module(module_name)

    def raise_data_error(_path):
        raise DataFileError("broken")

    monkeypatch.setattr("analysis.common.load_journal", raise_data_error)
    monkeypatch.setattr(module, check_func_name, lambda _rows, *, pretty=False: None)
    monkeypatch.setattr("sys.argv", ["prog", *argv_tail])

    with pytest.raises(SystemExit) as excinfo:
        module.main()

    assert excinfo.value.code == 1
