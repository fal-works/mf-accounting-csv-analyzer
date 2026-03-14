"""仕訳帳CSVのカラム名定義。"""

import json
from pathlib import Path
from typing import NamedTuple

_SCHEMA = json.loads(
    (Path(__file__).resolve().parent.parent / "schema" / "journal.json").read_text(
        encoding="utf-8"
    )
)

(
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
) = _SCHEMA["columns"]

JOURNAL_COLUMNS = list(_SCHEMA["columns"])

class Side(NamedTuple):
    """借方・貸方それぞれに対応するカラム定義。"""

    label: str
    account: str
    subaccount: str
    vendor: str
    tax: str
    amount: str


DEBIT_SIDE = Side(
    "借方",
    DEBIT_ACCOUNT,
    DEBIT_SUBACCOUNT,
    DEBIT_VENDOR,
    DEBIT_TAX,
    DEBIT_AMOUNT,
)
CREDIT_SIDE = Side(
    "貸方",
    CREDIT_ACCOUNT,
    CREDIT_SUBACCOUNT,
    CREDIT_VENDOR,
    CREDIT_TAX,
    CREDIT_AMOUNT,
)
SIDES = (DEBIT_SIDE, CREDIT_SIDE)
