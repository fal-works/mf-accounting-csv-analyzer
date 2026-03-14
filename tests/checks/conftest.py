"""analysis.checks テスト共通のフィクスチャとヘルパー。"""

from analysis.journal_columns import (
    CREDIT_ACCOUNT,
    CREDIT_AMOUNT,
    CREDIT_SUBACCOUNT,
    CREDIT_TAX,
    CREDIT_VENDOR,
    DEBIT_ACCOUNT,
    DEBIT_AMOUNT,
    DEBIT_SUBACCOUNT,
    DEBIT_TAX,
    DEBIT_VENDOR,
    JOURNAL_COLUMNS,
    SUMMARY,
    TX_DATE,
    TX_NO,
)


def make_row(**overrides: str) -> dict[str, str]:
    """仕訳帳の1行を生成する。指定しないカラムは空文字。"""
    row = {col: "" for col in JOURNAL_COLUMNS}
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
            TX_NO: tx_no,
            TX_DATE: tx_date,
            DEBIT_ACCOUNT: debit_account,
            DEBIT_SUBACCOUNT: debit_sub,
            DEBIT_VENDOR: debit_vendor,
            DEBIT_TAX: debit_tax,
            DEBIT_AMOUNT: amount,
            CREDIT_ACCOUNT: credit_account,
            CREDIT_SUBACCOUNT: credit_sub,
            CREDIT_VENDOR: credit_vendor,
            CREDIT_TAX: credit_tax,
            CREDIT_AMOUNT: amount,
            SUMMARY: summary,
        }
    )
