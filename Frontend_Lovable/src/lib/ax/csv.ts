import type { Row } from "./types";

export const MAX_ROWS = 5000;

function splitLine(line: string, delim: string): string[] {
  const out: string[] = [];
  let cur = "";
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (quoted) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"';
          i++;
        } else quoted = false;
      } else cur += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === delim) {
      out.push(cur);
      cur = "";
    } else cur += ch;
  }
  out.push(cur);
  return out.map((c) => c.trim());
}

function detectDelimiter(header: string): string {
  const candidates = [",", ";", "\t", "|"];
  let best = ",";
  let bestCount = 0;
  for (const c of candidates) {
    const n = header.split(c).length;
    if (n > bestCount) {
      bestCount = n;
      best = c;
    }
  }
  return best;
}

const NUM_RE = /^-?\$?\s?-?[\d,]*\.?\d+%?$/;

export function coerce(value: string): string | number | null {
  const v = value.trim();
  if (v === "" || v.toLowerCase() === "null" || v.toLowerCase() === "na" || v === "-") return null;
  if (NUM_RE.test(v)) {
    const n = Number(v.replace(/[$,%\s]/g, ""));
    if (!Number.isNaN(n)) return v.endsWith("%") ? n : n;
  }
  return v;
}

export function parseDelimited(text: string): { columns: string[]; rows: Row[] } {
  const lines = text.replace(/\r\n/g, "\n").split("\n").filter((l) => l.trim() !== "");
  if (lines.length === 0) return { columns: [], rows: [] };
  const delim = detectDelimiter(lines[0]);
  const columns = splitLine(lines[0], delim).map((c, i) => c.replace(/^"|"$/g, "") || `column_${i + 1}`);
  const rows: Row[] = [];
  for (let i = 1; i < lines.length && rows.length < MAX_ROWS; i++) {
    const cells = splitLine(lines[i], delim);
    const row: Row = {};
    columns.forEach((c, idx) => {
      row[c] = coerce(cells[idx] ?? "");
    });
    rows.push(row);
  }
  return { columns, rows };
}
