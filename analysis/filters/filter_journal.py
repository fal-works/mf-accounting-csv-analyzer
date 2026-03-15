#!/usr/bin/env python3
"""仕訳帳の条件フィルタリング・リスト出力ツール。"""

import argparse
import sys
from dataclasses import dataclass
from datetime import date

from analysis.common import (
    DataFileError,
    add_journal_args,
    format_pretty,
    format_tsv,
    load_journal,
    load_target_rows,
    parse_amount,
    parse_date,
    resolve_journals,
)
from analysis.journal_columns import (
    CREDIT_ACCOUNT,
    CREDIT_AMOUNT,
    CREDIT_SIDE,
    CREDIT_SUBACCOUNT,
    DEBIT_ACCOUNT,
    DEBIT_AMOUNT,
    DEBIT_SIDE,
    DEBIT_SUBACCOUNT,
    SIDES,
    SUMMARY,
    TX_DATE,
    TX_NO,
)

MULTI_YEAR = False
PRETTY_SUMMARY_LIMIT = 40

_OUTPUT_COLUMNS = (
    TX_NO,
    TX_DATE,
    DEBIT_ACCOUNT,
    DEBIT_SUBACCOUNT,
    DEBIT_AMOUNT,
    CREDIT_ACCOUNT,
    CREDIT_SUBACCOUNT,
    CREDIT_AMOUNT,
    SUMMARY,
)
_SIDE_MAP = {
    "debit": DEBIT_SIDE,
    "credit": CREDIT_SIDE,
}


@dataclass(frozen=True)
class FilterCondition:
    """フィルター条件。"""

    account: str | None = None
    subaccount: str | None = None
    vendor: str | None = None
    keyword: str | None = None
    tax: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    amount_min: int | None = None
    amount_max: int | None = None
    side: str | None = None


def _target_sides(cond: FilterCondition):
    if cond.side is None:
        return SIDES
    return (_SIDE_MAP[cond.side],)


def _matches_side_text(row: dict[str, str], cond: FilterCondition, attr: str, needle: str) -> bool:
    return any(needle in row[getattr(side, attr)] for side in _target_sides(cond))


def _amount_value(row: dict[str, str], cond: FilterCondition) -> int | None:
    amounts = [
        amount
        for side in _target_sides(cond)
        if (amount := parse_amount(row[side.amount])) is not None
    ]
    if not amounts:
        return None
    return max(amounts)


def match_row(row: dict[str, str], cond: FilterCondition) -> bool:
    """1行が条件にマッチするか判定する。"""
    if cond.account is not None and not _matches_side_text(row, cond, "account", cond.account):
        return False
    if cond.subaccount is not None and not _matches_side_text(row, cond, "subaccount", cond.subaccount):
        return False
    if cond.vendor is not None and not _matches_side_text(row, cond, "vendor", cond.vendor):
        return False
    if cond.tax is not None and not _matches_side_text(row, cond, "tax", cond.tax):
        return False
    if cond.keyword is not None and cond.keyword not in row[SUMMARY]:
        return False

    if cond.date_from is not None or cond.date_to is not None:
        tx_date = parse_date(row[TX_DATE])
        if tx_date is None:
            return False
        if cond.date_from is not None and tx_date < cond.date_from:
            return False
        if cond.date_to is not None and tx_date > cond.date_to:
            return False

    if cond.amount_min is not None or cond.amount_max is not None:
        amount = _amount_value(row, cond)
        if amount is None:
            return False
        if cond.amount_min is not None and amount < cond.amount_min:
            return False
        if cond.amount_max is not None and amount > cond.amount_max:
            return False

    return True


def filter_rows(rows: list[dict[str, str]], cond: FilterCondition) -> list[dict[str, str]]:
    """条件にマッチする行を返す。"""
    return [row for row in rows if match_row(row, cond)]


def _format_summary(value: str, *, pretty: bool) -> str:
    """pretty出力時のみ長い摘要を省略表示する。"""
    if not pretty or len(value) <= PRETTY_SUMMARY_LIMIT:
        return value
    return value[:PRETTY_SUMMARY_LIMIT] + "…"


def print_rows(rows: list[dict[str, str]], *, pretty: bool = False) -> None:
    """フィルター結果を表形式で出力する。"""
    formatted_rows = []
    for row in rows:
        values = []
        for column in _OUTPUT_COLUMNS:
            value = row[column]
            if column == SUMMARY:
                value = _format_summary(value, pretty=pretty)
            values.append(value)
        formatted_rows.append(values)
    formatter = format_pretty if pretty else format_tsv
    print(formatter(list(_OUTPUT_COLUMNS), formatted_rows))
    print(f"（{len(rows)}件）")


def _parse_date_arg(value: str) -> date:
    parsed = parse_date(value)
    if parsed is None:
        raise argparse.ArgumentTypeError("日付は YYYY/MM/DD 形式で指定してください")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="仕訳帳の条件フィルタリング・リスト出力ツール")
    add_journal_args(parser, allow_multiple_paths=False, include_years=False)
    parser.add_argument("--account", help="勘定科目の部分一致（借方・貸方いずれか）")
    parser.add_argument("--subaccount", help="補助科目の部分一致")
    parser.add_argument("--vendor", help="取引先の部分一致")
    parser.add_argument("--keyword", help="摘要の部分一致")
    parser.add_argument("--tax", help="税区分の部分一致")
    parser.add_argument("--date-from", type=_parse_date_arg, help="日付の下限（YYYY/MM/DD）")
    parser.add_argument("--date-to", type=_parse_date_arg, help="日付の上限（YYYY/MM/DD）")
    parser.add_argument("--amount-min", type=int, help="金額の下限（以上）")
    parser.add_argument("--amount-max", type=int, help="金額の上限（以下）")
    parser.add_argument("--side", choices=("debit", "credit"), help="条件判定の対象を借方/貸方に限定")
    parser.add_argument("--pretty", action="store_true", help="人間向け整形出力")
    return parser


def _validate_condition(parser: argparse.ArgumentParser, cond: FilterCondition) -> None:
    if cond.date_from is not None and cond.date_to is not None and cond.date_from > cond.date_to:
        parser.error("--date-from は --date-to 以下にしてください")
    if cond.amount_min is not None and cond.amount_max is not None and cond.amount_min > cond.amount_max:
        parser.error("--amount-min は --amount-max 以下にしてください")

    if not any(
        value is not None
        for key, value in cond.__dict__.items()
        if key != "side"
    ):
        parser.error("フィルター条件を1つ以上指定してください")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.journals is None:
        args.journals = []
    elif isinstance(args.journals, str):
        args.journals = [args.journals]
    cond = FilterCondition(
        account=args.account,
        subaccount=args.subaccount,
        vendor=args.vendor,
        keyword=args.keyword,
        tax=args.tax,
        date_from=args.date_from,
        date_to=args.date_to,
        amount_min=args.amount_min,
        amount_max=args.amount_max,
        side=args.side,
    )
    _validate_condition(parser, cond)

    try:
        resolved = resolve_journals(args, parser)
        if resolved.target_year is not None:
            rows = load_target_rows(resolved.target_year, years=1)
        else:
            rows = load_journal(resolved.paths[0])
    except DataFileError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print_rows(filter_rows(rows, cond), pretty=args.pretty)


if __name__ == "__main__":
    main()
