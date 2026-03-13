import { describe, expect, test } from "vitest";
import {
  parseCSVRow,
  splitCSVLines,
  identifyType,
  extractYear,
  esc,
  isUTF8,
  uint8ToBase64,
  CSV_TYPES,
} from "./csv-utils.js";

// ---------------------------------------------------------------------------
// parseCSVRow
// ---------------------------------------------------------------------------
describe("parseCSVRow", () => {
  test("parses simple comma-separated values", () => {
    expect(parseCSVRow("a,b,c")).toEqual(["a", "b", "c"]);
  });

  test("returns null for empty string", () => {
    expect(parseCSVRow("")).toBeNull();
  });

  test("handles quoted fields", () => {
    expect(parseCSVRow('"hello","world"')).toEqual(["hello", "world"]);
  });

  test("handles escaped quotes inside quoted fields", () => {
    expect(parseCSVRow('"say ""hello""",b')).toEqual(['say "hello"', "b"]);
  });

  test("handles commas inside quoted fields", () => {
    expect(parseCSVRow('"a,b",c')).toEqual(["a,b", "c"]);
  });

  test("handles mixed quoted and unquoted fields", () => {
    expect(parseCSVRow('plain,"quoted",plain2')).toEqual([
      "plain",
      "quoted",
      "plain2",
    ]);
  });

  test("handles empty fields", () => {
    expect(parseCSVRow("a,,c")).toEqual(["a", "", "c"]);
  });

  test("handles single field", () => {
    expect(parseCSVRow("only")).toEqual(["only"]);
  });

  test("handles trailing comma", () => {
    expect(parseCSVRow("a,b,")).toEqual(["a", "b", ""]);
  });
});

// ---------------------------------------------------------------------------
// splitCSVLines
// ---------------------------------------------------------------------------
describe("splitCSVLines", () => {
  test("splits simple lines by LF", () => {
    expect(splitCSVLines("a,b\nc,d\n")).toEqual(["a,b", "c,d", ""]);
  });

  test("splits lines by CRLF", () => {
    expect(splitCSVLines("a,b\r\nc,d\r\n")).toEqual(["a,b", "c,d", ""]);
  });

  test("keeps newlines inside quoted fields", () => {
    expect(splitCSVLines('a,"line1\nline2",c\nd,e,f')).toEqual([
      'a,"line1\nline2",c',
      "d,e,f",
    ]);
  });

  test("handles escaped quotes inside quoted fields", () => {
    expect(splitCSVLines('"say ""hi"""\nnext')).toEqual([
      '"say ""hi"""',
      "next",
    ]);
  });

  test("handles empty input", () => {
    expect(splitCSVLines("")).toEqual([""]);
  });
});

// ---------------------------------------------------------------------------
// identifyType
// ---------------------------------------------------------------------------
describe("identifyType", () => {
  test("identifies 仕訳帳 by header columns", () => {
    const header = [
      "取引No",
      "取引日",
      "借方勘定科目",
      "貸方勘定科目",
      "借方金額(円)",
      "貸方金額(円)",
      "摘要",
    ];
    const result = identifyType(header, "export.csv");
    expect(result).not.toBeNull();
    expect(result!.saveName).toBe("仕訳帳.csv");
  });

  test("identifies 総勘定元帳 by header columns", () => {
    const header = ["取引日", "勘定科目", "相手勘定科目", "金額", "残高"];
    const result = identifyType(header, "export.csv");
    expect(result).not.toBeNull();
    expect(result!.saveName).toBe("総勘定元帳.csv");
  });

  test("prefers type with more matching columns", () => {
    // 仕訳帳 has 4 identifyColumns, 総勘定元帳 has 3
    // If both match, 仕訳帳 wins because it has a higher score
    const header = [
      "取引日",
      "借方勘定科目",
      "貸方勘定科目",
      "借方金額(円)",
      "貸方金額(円)",
      "勘定科目",
      "相手勘定科目",
      "残高",
    ];
    const result = identifyType(header, "export.csv");
    expect(result).not.toBeNull();
    expect(result!.saveName).toBe("仕訳帳.csv");
  });

  test("falls back to filename matching", () => {
    const header = ["col1", "col2"];
    const result = identifyType(header, "仕訳帳_2025.csv");
    expect(result).not.toBeNull();
    expect(result!.saveName).toBe("仕訳帳.csv");
  });

  test("returns null when no match", () => {
    expect(identifyType(["col1", "col2"], "unknown.csv")).toBeNull();
  });

  test("trims header values for matching", () => {
    const header = [" 勘定科目 ", " 相手勘定科目 ", " 残高 "];
    const result = identifyType(header, "x.csv");
    expect(result).not.toBeNull();
    expect(result!.saveName).toBe("総勘定元帳.csv");
  });
});

