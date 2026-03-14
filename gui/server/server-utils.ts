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
