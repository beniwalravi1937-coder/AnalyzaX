import type {
  Agg,
  ColKind,
  ColumnProfile,
  DatasetProfile,
  Recommendation,
  Row,
  TransformStep,
} from "./types";

const DATE_RE = /^\d{4}-\d{2}-\d{2}([ T].*)?$|^\d{1,2}\/\d{1,2}\/\d{2,4}$/;

export function inferKind(name: string, values: Array<string | number | null>): ColKind {
  const present = values.filter((v) => v !== null && v !== "");
  if (present.length === 0) return "categorical";
  const nums = present.filter((v) => typeof v === "number").length;
  if (nums / present.length > 0.8) return "numeric";
  const strs = present.map(String);
  const dates = strs.filter((s) => DATE_RE.test(s)).length;
  if (dates / strs.length > 0.8) return "temporal";
  const bools = strs.filter((s) => /^(true|false|yes|no|y|n)$/i.test(s)).length;
  if (bools / strs.length > 0.9) return "boolean";
  return "categorical";
}

function quantile(sorted: number[], q: number): number {
  if (sorted.length === 0) return 0;
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  const next = sorted[base + 1] ?? sorted[base];
  return sorted[base] + rest * (next - sorted[base]);
}

export function profileColumn(name: string, rows: Row[]): ColumnProfile {
  const values = rows.map((r) => r[name] ?? null);
  const kind = inferKind(name, values);
  const present = values.filter((v) => v !== null && v !== "");
  const missing = rows.length - present.length;
  const uniqueSet = new Set(present.map(String));
  const p: ColumnProfile = {
    name,
    kind,
    missing,
    missingPct: rows.length ? (missing / rows.length) * 100 : 0,
    unique: uniqueSet.size,
  };

  if (kind === "numeric") {
    const nums = present.map(Number).filter((n) => !Number.isNaN(n)).sort((a, b) => a - b);
    if (nums.length) {
      const mean = nums.reduce((a, b) => a + b, 0) / nums.length;
      const variance = nums.reduce((a, b) => a + (b - mean) ** 2, 0) / nums.length;
      const q1 = quantile(nums, 0.25);
      const q3 = quantile(nums, 0.75);
      const iqr = q3 - q1;
      p.min = nums[0];
      p.max = nums[nums.length - 1];
      p.mean = mean;
      p.median = quantile(nums, 0.5);
      p.std = Math.sqrt(variance);
      p.outliers = nums.filter((n) => n < q1 - 1.5 * iqr || n > q3 + 1.5 * iqr).length;
    }
  } else {
    const counts = new Map<string, number>();
    present.forEach((v) => {
      const k = String(v);
      counts.set(k, (counts.get(k) ?? 0) + 1);
    });
    p.top = [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([value, count]) => ({ value, count }));
  }
  return p;
}

export function countDuplicates(rows: Row[], columns: string[]): number {
  const seen = new Set<string>();
  let dupes = 0;
  for (const r of rows) {
    const key = columns.map((c) => String(r[c] ?? "")).join("\u0001");
    if (seen.has(key)) dupes++;
    else seen.add(key);
  }
  return dupes;
}

export function profileDataset(columns: string[], rows: Row[]): DatasetProfile {
  const cols = columns.map((c) => profileColumn(c, rows));
  const missingCells = cols.reduce((a, c) => a + c.missing, 0);
  const duplicateRows = countDuplicates(rows, columns);
  const totalCells = Math.max(1, rows.length * columns.length);
  const missingPenalty = (missingCells / totalCells) * 45;
  const dupePenalty = rows.length ? (duplicateRows / rows.length) * 25 : 0;
  const outliers = cols.reduce((a, c) => a + (c.outliers ?? 0), 0);
  const outlierPenalty = rows.length ? Math.min(15, (outliers / rows.length) * 30) : 0;
  const constantCols = cols.filter((c) => c.unique <= 1).length;
  const constantPenalty = Math.min(15, constantCols * 5);
  const score = Math.max(
    0,
    Math.round(100 - missingPenalty - dupePenalty - outlierPenalty - constantPenalty),
  );
  const issues =
    cols.filter((c) => c.missingPct > 0).length +
    (duplicateRows > 0 ? 1 : 0) +
    cols.filter((c) => (c.outliers ?? 0) > 0).length +
    constantCols;

  return {
    rowCount: rows.length,
    colCount: columns.length,
    missingCells,
    duplicateRows,
    qualityScore: score,
    issues,
    columns: cols,
  };
}

