// ---------------------------------------------------------------------------
// CSV Type Definitions
// ---------------------------------------------------------------------------
// Each entry defines a CSV type: its formal columns and the filename to save as.
// To add a new type, just add an entry here.

export interface CsvTypeDef {
  saveName: string;
  /** Formal columns expected for this CSV type */
  columns: string[];
  /** Column that contains dates in YYYY/MM/DD format */
  dateColumn: string;
}

export const CSV_TYPES: CsvTypeDef[] = [
  {
    saveName: "仕訳帳.csv",
    columns: [
      "取引No",
      "取引日",
      "借方勘定科目",
      "借方補助科目",
      "借方取引先",
      "借方税区分",
      "借方金額(円)",
      "貸方勘定科目",
      "貸方補助科目",
      "貸方取引先",
      "貸方税区分",
      "貸方金額(円)",
      "摘要",
      "メモ",
    ],
    dateColumn: "取引日",
  },
];

// ---------------------------------------------------------------------------
// HTML escaping
// ---------------------------------------------------------------------------
export function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ---------------------------------------------------------------------------
// Base64 encoding
// ---------------------------------------------------------------------------
export function uint8ToBase64(bytes: Uint8Array): string {
  const binary = Array.from(bytes, (b) => String.fromCharCode(b)).join("");
  return btoa(binary);
}

// ---------------------------------------------------------------------------
// Encoding detection
// ---------------------------------------------------------------------------
export function isUTF8(bytes: Uint8Array): boolean {
  try {
    new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    return true;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// CSV type identification
// ---------------------------------------------------------------------------
export function identifyType(header: string[]): CsvTypeDef | null {
  const headerSet = new Set(header.map((h) => h.trim()));

  for (const t of CSV_TYPES) {
    const matchesAllColumns = t.columns.every((column) => headerSet.has(column));
    if (matchesAllColumns) return t;
  }
  return null;
}

export function findMissingRequiredColumns(
  header: string[],
  columns: string[],
): string[] {
  const headerSet = new Set(header.map((h) => h.trim()));
  return columns.filter((column) => !headerSet.has(column));
}

// ---------------------------------------------------------------------------
// Year extraction
// ---------------------------------------------------------------------------
export function extractYear(
  lines: string[],
  header: string[],
  dateColumn: string,
): number | null {
  const colIdx = header.findIndex((h) => h.trim() === dateColumn);
  if (colIdx < 0) return null;

  const counts: Record<string, number> = {};
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    const row = parseCSVRow(lines[i]);
    if (!row || colIdx >= row.length) continue;
    const m = row[colIdx].match(/^(\d{4})\//);
    if (m) counts[m[1]] = (counts[m[1]] || 0) + 1;
  }

  const entries = Object.entries(counts);
  if (entries.length === 0) return null;
  if (entries.length === 1) return Number(entries[0][0]);

  // Multiple years — use the dominant one only if it vastly outnumbers others
  entries.sort((a, b) => b[1] - a[1]);
  if (entries[0][1] > entries[1][1] * 10) {
    return Number(entries[0][0]);
  }
  return null;
}

// ---------------------------------------------------------------------------
// CSV line splitter (respects quoted fields containing newlines)
// ---------------------------------------------------------------------------
export function splitCSVLines(text: string): string[] {
  const lines: string[] = [];
  let start = 0;
  let inQuote = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuote) {
      if (ch === '"') {
        if (i + 1 < text.length && text[i + 1] === '"') {
          i++; // skip escaped quote
        } else {
          inQuote = false;
        }
      }
    } else if (ch === '"') {
      inQuote = true;
    } else if (ch === '\n') {
      const end = i > 0 && text[i - 1] === '\r' ? i - 1 : i;
      lines.push(text.slice(start, end));
      start = i + 1;
    }
  }
  if (start <= text.length) {
    lines.push(text.slice(start));
  }
  return lines;
}

// ---------------------------------------------------------------------------
// Minimal CSV row parser (handles quoted fields)
// ---------------------------------------------------------------------------
export function parseCSVRow(line: string): string[] | null {
  if (!line) return null;
  const fields: string[] = [];
  let i = 0;
  while (i <= line.length) {
    if (i === line.length) {
      fields.push("");
      break;
    }
    if (line[i] === '"') {
      let val = "";
      i++;
      while (i < line.length) {
        if (line[i] === '"') {
          if (i + 1 < line.length && line[i + 1] === '"') {
            val += '"';
            i += 2;
          } else {
            i++;
            break;
          }
        } else {
          val += line[i++];
        }
      }
      fields.push(val);
      if (i >= line.length) break;
      if (line[i] === ",") i++;
    } else {
      const next = line.indexOf(",", i);
      if (next < 0) {
        fields.push(line.slice(i));
        break;
      }
      fields.push(line.slice(i, next));
      i = next + 1;
    }
  }
  return fields;
}
