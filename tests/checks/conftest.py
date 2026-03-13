"""checks/ テスト共通のフィクスチャとヘルパー。"""

import sys
from pathlib import Path

# checks/ モジュールを import 可能にする
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "checks"))

# 仕訳帳CSVの全カラム
_JOURNAL_COLUMNS = [
    "取引No", "取引日",
    "借方勘定科目", "借方補助科目", "借方取引先", "借方税区分", "借方金額(円)",
    "貸方勘定科目", "貸方補助科目", "貸方取引先", "貸方税区分", "貸方金額(円)",
    "摘要", "メモ",
]


def make_row(**overrides: str) -> dict[str, str]:
    """仕訳帳の1行を生成する。指定しないカラムは空文字。"""
    row = {col: "" for col in _JOURNAL_COLUMNS}
    row.update(overrides)
    return row


def make_simple_row(
    tx_no: str,
    tx_date: str,
    debit_account: str,
    credit_account: str,
    amount: str,
    *,
    summary: str = "",
    debit_tax: str = "",
    credit_tax: str = "",
    debit_sub: str = "",
    credit_sub: str = "",
    debit_vendor: str = "",
    credit_vendor: str = "",
) -> dict[str, str]:
    """よく使うパターンの仕訳行を簡潔に生成する。"""
    return make_row(
        **{
            "取引No": tx_no,
            "取引日": tx_date,
            "借方勘定科目": debit_account,
            "借方補助科目": debit_sub,
            "借方取引先": debit_vendor,
            "借方税区分": debit_tax,
            "借方金額(円)": amount,
            "貸方勘定科目": credit_account,
            "貸方補助科目": credit_sub,
            "貸方取引先": credit_vendor,
            "貸方税区分": credit_tax,
            "貸方金額(円)": amount,
            "摘要": summary,
        }
    )
