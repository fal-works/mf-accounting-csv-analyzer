# analysis/checks/ — 計上ミス検出スクリプト 開発ドキュメント

スクリプトの一覧と個別の補足説明は [catalog.md](catalog.md)を参照。
分析手順は [analysis-flow.md](../analysis-flow.md) を参照。

## CheckResult

全チェック関数は `CheckResult`（NamedTuple）を返す。

- `warnings: int` — 警告件数
- `skipped: bool` — データ不足等でスキップされたか（デフォルト `False`）
- `reason: str` — スキップ理由（デフォルト `""`)

## モジュール属性

各 `check_*.py` はモジュールレベルで以下を定義する。

- `MULTI_YEAR: bool` — 複数年度データを前提とするか（必須）
- `ENABLED: bool` — `False` でランナーの自動検出から除外（省略時 `True`）

## エラー処理

`common.read_csv()` はファイル不在時に `DataFileError` 例外を送出する。
CLIの終了コードは「正常完了なら 0、データ読み込みエラーなら 1」とする。警告ありは正常完了なので exit 0 のまま。
`sys.exit()` は CLI エントリポイント（`main()`）に限定されているため、ランナーやプログラムからは例外として扱える。

## CLI 引数

標準的な個別チェックCLIは、`--target` 等のオプションまたはパス指定のいずれかを受け付けるデュアルモードに統一する。

## 出力形式

チェック結果の主な利用者はLLMエージェントであるため、処理結果は装飾のないシンプルなテキストで出力する。
外部ツール連携の予定はないため、JSON等の機械可読形式は提供しない。

## カラム定数

`analysis/journal_columns.py` が仕訳帳CSVのカラム名定数（`TX_NO`, `DEBIT_ACCOUNT` 等）を提供する。
値は `schema/journal.json` から読み込まれる。チェックスクリプトではこの定数を使い、カラム名を直接文字列で書かない。

## チェックの追加手順

1. `analysis/checks/check_<name>.py` を作成し、`MULTI_YEAR` を定義
2. `check_<name>(rows) -> CheckResult` を実装
3. `tests/checks/test_check_<name>.py` にテストを追加
4. [catalog.md](catalog.md) にスクリプト一覧・偽陽性ガイドを追記
5. ランナーが自動検出するため登録不要

開発中は `ENABLED = False` を設定するか、`check_` プレフィックスを付けないファイル名にする。
