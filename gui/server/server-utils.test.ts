import { describe, expect, test } from "vitest";
import { countDataRows, isErrnoException, staticFileErrorResponse } from "./server-utils.js";

describe("countDataRows", () => {
  test("counts data rows excluding header", () => {
    const csv = "header1,header2\nrow1a,row1b\nrow2a,row2b\n";
    expect(countDataRows(csv)).toBe(2);
  });

  test("ignores trailing empty lines", () => {
    const csv = "h1,h2\ndata1,data2\n\n\n";
    expect(countDataRows(csv)).toBe(1);
  });

  test("returns 0 for header-only CSV", () => {
    expect(countDataRows("h1,h2\n")).toBe(0);
  });

  test("returns 0 for header-only without trailing newline", () => {
    expect(countDataRows("h1,h2")).toBe(0);
  });

  test("handles CRLF line endings", () => {
    const csv = "h1,h2\r\nrow1,row2\r\nrow3,row4\r\n";
    expect(countDataRows(csv)).toBe(2);
  });

  test("handles single data row without trailing newline", () => {
    const csv = "h1,h2\ndata1,data2";
    expect(countDataRows(csv)).toBe(1);
  });
});

describe("isErrnoException", () => {
  test("returns true for Error instances", () => {
    expect(isErrnoException(new Error("boom"))).toBe(true);
  });

  test("returns false for non-Error values", () => {
    expect(isErrnoException("boom")).toBe(false);
  });
});

describe("staticFileErrorResponse", () => {
  test("returns 404 for ENOENT", () => {
    const error = Object.assign(new Error("missing"), { code: "ENOENT" });
    expect(staticFileErrorResponse(error)).toEqual({
      status: 404,
      body: "Not Found",
    });
  });

  test("returns 500 for non-ENOENT errors", () => {
    const error = Object.assign(new Error("forbidden"), { code: "EACCES" });
    expect(staticFileErrorResponse(error)).toEqual({
      status: 500,
      body: "Internal Server Error",
    });
  });

  test("returns 500 for non-Error values", () => {
    expect(staticFileErrorResponse("boom")).toEqual({
      status: 500,
      body: "Internal Server Error",
    });
  });
});
