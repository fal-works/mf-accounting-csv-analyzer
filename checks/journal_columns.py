"""仕訳帳CSVのカラム名定義。"""

TX_NO = "取引No"
TX_DATE = "取引日"

DEBIT_ACCOUNT = "借方勘定科目"
DEBIT_SUBACCOUNT = "借方補助科目"
DEBIT_VENDOR = "借方取引先"
DEBIT_TAX = "借方税区分"
DEBIT_AMOUNT = "借方金額(円)"

CREDIT_ACCOUNT = "貸方勘定科目"
CREDIT_SUBACCOUNT = "貸方補助科目"
CREDIT_VENDOR = "貸方取引先"
CREDIT_TAX = "貸方税区分"
CREDIT_AMOUNT = "貸方金額(円)"

SUMMARY = "摘要"
MEMO = "メモ"

JOURNAL_COLUMNS = [
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
]


def side_column(side: str, kind: str) -> str:
    """借方・貸方を受け取り、対応するカラム名を返す。"""
    return f"{side}{kind}"
