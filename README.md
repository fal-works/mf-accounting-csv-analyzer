# mf-accounting-csv-analyzer

会計ソフト（マネーフォワード クラウド確定申告）からエクスポートした会計データを分析・検査します。

独立したツールではなく、このプロジェクトフォルダー内で完結する運用を想定しています。

## 必要環境

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22+
- pnpm
- 最新のWebブラウザ（GUI用）

## セットアップ

```bash
uv sync        # Python 仮想環境の作成と依存パッケージのインストール
pnpm install   # Node.js 依存パッケージのインストール
```

## CSV インポート

```bash
pnpm start
```

ブラウザーで <http://localhost:3456> を開き、会計ソフトからエクスポートしたCSVをドラッグ＆ドロップします。

- Shift-JIS は自動で UTF-8 に変換
- ファイルタイプ（仕訳帳）はヘッダーから自動判定
- 年度は取引日から自動判定
- `data/{年度}/` に保存（`data/` は `.gitignore` 済み）

## 分析

基本はAI任せですが、以下のコマンドを手動で実行することもできます。

```bash
uv run summary --target 2025 --pretty  # サマリー（全体像の把握）
uv run check --target 2025  # チェック（計上ミスの検出）
uv run filter-journal --target 2025 [条件] --pretty  # 仕訳の絞り込み検索
```

各コマンドの詳細は `--help` を参照してください。
