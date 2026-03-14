"""CLI の終了コード仕様テスト。"""

from importlib import import_module

import pytest

from checks.common import CheckResult, DataFileError


CHECK_MODULE_CASES = [
    ("checks.check_consistency", "check_consistency", ["dummy.csv"]),
    ("checks.check_dates", "check_monthly_sales", ["dummy.csv"]),
    ("checks.check_duplicates", "check_duplicate_entries", ["dummy.csv"]),
    ("checks.check_outliers", "check_outliers", ["dummy.csv"]),
    ("checks.check_receivables", "check_receivables", ["dummy.csv"]),
    ("checks.check_recurring", "check_recurring", ["dummy.csv"]),
    ("checks.check_tax", "check_tax_categories", ["dummy.csv"]),
    ("checks.check_vendor_consistency", "check_vendor_consistency", ["dummy.csv"]),
    ("checks.check_yoy", "check_yoy", ["dummy.csv"]),
]


@pytest.mark.parametrize(("module_name", "check_func_name", "argv_tail"), CHECK_MODULE_CASES)
def test_check_main_returns_zero_when_warnings_exist(monkeypatch, module_name, check_func_name, argv_tail):
    module = import_module(module_name)

    monkeypatch.setattr(module, "load_journal", lambda _path: [])
    monkeypatch.setattr(module, check_func_name, lambda _rows: CheckResult(2))
    monkeypatch.setattr("sys.argv", ["prog", *argv_tail])

    module.main()


@pytest.mark.parametrize(("module_name", "check_func_name", "argv_tail"), CHECK_MODULE_CASES)
def test_check_main_exits_one_on_data_file_error(monkeypatch, module_name, check_func_name, argv_tail):
    module = import_module(module_name)

    def raise_data_error(_path):
        raise DataFileError("broken")

    monkeypatch.setattr(module, "load_journal", raise_data_error)
    monkeypatch.setattr(module, check_func_name, lambda _rows: CheckResult(0))
    monkeypatch.setattr("sys.argv", ["prog", *argv_tail])

    with pytest.raises(SystemExit) as excinfo:
        module.main()

    assert excinfo.value.code == 1
