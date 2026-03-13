import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import { text } from "node:stream/consumers";
import { countDataRows } from "./server-utils.js";
import type { ImportRequest } from "./server-utils.js";

const PORT = 3456;
// dist/server.js → gui/dist/, so ../.. = repo root
const REPO_ROOT = path.resolve(import.meta.dirname, "../..");
const DATA_DIR = path.join(REPO_ROOT, "data");
const GUI_DIR = path.join(REPO_ROOT, "gui");

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
};

const MAX_BODY = 10 * 1024 * 1024; // 10 MB

const server = http.createServer(async (req, res) => {
  // POST /import — save a CSV file
  if (req.method === "POST" && req.url === "/import") {
    // CSRF protection: reject requests without application/json Content-Type
    // (browsers send CORS preflight for non-simple Content-Types)
    const ct = req.headers["content-type"] ?? "";
    if (!ct.includes("application/json")) {
      res.writeHead(415);
      res.end("Unsupported Media Type");
      return;
    }
    // Guard against oversized requests
    const contentLength = parseInt(req.headers["content-length"] ?? "0", 10);
    if (contentLength > MAX_BODY) {
      res.writeHead(413);
      res.end("Payload Too Large");
      return;
    }
    return handleImport(req, res);
  }

  // GET — serve static files from gui/
  if (req.method === "GET") {
    const urlPath = req.url === "/" ? "/csv-importer.html" : req.url!;
    const filePath = path.resolve(GUI_DIR, urlPath.slice(1));

    // Prevent directory traversal
    if (!filePath.startsWith(GUI_DIR + path.sep) && filePath !== GUI_DIR) {
      res.writeHead(403);
      res.end("Forbidden");
      return;
    }

    try {
      // Resolve symlinks and re-check
      const realPath = await fs.realpath(filePath);
      const realGUI = await fs.realpath(GUI_DIR);
      if (!realPath.startsWith(realGUI + path.sep) && realPath !== realGUI) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }
      const data = await fs.readFile(realPath);
      const ext = path.extname(filePath);
      res.writeHead(200, { "Content-Type": MIME[ext] ?? "application/octet-stream" });
      res.end(data);
    } catch {
      res.writeHead(404);
      res.end("Not Found");
    }
    return;
  }

  res.writeHead(405);
  res.end("Method Not Allowed");
});

async function handleImport(
  req: http.IncomingMessage,
  res: http.ServerResponse,
): Promise<void> {
  const body = await text(req);
  let payload: ImportRequest;
  try {
    payload = JSON.parse(body);
  } catch {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Invalid JSON" }));
    return;
  }

  const { year, saveName, content, rawBase64 } = payload;

  // Validate
  if (!year || !saveName || !content) {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Missing year, saveName, or content" }));
    return;
  }

  // Prevent path traversal — resolve and verify under DATA_DIR
  const yearDir = path.resolve(DATA_DIR, String(year));
  const filePath = path.resolve(yearDir, saveName);
  if (!filePath.startsWith(yearDir + path.sep) || !yearDir.startsWith(DATA_DIR + path.sep)) {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Invalid year or saveName" }));
    return;
  }

  try {
    // Count rows in existing file (if any) before overwriting
    let prevRows: number | null = null;
    try {
      const existing = await fs.readFile(filePath, "utf-8");
      prevRows = countDataRows(existing);
    } catch {
      // file doesn't exist yet
    }

    await fs.mkdir(yearDir, { recursive: true });
    await fs.writeFile(filePath, content, "utf-8");

    // Save original Shift-JIS file alongside UTF-8 version
    if (rawBase64) {
      const sjisName = saveName.replace(/\.csv$/, "_sjis.csv");
      const sjisPath = path.join(yearDir, sjisName);
      await fs.writeFile(sjisPath, Buffer.from(rawBase64, "base64"));
      console.log(`saved: ${path.relative(REPO_ROOT, sjisPath)} (Shift-JIS original)`);
    }

    const relPath = path.relative(REPO_ROOT, filePath);
    const newRows = countDataRows(content);
    console.log(`saved: ${relPath} (${newRows} rows)`);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true, path: relPath, newRows, prevRows }));
  } catch (e: unknown) {
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) }));
  }
}

server.listen(PORT, "127.0.0.1", () => {
  console.log(`CSV import server running at http://localhost:${PORT}`);
  console.log(`data/ → ${DATA_DIR}`);
});
