"""analysis.common の表整形ユーティリティテスト。"""

from analysis.common import _display_width, format_pretty, format_tsv


def test_format_tsv_joins_with_tabs():
    headers = ["科目", "件数", "合計"]
    rows = [["通信費", "2", "3000"], ["消耗品費", "15", "124500"]]

    assert format_tsv(headers, rows) == (
        "科目\t件数\t合計\n"
        "通信費\t2\t3000\n"
        "消耗品費\t15\t124500"
    )


def test_format_pretty_aligns_columns_with_cjk_width():
    headers = ["科目", "件数", "合計"]
    rows = [["通信費", "2", "3000"], ["消耗品費", "15", "124500"]]

    assert format_pretty(headers, rows) == (
        "科目      件数    合計\n"
        "通信費       2    3000\n"
        "消耗品費    15  124500"
    )


def test_format_pretty_left_aligns_strings_and_right_aligns_numbers():
    headers = ["取引先", "件数", "勘定科目"]
    rows = [["Amazon", "12", "通信費"], ["長い取引先名", "3", "消耗品費, 雑費"]]

    lines = format_pretty(headers, rows).splitlines()

    assert lines[0] == "取引先        件数  勘定科目"
    assert lines[1].startswith("Amazon")
    assert lines[1].endswith("12  通信費")
    assert lines[2].startswith("長い取引先名")
    assert lines[2].endswith("3  消耗品費, 雑費")
    assert "\t" not in format_pretty(headers, rows)


def test_format_pretty_handles_numeric_with_commas_and_negative_values():
    headers = ["項目", "金額"]
    rows = [["売上", "1,234"], ["返金", "-56"]]

    lines = format_pretty(headers, rows).splitlines()

    assert lines[0] == "項目   金額"
    assert lines[1] == "売上  1,234"
    assert lines[2] == "返金    -56"


def test_format_pretty_treats_decimal_strings_as_numeric():
    headers = ["項目", "金額"]
    rows = [["売上", "1,234.5"], ["返金", "-56.0"]]

    lines = format_pretty(headers, rows).splitlines()

    assert lines[1].endswith("1,234.5")
    assert lines[2].endswith("-56.0")


def test_format_pretty_outputs_header_only_for_empty_rows():
    assert format_pretty(["科目", "件数"], []) == "科目  件数"


def test_display_width_counts_ascii_fullwidth_and_mixed_text():
    assert _display_width("abc") == 3
    assert _display_width("あいう") == 6
    assert _display_width("漢字") == 4
    assert _display_width("A漢い") == 5