// ---------------------------------------------------------------------------
// extractYear
// ---------------------------------------------------------------------------
describe("extractYear", () => {
  test("extracts year from date column", () => {
    const header = ["取引日", "金額"];
    const lines = ["取引日,金額", "2025/01/15,1000", "2025/03/20,2000"];
    expect(extractYear(lines, header, "取引日")).toBe(2025);
  });

  test("returns null when date column not found", () => {
    const header = ["日付", "金額"];
    expect(extractYear(["日付,金額", "2025/01/01,100"], header, "取引日")).toBeNull();
  });

  test("returns null when no date values found", () => {
    const header = ["取引日", "金額"];
    expect(extractYear(["取引日,金額", ",100"], header, "取引日")).toBeNull();
  });

  test("returns null when multiple years are close in count", () => {
    const header = ["取引日"];
    const lines = [
      "取引日",
      "2024/12/01",
      "2024/12/15",
      "2025/01/01",
      "2025/01/15",
    ];
    expect(extractYear(lines, header, "取引日")).toBeNull();
  });

  test("returns dominant year when it vastly outnumbers others", () => {
    const header = ["取引日"];
    const lines = ["取引日"];
    // 20 rows of 2025, 1 row of 2024 → ratio > 10
    for (let i = 0; i < 20; i++) lines.push("2025/06/01");
    lines.push("2024/12/31");
    expect(extractYear(lines, header, "取引日")).toBe(2025);
  });

  test("skips empty lines", () => {
    const header = ["取引日"];
    const lines = ["取引日", "2025/01/01", "", "2025/02/01", ""];
    expect(extractYear(lines, header, "取引日")).toBe(2025);
  });
});

// ---------------------------------------------------------------------------
// esc
// ---------------------------------------------------------------------------
describe("esc", () => {
  test("escapes &, <, >", () => {
    expect(esc("a & b < c > d")).toBe("a &amp; b &lt; c &gt; d");
  });

  test("returns plain string unchanged", () => {
    expect(esc("hello")).toBe("hello");
  });
});

// ---------------------------------------------------------------------------
// isUTF8
// ---------------------------------------------------------------------------
describe("isUTF8", () => {
  test("returns true for valid UTF-8 bytes", () => {
    const bytes = new TextEncoder().encode("こんにちは");
    expect(isUTF8(bytes)).toBe(true);
  });

  test("returns true for ASCII bytes", () => {
    const bytes = new TextEncoder().encode("hello");
    expect(isUTF8(bytes)).toBe(true);
  });

  test("returns false for invalid UTF-8 bytes", () => {
    // 0x80 alone is not valid UTF-8
    const bytes = new Uint8Array([0x80, 0x81, 0x82]);
    expect(isUTF8(bytes)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// uint8ToBase64
// ---------------------------------------------------------------------------
describe("uint8ToBase64", () => {
  test("encodes bytes to base64", () => {
    const bytes = new TextEncoder().encode("hello");
    expect(uint8ToBase64(bytes)).toBe(btoa("hello"));
  });

  test("handles empty input", () => {
    expect(uint8ToBase64(new Uint8Array([]))).toBe("");
  });
});
