import { describe, expect, test } from "vitest";
import {
  parseCSVRow,
  splitCSVLines,
  identifyType,
  findMissingRequiredColumns,
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
  test("identifies 仕訳帳 when all formal columns are present", () => {
    const header = CSV_TYPES[0].columns;
    const result = identifyType(header);
    expect(result).not.toBeNull();
    expect(result!.saveName).toBe("仕訳帳.csv");
  });

  test("returns null when formal columns are missing", () => {
    const header = CSV_TYPES[0].columns.filter((column) => column !== "メモ");
    expect(identifyType(header)).toBeNull();
  });

  test("returns null when no match", () => {
    expect(identifyType(["col1", "col2"])).toBeNull();
  });

  test("trims header values for matching", () => {
    const header = CSV_TYPES[0].columns.map((column) => ` ${column} `);
    const result = identifyType(header);
    expect(result).not.toBeNull();
    expect(result!.saveName).toBe("仕訳帳.csv");
  });
});

// ---------------------------------------------------------------------------
// findMissingRequiredColumns
// ---------------------------------------------------------------------------
describe("findMissingRequiredColumns", () => {
  test("returns no missing columns when all required columns exist", () => {
    const columns = CSV_TYPES[0].columns;
    expect(findMissingRequiredColumns(columns, columns)).toEqual([]);
  });

  test("returns missing columns in definition order", () => {
    const columns = CSV_TYPES[0].columns;
    const header = columns.filter(
      (column) => column !== "借方補助科目" && column !== "メモ",
    );
    expect(findMissingRequiredColumns(header, columns)).toEqual([
      "借方補助科目",
      "メモ",
    ]);
  });

  test("trims header values before checking required columns", () => {
    const columns = CSV_TYPES[0].columns;
    const header = columns.map((column) => ` ${column} `);
    expect(findMissingRequiredColumns(header, columns)).toEqual([]);
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
