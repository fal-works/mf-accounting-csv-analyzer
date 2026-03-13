#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: convert_encoding.sh [--to-sjis] <file_or_dir> [...]

CSV ファイルのエンコーディングを変換する。

  デフォルト: Shift-JIS → UTF-8 (ファイル名そのまま)
  --to-sjis:  UTF-8 → Shift-JIS (ファイル名に _sjis を付与)

例:
  ./convert_encoding.sh data/2025/                  # フォルダ内の全CSVをUTF-8に
  ./convert_encoding.sh data/2025/仕訳帳_*.csv      # 特定ファイルをUTF-8に
  ./convert_encoding.sh --to-sjis data/2025/仕訳帳.csv  # Shift-JISに変換(_sjis付与)
EOF
  exit 1
}

[[ $# -eq 0 ]] && usage

to_sjis=false
if [[ "$1" == "--to-sjis" ]]; then
  to_sjis=true
  shift
fi

[[ $# -eq 0 ]] && usage

# 対象ファイルを収集
files=()
for arg in "$@"; do
  if [[ -d "$arg" ]]; then
    while IFS= read -r -d '' f; do
      files+=("$f")
    done < <(find "$arg" -maxdepth 1 -name '*.csv' -print0)
  elif [[ -f "$arg" ]]; then
    files+=("$arg")
  else
    echo "スキップ (見つからない): $arg" >&2
  fi
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "対象のCSVファイルがありません。" >&2
  exit 1
fi

for src in "${files[@]}"; do
  if $to_sjis; then
    # UTF-8 → Shift-JIS: _sjis サフィックスを付けて出力
    base="${src%.csv}"
    # 既に _sjis が付いていれば二重付与しない
    if [[ "$base" == *_sjis ]]; then
      dst="$src"
    else
      dst="${base}_sjis.csv"
    fi
    iconv -f UTF-8 -t SHIFT_JIS "$src" > "$dst.tmp"
    mv "$dst.tmp" "$dst"
    echo "$src → $dst (Shift-JIS)"
  else
    # Shift-JIS → UTF-8: そのまま上書き
    iconv -f SHIFT_JIS -t UTF-8 "$src" > "$src.tmp"
    mv "$src.tmp" "$src"
    echo "$src → UTF-8"
  fi
done
