export interface ImportRequest {
  year: number;
  saveName: string;
  content: string;
  /** Base64-encoded original Shift-JIS bytes (omitted when file was already UTF-8) */
  rawBase64?: string;
}

export function countDataRows(csv: string): number {
  const lines = csv.split(/\r?\n/);
  // Exclude header and trailing empty lines
  return lines.filter((l, i) => i > 0 && l.trim() !== "").length;
}

export function isErrnoException(
  error: unknown,
): error is NodeJS.ErrnoException {
  return error instanceof Error;
}

export function staticFileErrorResponse(error: unknown): {
  status: 404 | 500;
  body: "Not Found" | "Internal Server Error";
} {
  if (isErrnoException(error) && error.code === "ENOENT") {
    return { status: 404, body: "Not Found" };
  }
  return { status: 500, body: "Internal Server Error" };
}

export function getStaticRequestPath(rawUrl: string | undefined): string {
  if (!rawUrl || rawUrl === "/") {
    return "/csv-importer.html";
  }
  return new URL(rawUrl, "http://localhost").pathname;
}