/* ------------------------------- cleaning -------------------------------- */

let counter = 0;
export const uid = (prefix = "id") => `${prefix}_${Date.now().toString(36)}_${(counter++).toString(36)}`;

export function recommend(profile: DatasetProfile): Recommendation[] {
  const recs: Recommendation[] = [];
  if (profile.duplicateRows > 0) {
    recs.push({
      id: uid("rec"),
      kind: "drop_duplicates",
      label: "Remove duplicate rows",
      detail: `${profile.duplicateRows} exact duplicate rows`,
      severity: "high",
      reason: "Duplicated records inflate counts and skew every aggregate.",
    });
  }
  for (const c of profile.columns) {
    if (c.missingPct >= 60) {
      recs.push({
        id: uid("rec"),
        kind: "drop_column",
        column: c.name,
        label: `Drop "${c.name}"`,
        detail: `${c.missingPct.toFixed(1)}% missing`,
        severity: "high",
        reason: "Too sparse to model or chart reliably.",
      });
    } else if (c.missingPct > 0) {
      recs.push({
        id: uid("rec"),
        kind: c.kind === "numeric" ? "impute_median" : "impute_mode",
        column: c.name,
        label: `Fill gaps in "${c.name}"`,
        detail:
          c.kind === "numeric"
            ? `${c.missing} missing → median ${(c.median ?? 0).toLocaleString()}`
            : `${c.missing} missing → most common value`,
        severity: c.missingPct > 20 ? "medium" : "low",
        reason: "Missing values break aggregations and chart continuity.",
      });
    }
    if (c.unique <= 1 && profile.rowCount > 1) {
      recs.push({
        id: uid("rec"),
        kind: "drop_column",
        column: c.name,
        label: `Drop constant column "${c.name}"`,
        detail: "Single distinct value",
        severity: "medium",
        reason: "A constant column carries no analytical signal.",
      });
    }
    if ((c.outliers ?? 0) > 0) {
      recs.push({
        id: uid("rec"),
        kind: "clip_outliers",
        column: c.name,
        label: `Clip outliers in "${c.name}"`,
        detail: `${c.outliers} values outside 1.5×IQR`,
        severity: "low",
        reason: "Extreme values dominate means and axis scales.",
      });
    }
  }
  return recs;
}

