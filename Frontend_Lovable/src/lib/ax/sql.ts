import type { Row } from "./types";

/**
 * Tiny read-only SQL engine that runs entirely in the browser against the
 * active dataset version. Supported grammar:
 *
 *   SELECT <cols | * | AGG(col) [AS alias]>
 *   FROM dataset
 *   [WHERE <cond> [AND|OR <cond>]...]
 *   [GROUP BY <col>]
 *   [ORDER BY <col> [ASC|DESC]]
 *   [LIMIT <n>]
 */

export interface SqlResult {
  columns: string[];
  rows: Row[];
  rowCount: number;
  ms: number;
  sql: string;
}

export class SqlError extends Error {}

const AGGS = ["count", "sum", "avg", "min", "max"] as const;
type Agg = (typeof AGGS)[number];

interface Cond {
  join: "AND" | "OR";
  col: string;
  op: string;
  value: string;
}

function stripQuotes(s: string) {
  const t = s.trim();
  if ((t.startsWith("'") && t.endsWith("'")) || (t.startsWith('"') && t.endsWith('"'))) return t.slice(1, -1);
  return t;
}

function section(sql: string, kw: RegExp): string | null {
  const m = sql.match(kw);
  return m ? m[1].trim() : null;
}

function parseConditions(text: string): Cond[] {
  const parts = text.split(/\s+(AND|OR)\s+/i);
  const conds: Cond[] = [];
  let join: "AND" | "OR" = "AND";
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i].trim();
    if (/^(AND|OR)$/i.test(p)) {
      join = p.toUpperCase() as "AND" | "OR";
      continue;
    }
    const m = p.match(/^(.+?)\s*(>=|<=|!=|<>|=|>|<|\bLIKE\b|\bIS NOT NULL\b|\bIS NULL\b)\s*(.*)$/i);
    if (!m) throw new SqlError(`Could not parse condition: "${p}"`);
    conds.push({ join, col: stripQuotes(m[1]), op: m[2].toUpperCase(), value: stripQuotes(m[3] ?? "") });
  }
  return conds;
}

function testCond(row: Row, c: Cond): boolean {
  const raw = row[c.col];
  if (c.op === "IS NULL") return raw === null || raw === "";
  if (c.op === "IS NOT NULL") return !(raw === null || raw === "");
  if (c.op === "LIKE") {
    const pattern = new RegExp(`^${c.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/%/g, ".*")}$`, "i");
    return pattern.test(String(raw ?? ""));
  }
  const numeric = Number(raw);
  const target = Number(c.value);
  const bothNumeric = !Number.isNaN(numeric) && !Number.isNaN(target) && raw !== null && raw !== "";
  const a = bothNumeric ? numeric : String(raw ?? "").toLowerCase();
  const b = bothNumeric ? target : c.value.toLowerCase();
  switch (c.op) {
    case "=":
      return a === b;
    case "!=":
    case "<>":
      return a !== b;
    case ">":
      return a > b;
    case "<":
      return a < b;
    case ">=":
      return a >= b;
    case "<=":
      return a <= b;
    default:
      return false;
  }
}

interface SelectItem {
  agg: Agg | null;
  col: string;
  alias: string;
}

function parseSelect(text: string, columns: string[]): SelectItem[] {
  if (text.trim() === "*") return columns.map((c) => ({ agg: null, col: c, alias: c }));
  return text.split(",").map((partRaw) => {
    const part = partRaw.trim();
    const aliasMatch = part.match(/^(.*?)\s+AS\s+([A-Za-z_][\w]*)$/i);
    const expr = (aliasMatch ? aliasMatch[1] : part).trim();
    const aggMatch = expr.match(/^(count|sum|avg|min|max)\s*\(\s*(\*|[^)]+?)\s*\)$/i);
    if (aggMatch) {
      const agg = aggMatch[1].toLowerCase() as Agg;
      const col = stripQuotes(aggMatch[2]);
      return { agg, col, alias: aliasMatch ? aliasMatch[2] : `${agg}(${col})` };
    }
    const col = stripQuotes(expr);
    return { agg: null, col, alias: aliasMatch ? aliasMatch[2] : col };
  });
}

function applyAgg(agg: Agg, values: (string | number | null)[]): number {
  if (agg === "count") return values.filter((v) => v !== null && v !== "").length;
  const n = values.map(Number).filter((v) => !Number.isNaN(v));
  if (!n.length) return 0;
  switch (agg) {
    case "sum":
      return n.reduce((a, b) => a + b, 0);
    case "avg":
      return n.reduce((a, b) => a + b, 0) / n.length;
    case "min":
      return Math.min(...n);
    case "max":
      return Math.max(...n);
  }
}

const round = (n: number) => Math.round(n * 10000) / 10000;

