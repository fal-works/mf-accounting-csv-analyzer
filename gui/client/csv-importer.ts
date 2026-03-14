import {
  CSV_TYPES,
  esc,
  isUTF8,
  uint8ToBase64,
  identifyType,
  findMissingRequiredColumns,
  extractYear,
  parseCSVRow,
  splitCSVLines,
} from "./csv-utils.js";

// ---------------------------------------------------------------------------
// DOM elements
// ---------------------------------------------------------------------------
const dropZone = document.getElementById("drop-zone") as HTMLDivElement;
const logEl = document.getElementById("log") as HTMLDivElement;

// ---------------------------------------------------------------------------
// Populate the type definitions table
// ---------------------------------------------------------------------------
{
  const tbody = document.getElementById("type-defs-body") as HTMLTableSectionElement;
  for (const t of CSV_TYPES) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${esc(t.saveName)}</td><td>${esc(t.columns.join(", "))}</td>`;
    tbody.appendChild(tr);
  }
}

// ---------------------------------------------------------------------------
// Drag & drop / file input
// ---------------------------------------------------------------------------
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("active");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("active"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("active");
  if (e.dataTransfer) handleFiles(e.dataTransfer.files);
});

dropZone.querySelector<HTMLInputElement>("input[type='file']")!
  .addEventListener("change", (e) => {
    const input = e.target as HTMLInputElement;
    if (input.files) handleFiles(input.files);
    input.value = "";
  });

async function handleFiles(fileList: FileList): Promise<void> {
  for (const file of fileList) {
    await processFile(file);
  }
}

// ---------------------------------------------------------------------------
// Core processing
// ---------------------------------------------------------------------------
async function processFile(file: File): Promise<void> {
  log("info", `--- ${file.name} ---`);

  // 1. Read raw bytes
  const buf = await file.arrayBuffer();
  const bytes = new Uint8Array(buf);

  // 2. Detect encoding and decode to string
  let text: string;
  let rawBase64: string | undefined;
  if (isUTF8(bytes)) {
    text = new TextDecoder("utf-8").decode(bytes);
    log("info", "エンコーディング: UTF-8");
  } else {
    text = new TextDecoder("shift_jis").decode(bytes);
    // Keep original Shift-JIS bytes for archival
    rawBase64 = uint8ToBase64(bytes);
    log("info", "エンコーディング: Shift-JIS → UTF-8 に変換");
  }

  // Strip BOM if present
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);

  // 3. Parse header row
  const lines = splitCSVLines(text);
  const header = parseCSVRow(lines[0]);
  if (!header || header.length === 0) {
    log("err", "ヘッダー行を解析できません\n");
    return;
  }

  // 4. Identify CSV type
  const csvType = identifyType(header);
  if (!csvType) {
    log("err", `CSVタイプを判定できません。ヘッダー: ${header.slice(0, 5).join(", ")}...\n`);
    return;
  }
  log("info", `タイプ: ${csvType.saveName}`);

  const missingColumns = findMissingRequiredColumns(header, csvType.columns);
  if (missingColumns.length > 0) {
    log("err", `必須カラムが不足しています: ${missingColumns.join(", ")}\n`);
    return;
  }

  // 5. Extract year from dates
  const year = extractYear(lines, header, csvType.dateColumn);
  if (!year) {
    log("err", `年度を推定できません（${csvType.dateColumn} カラムから日付を取得できませんでした）\n`);
    return;
  }
  log("info", `年度: ${year}`);

  // 6. Save via server
  try {
    const res = await fetch("/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ year, saveName: csvType.saveName, content: text, rawBase64 }),
    });
    const result: {
      ok?: boolean; path?: string; error?: string;
      newRows?: number; prevRows?: number | null;
    } = await res.json();
    if (result.ok) {
      let msg = `保存完了: ${result.path} (${result.newRows} 件)`;
      if (result.prevRows != null) {
        msg += ` ← 旧 ${result.prevRows} 件`;
      }
      log("ok", msg + "\n");
    } else {
      log("err", `保存失敗: ${result.error}\n`);
    }
  } catch (e: unknown) {
    log("err", `通信エラー: ${e instanceof Error ? e.message : String(e)}\n`);
  }
}

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------
type LogLevel = "ok" | "err" | "info";

function log(level: LogLevel, msg: string): void {
  const span = document.createElement("span");
  span.className = "log-" + level;
  span.textContent = msg + "\n";
  logEl.appendChild(span);
  logEl.scrollTop = logEl.scrollHeight;
}
