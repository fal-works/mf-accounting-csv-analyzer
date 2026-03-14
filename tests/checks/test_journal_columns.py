"""journal_columns の公開定義を検証する。"""

import json
from pathlib import Path

from checks.journal_columns import (
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
    MEMO,
    SUMMARY,
    TX_DATE,
    TX_NO,
)


def test_public_constants_match_schema_columns() -> None:
    schema = json.loads(
        (Path(__file__).resolve().parents[2] / "schema" / "journal.json").read_text(
            encoding="utf-8"
        )
    )

    assert [
        TX_NO,
        TX_DATE,
        DEBIT_ACCOUNT,
        DEBIT_SUBACCOUNT,
        DEBIT_VENDOR,
        DEBIT_TAX,
        DEBIT_AMOUNT,
        CREDIT_ACCOUNT,
        CREDIT_SUBACCOUNT,
        CREDIT_VENDOR,
        CREDIT_TAX,
        CREDIT_AMOUNT,
        SUMMARY,
        MEMO,
    ] == schema["columns"]
    assert JOURNAL_COLUMNS == schema["columns"]