export function runSql(sqlInput: string, rows: Row[], columns: string[]): SqlResult {
  const started = performance.now();
  const sql = sqlInput.trim().replace(/;\s*$/, "").replace(/\s+/g, " ");
  if (!/^select\s/i.test(sql)) throw new SqlError("Only SELECT statements are supported.");

  const selectText = section(sql, /select\s+(.*?)\s+from\s/i);
  if (!selectText) throw new SqlError("Missing FROM clause. Query the table named `dataset`.");
  const whereText = section(sql, /\swhere\s+(.*?)(?:\s+group by\s|\s+order by\s|\s+limit\s|$)/i);
  const groupText = section(sql, /\sgroup by\s+(.*?)(?:\s+order by\s|\s+limit\s|$)/i);
  const orderText = section(sql, /\sorder by\s+(.*?)(?:\s+limit\s|$)/i);
  const limitText = section(sql, /\slimit\s+(\d+)\s*$/i);

  const items = parseSelect(selectText, columns);
  for (const it of items) {
    if (it.col !== "*" && !columns.includes(it.col)) {
      throw new SqlError(`Unknown column "${it.col}". Available: ${columns.join(", ")}`);
    }
  }

  let working = rows;
  if (whereText) {
    const conds = parseConditions(whereText);
    for (const c of conds) {
      if (!columns.includes(c.col)) throw new SqlError(`Unknown column "${c.col}" in WHERE.`);
    }
    working = rows.filter((r) =>
      conds.reduce<boolean>((acc, c, i) => {
        const t = testCond(r, c);
        if (i === 0) return t;
        return c.join === "AND" ? acc && t : acc || t;
      }, true),
    );
  }

  let out: Row[];
  const hasAgg = items.some((i) => i.agg);

  if (groupText) {
    const groupCols = groupText.split(",").map((g) => stripQuotes(g));
    for (const g of groupCols) if (!columns.includes(g)) throw new SqlError(`Unknown GROUP BY column "${g}".`);
    const buckets = new Map<string, Row[]>();
    for (const r of working) {
      const key = groupCols.map((g) => String(r[g] ?? "(blank)")).join("\u0001");
      const list = buckets.get(key) ?? [];
      list.push(r);
      buckets.set(key, list);
    }
    out = [...buckets.entries()].map(([key, group]) => {
      const rec: Row = {};
      key.split("\u0001").forEach((v, i) => {
        rec[groupCols[i]] = v;
      });
      for (const it of items) {
        if (it.agg) rec[it.alias] = round(applyAgg(it.agg, group.map((g) => g[it.col])));
        else if (!groupCols.includes(it.col)) rec[it.alias] = group[0][it.col];
      }
      return rec;
    });
  } else if (hasAgg) {
    const rec: Row = {};
    for (const it of items) {
      rec[it.alias] = it.agg ? round(applyAgg(it.agg, working.map((g) => g[it.col]))) : working[0]?.[it.col] ?? null;
    }
    out = [rec];
  } else {
    out = working.map((r) => {
      const rec: Row = {};
      for (const it of items) rec[it.alias] = r[it.col] ?? null;
      return rec;
    });
  }

  if (orderText) {
    const m = orderText.match(/^(.*?)(?:\s+(asc|desc))?$/i);
    const col = stripQuotes(m?.[1] ?? "");
    const dir = (m?.[2] ?? "asc").toLowerCase() === "desc" ? -1 : 1;
    out = [...out].sort((a, b) => {
      const av = a[col];
      const bv = b[col];
      const an = Number(av);
      const bn = Number(bv);
      if (!Number.isNaN(an) && !Number.isNaN(bn) && av !== null && bv !== null) return (an - bn) * dir;
      return String(av ?? "").localeCompare(String(bv ?? "")) * dir;
    });
  }

  const total = out.length;
  if (limitText) out = out.slice(0, Number(limitText));

  const resultColumns = out.length ? Object.keys(out[0]) : items.map((i) => i.alias);
  return { columns: resultColumns, rows: out, rowCount: total, ms: performance.now() - started, sql };
}

export const SQL_TEMPLATES: { title: string; description: string; build: (cols: string[], numeric: string[], categorical: string[]) => string }[] = [
  {
    title: "Preview rows",
    description: "First 25 records of the active version",
    build: () => "SELECT * FROM dataset LIMIT 25;",
  },
  {
    title: "Count rows",
    description: "Total record count",
    build: (cols) => `SELECT COUNT(${cols[0]}) AS total_rows FROM dataset;`,
  },
  {
    title: "Group totals",
    description: "Aggregate a numeric column by a category",
    build: (_c, numeric, categorical) =>
      `SELECT ${categorical[0] ?? "category"}, SUM(${numeric[0] ?? "value"}) AS total\nFROM dataset\nGROUP BY ${categorical[0] ?? "category"}\nORDER BY total DESC\nLIMIT 20;`,
  },
  {
    title: "Averages by group",
    description: "Mean of a numeric column per category",
    build: (_c, numeric, categorical) =>
      `SELECT ${categorical[0] ?? "category"}, AVG(${numeric[0] ?? "value"}) AS average, COUNT(${numeric[0] ?? "value"}) AS records\nFROM dataset\nGROUP BY ${categorical[0] ?? "category"}\nORDER BY average DESC;`,
  },
  {
    title: "Top records",
    description: "Highest values on a numeric column",
    build: (_c, numeric) =>
      `SELECT * FROM dataset\nORDER BY ${numeric[0] ?? "value"} DESC\nLIMIT 10;`,
  },
  {
    title: "Find missing values",
    description: "Rows where a column is empty",
    build: (cols) => `SELECT * FROM dataset\nWHERE ${cols[0]} IS NULL\nLIMIT 25;`,
  },
];
