# checks/ — 計上ミス検出スクリプト

分析手順は [analysis-flow.md](analysis-flow.md) を参照。

## 実行

```bash
# 一括実行（推奨）
python -m checks.runner data/*/仕訳帳.csv

# 選択実行・除外
python -m checks.runner data/2025/仕訳帳.csv --only check_tax,check_dates
python -m checks.runner data/*/仕訳帳.csv --skip check_yoy

# 一覧表示
python -m checks.runner --list

# 個別実行
python checks/check_tax.py data/2025/仕訳帳.csv
python checks/check_outliers.py data/*/仕訳帳.csv --summary
```

## スクリプト一覧

| スクリプト | 年度 | 目的 |
|---|---|---|
| `check_tax` | 単年度 | 税区分の有効値・科目との整合性 |
| `check_duplicates` | 単年度 | 同一内容の二重入力 |
| `check_dates` | 単年度 | 売上高の月次計上漏れ |
| `check_recurring` | 単年度 | 定期経費の欠落月 |
| `check_receivables` | 単年度 | 売掛金・未払金の消込状況 |
| `check_consistency` | 複数可 | 摘要×科目の揺れ |
| `check_vendor_consistency` | 複数可 | 取引先×科目・税区分の揺れ |
| `check_outliers` | 複数可 | 金額の外れ値（桁間違い等） |
| `check_yoy` | 複数必須 | 年度間の科目別合計の変動 |

## 構成

### CheckResult

全チェック関数は `CheckResult`（NamedTuple）を返す。

- `warnings: int` — 警告件数
- `skipped: bool` — データ不足等でスキップされたか（デフォルト `False`）
- `reason: str` — スキップ理由（デフォルト `""`）

### モジュール属性

各 `check_*.py` はモジュールレベルで以下を定義する。

- `MULTI_YEAR: bool` — 複数年度データを前提とするか（必須）
- `ENABLED: bool` — `False` でランナーの自動検出から除外（省略時 `True`）

### エラー処理

`common.read_csv()` はファイル不在時に `DataFileError` 例外を送出する。
`sys.exit()` は CLI エントリポイント（`main()`）に限定されているため、ランナーやプログラムからは例外として扱える。

### チェックの追加手順

1. `checks/check_<name>.py` を作成し、`MULTI_YEAR` を定義
2. `check_<name>(rows) -> CheckResult` を実装
3. `tests/checks/test_check_<name>.py` にテストを追加
4. ランナーが自動検出するため登録不要

開発中は `ENABLED = False` を設定するか、`check_` プレフィックスを付けないファイル名にする。