export function applySteps(
  columns: string[],
  rows: Row[],
  steps: TransformStep[],
): { columns: string[]; rows: Row[] } {
  let cols = [...columns];
  let out = rows.map((r) => ({ ...r }));

  for (const step of steps) {
    const col = step.column;
    switch (step.kind) {
      case "drop_column":
        if (col) {
          cols = cols.filter((c) => c !== col);
          out = out.map((r) => {
            const { [col]: _drop, ...rest } = r;
            return rest as Row;
          });
        }
        break;
      case "drop_duplicates": {
        const seen = new Set<string>();
        out = out.filter((r) => {
          const key = cols.map((c) => String(r[c] ?? "")).join("\u0001");
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
        break;
      }
      case "drop_missing_rows":
        out = out.filter((r) => cols.every((c) => r[c] !== null && r[c] !== ""));
        break;
      case "impute_median": {
        if (!col) break;
        const p = profileColumn(col, out);
        const fill = p.median ?? 0;
        out = out.map((r) => (r[col] === null || r[col] === "" ? { ...r, [col]: fill } : r));
        break;
      }
      case "impute_mode": {
        if (!col) break;
        const p = profileColumn(col, out);
        const fill = p.top?.[0]?.value ?? "unknown";
        out = out.map((r) => (r[col] === null || r[col] === "" ? { ...r, [col]: fill } : r));
        break;
      }
      case "trim_whitespace":
        out = out.map((r) => {
          const n: Row = { ...r };
          for (const c of cols) if (typeof n[c] === "string") n[c] = (n[c] as string).trim();
          return n;
        });
        break;
      case "cast_numeric":
        if (!col) break;
        out = out.map((r) => {
          const v = r[col];
          if (v === null) return r;
          const n = Number(String(v).replace(/[$,%\s]/g, ""));
          return Number.isNaN(n) ? r : { ...r, [col]: n };
        });
        break;
      case "clip_outliers": {
        if (!col) break;
        const nums = out
          .map((r) => Number(r[col]))
          .filter((n) => !Number.isNaN(n))
          .sort((a, b) => a - b);
        if (!nums.length) break;
        const q1 = quantile(nums, 0.25);
        const q3 = quantile(nums, 0.75);
        const iqr = q3 - q1;
        const lo = q1 - 1.5 * iqr;
        const hi = q3 + 1.5 * iqr;
        out = out.map((r) => {
          const v = Number(r[col]);
          if (Number.isNaN(v)) return r;
          return { ...r, [col]: Math.min(hi, Math.max(lo, v)) };
        });
        break;
      }
    }
  }
  return { columns: cols, rows: out };
}

/* ----------------------------- aggregation ------------------------------- */

export function aggregate(
  rows: Row[],
  x: string,
  y: string,
  agg: Agg,
  limit = 12,
): Array<{ name: string; value: number }> {
  const groups = new Map<string, number[]>();
  for (const r of rows) {
    const key = r[x] === null || r[x] === "" ? "(blank)" : String(r[x]);
    const raw = Number(r[y]);
    const arr = groups.get(key) ?? [];
    arr.push(Number.isNaN(raw) ? 0 : raw);
    groups.set(key, arr);
  }
  const result = [...groups.entries()].map(([name, vals]) => {
    let value = 0;
    switch (agg) {
      case "sum":
        value = vals.reduce((a, b) => a + b, 0);
        break;
      case "avg":
        value = vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
        break;
      case "count":
        value = vals.length;
        break;
      case "min":
        value = Math.min(...vals);
        break;
      case "max":
        value = Math.max(...vals);
        break;
    }
    return { name, value: Math.round(value * 100) / 100 };
  });
  const chronological =
    result.length > 0 && result.every((r) => !Number.isNaN(Date.parse(r.name)) && /\d{4}/.test(r.name));
  if (chronological) {
    result.sort((a, b) => Date.parse(a.name) - Date.parse(b.name));
    return result.slice(0, limit);
  }
  result.sort((a, b) => b.value - a.value);
  return result.slice(0, limit);

}

export function correlation(rows: Row[], a: string, b: string): number | null {
  const pairs = rows
    .map((r) => [Number(r[a]), Number(r[b])])
    .filter(([x, y]) => !Number.isNaN(x) && !Number.isNaN(y));
  if (pairs.length < 3) return null;
  const n = pairs.length;
  const mx = pairs.reduce((s, p) => s + p[0], 0) / n;
  const my = pairs.reduce((s, p) => s + p[1], 0) / n;
  let num = 0;
  let dx = 0;
  let dy = 0;
  for (const [x, y] of pairs) {
    num += (x - mx) * (y - my);
    dx += (x - mx) ** 2;
    dy += (y - my) ** 2;
  }
  if (dx === 0 || dy === 0) return null;
  return num / Math.sqrt(dx * dy);
}

export const fmtNum = (n: number) =>
  Math.abs(n) >= 1000 ? n.toLocaleString(undefined, { maximumFractionDigits: 0 }) : String(Math.round(n * 100) / 100);

export const fmtCompact = (n: number) =>
  new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(n);
