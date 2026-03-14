"""account_summary.py のテスト。"""

from analysis.common import median
from analysis.tools.account_summary import print_summary, summarize_accounts
from conftest import make_simple_row


def test_summarize_accounts_excludes_skip_accounts():
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1200"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "3600"),
        make_simple_row("3", "2025/01/25", "消耗品費", "普通預金", "800"),
        make_simple_row("4", "2025/01/31", "普通預金", "売掛金", "999999"),
    ]

    assert summarize_accounts(rows) == [
        ("消耗品費", 1, 800, 800.0, 800.0, 800, 800),
        ("通信費", 2, 4800, 2400.0, 2400.0, 1200, 3600),
    ]


def test_print_summary_outputs_tsv(capsys):
    rows = [
        make_simple_row("1", "2025/01/10", "通信費", "普通預金", "1000"),
        make_simple_row("2", "2025/01/20", "通信費", "普通預金", "2000"),
        make_simple_row("3", "2025/01/25", "新聞図書費", "普通預金", "1500"),
    ]

    print_summary(rows)
    out = capsys.readouterr().out.strip().splitlines()

    assert out[0] == "科目\t件数\t合計\t平均\t中央値\t最小\t最大"
    assert out[1] == "新聞図書費\t1\t1500\t1500\t1500\t1500\t1500"
    assert out[2] == "通信費\t2\t3000\t1500\t1500\t1000\t2000"


def test_median_handles_even_and_odd_counts():
    assert median([1, 9, 5]) == 5.0
    assert median([1, 9, 5, 7]) == 6.0
