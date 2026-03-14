"""仕訳帳CSVのカラム名定義。"""

import json
from pathlib import Path

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


def side_column(side: str, kind: str) -> str:
    """借方・貸方を受け取り、対応するカラム名を返す。"""
    return f"{side}{kind}"
