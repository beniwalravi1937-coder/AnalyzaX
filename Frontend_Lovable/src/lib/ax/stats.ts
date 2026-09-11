import type { Row } from "./types";

export function nums(rows: Row[], col: string): number[] {
  const out: number[] = [];
  for (const r of rows) {
    const v = Number(r[col]);
    if (r[col] !== null && r[col] !== "" && !Number.isNaN(v)) out.push(v);
  }
  return out;
}

export const mean = (v: number[]) => (v.length ? v.reduce((a, b) => a + b, 0) / v.length : 0);

export function variance(v: number[]): number {
  if (v.length < 2) return 0;
  const m = mean(v);
  return v.reduce((s, x) => s + (x - m) ** 2, 0) / (v.length - 1);
}

export const sd = (v: number[]) => Math.sqrt(variance(v));

export function quantile(v: number[], q: number): number {
  if (!v.length) return 0;
  const s = [...v].sort((a, b) => a - b);
  const pos = (s.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  const next = s[base + 1] ?? s[base];
  return s[base] + rest * (next - s[base]);
}

export const median = (v: number[]) => quantile(v, 0.5);

export function skewness(v: number[]): number {
  const s = sd(v);
  if (!s || v.length < 3) return 0;
  const m = mean(v);
  return v.reduce((a, x) => a + ((x - m) / s) ** 3, 0) / v.length;
}

export function kurtosis(v: number[]): number {
  const s = sd(v);
  if (!s || v.length < 4) return 0;
  const m = mean(v);
  return v.reduce((a, x) => a + ((x - m) / s) ** 4, 0) / v.length - 3;
}

// ---------- distributions ----------

function logGamma(x: number): number {
  const c = [
    76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155,
    0.1208650973866179e-2, -0.5395239384953e-5,
  ];
  let y = x;
  let tmp = x + 5.5;
  tmp -= (x + 0.5) * Math.log(tmp);
  let ser = 1.000000000190015;
  for (let j = 0; j < 6; j++) ser += c[j] / ++y;
  return -tmp + Math.log((2.5066282746310005 * ser) / x);
}

function betacf(a: number, b: number, x: number): number {
  const FPMIN = 1e-300;
  const qab = a + b;
  const qap = a + 1;
  const qam = a - 1;
  let c = 1;
  let d = 1 - (qab * x) / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= 200; m++) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    h *= d * c;
    aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < 3e-9) break;
  }
  return h;
}

function incompleteBeta(a: number, b: number, x: number): number {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const bt = Math.exp(logGamma(a + b) - logGamma(a) - logGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
  return x < (a + 1) / (a + b + 2) ? (bt * betacf(a, b, x)) / a : 1 - (bt * betacf(b, a, 1 - x)) / b;
}

/** Two-sided p-value for a t statistic with df degrees of freedom. */
export function tPValue(t: number, df: number): number {
  if (!Number.isFinite(t) || df <= 0) return 1;
  return incompleteBeta(df / 2, 0.5, df / (df + t * t));
}

function lowerGamma(s: number, x: number): number {
  if (x <= 0) return 0;
  let sum = 1 / s;
  let term = sum;
  for (let n = 1; n < 300; n++) {
    term *= x / (s + n);
    sum += term;
    if (term < sum * 1e-12) break;
  }
  return sum * Math.exp(-x + s * Math.log(x) - logGamma(s));
}

/** Upper-tail p-value for a chi-square statistic. */
export function chiSquarePValue(chi2: number, df: number): number {
  if (!Number.isFinite(chi2) || df <= 0) return 1;
  return Math.max(0, Math.min(1, 1 - lowerGamma(df / 2, chi2 / 2)));
}

export function fPValue(f: number, df1: number, df2: number): number {
  if (!Number.isFinite(f) || f <= 0) return 1;
  return incompleteBeta(df2 / 2, df1 / 2, df2 / (df2 + df1 * f));
}

// ---------- tests ----------

export interface TestResult {
  name: string;
  statistic: number;
  pValue: number;
  df?: number;
  effect?: { label: string; value: number };
  ci?: [number, number];
  detail: string;
}

export function welchTTest(a: number[], b: number[], labelA: string, labelB: string): TestResult | null {
  if (a.length < 3 || b.length < 3) return null;
  const ma = mean(a);
  const mb = mean(b);
  const va = variance(a);
  const vb = variance(b);
  const se = Math.sqrt(va / a.length + vb / b.length);
  if (!se) return null;
  const t = (ma - mb) / se;
  const df =
    (va / a.length + vb / b.length) ** 2 /
    ((va / a.length) ** 2 / (a.length - 1) + (vb / b.length) ** 2 / (b.length - 1));
  const pooled = Math.sqrt(((a.length - 1) * va + (b.length - 1) * vb) / (a.length + b.length - 2));
  const d = pooled ? (ma - mb) / pooled : 0;
  return {
    name: "Welch two-sample t-test",
    statistic: t,
    pValue: tPValue(t, df),
    df,
    effect: { label: "Cohen's d", value: d },
    ci: [ma - mb - 1.96 * se, ma - mb + 1.96 * se],
    detail: `${labelA} mean ${ma.toFixed(2)} (n=${a.length}) vs ${labelB} mean ${mb.toFixed(2)} (n=${b.length})`,
  };
}

export function oneSampleTTest(v: number[], mu: number): TestResult | null {
  if (v.length < 3) return null;
  const m = mean(v);
  const se = sd(v) / Math.sqrt(v.length);
  if (!se) return null;
  const t = (m - mu) / se;
  const df = v.length - 1;
  return {
    name: "One-sample t-test",
    statistic: t,
    pValue: tPValue(t, df),
    df,
    ci: [m - 1.96 * se, m + 1.96 * se],
    detail: `Sample mean ${m.toFixed(3)} tested against ${mu}`,
  };
}

export function mannWhitney(a: number[], b: number[]): TestResult | null {
  if (a.length < 3 || b.length < 3) return null;
  const all = [...a.map((v) => ({ v, g: 0 })), ...b.map((v) => ({ v, g: 1 }))].sort((x, y) => x.v - y.v);
  const ranks = new Array(all.length).fill(0);
  let i = 0;
  while (i < all.length) {
    let j = i;
    while (j + 1 < all.length && all[j + 1].v === all[i].v) j++;
    const r = (i + j + 2) / 2;
    for (let k = i; k <= j; k++) ranks[k] = r;
    i = j + 1;
  }
  let ra = 0;
  all.forEach((item, idx) => {
    if (item.g === 0) ra += ranks[idx];
  });
  const na = a.length;
  const nb = b.length;
  const u = ra - (na * (na + 1)) / 2;
  const mu = (na * nb) / 2;
  const su = Math.sqrt((na * nb * (na + nb + 1)) / 12);
  const z = su ? (u - mu) / su : 0;
  const p = 2 * (1 - normalCdf(Math.abs(z)));
  return {
    name: "Mann-Whitney U test",
    statistic: u,
    pValue: Math.max(0, Math.min(1, p)),
    effect: { label: "Rank-biserial", value: (2 * u) / (na * nb) - 1 },
    detail: `Distribution-free comparison of ${na} vs ${nb} observations`,
  };
}

export function normalCdf(z: number): number {
  const t = 1 / (1 + 0.2316419 * Math.abs(z));
  const d = 0.3989423 * Math.exp((-z * z) / 2);
  const p = d * t * (1.330274429 * t ** 4 - 1.821255978 * t ** 3 + 1.781477937 * t ** 2 - 0.356563782 * t + 0.319381530);
  return z > 0 ? 1 - p : p;
}

export function chiSquareIndependence(rows: Row[], a: string, b: string): TestResult | null {
  const catsA = [...new Set(rows.map((r) => String(r[a] ?? "(blank)")))];
  const catsB = [...new Set(rows.map((r) => String(r[b] ?? "(blank)")))];
  if (catsA.length < 2 || catsB.length < 2 || catsA.length > 30 || catsB.length > 30) return null;
  const table = catsA.map(() => catsB.map(() => 0));
  for (const r of rows) {
    const i = catsA.indexOf(String(r[a] ?? "(blank)"));
    const j = catsB.indexOf(String(r[b] ?? "(blank)"));
    if (i >= 0 && j >= 0) table[i][j]++;
  }
  const total = rows.length;
  const rowSums = table.map((r) => r.reduce((s, x) => s + x, 0));
  const colSums = catsB.map((_, j) => table.reduce((s, r) => s + r[j], 0));
  let chi2 = 0;
  for (let i = 0; i < catsA.length; i++) {
    for (let j = 0; j < catsB.length; j++) {
      const e = (rowSums[i] * colSums[j]) / total;
      if (e > 0) chi2 += (table[i][j] - e) ** 2 / e;
    }
  }
  const df = (catsA.length - 1) * (catsB.length - 1);
  return {
    name: "Chi-square test of independence",
    statistic: chi2,
    pValue: chiSquarePValue(chi2, df),
    df,
    effect: { label: "Cramér's V", value: Math.sqrt(chi2 / (total * Math.min(catsA.length - 1, catsB.length - 1))) },
    detail: `${catsA.length} × ${catsB.length} contingency table on ${total} rows`,
  };
}

export function anova(groups: { label: string; values: number[] }[]): TestResult | null {
  const valid = groups.filter((g) => g.values.length >= 2);
  if (valid.length < 2) return null;
  const all = valid.flatMap((g) => g.values);
  const grand = mean(all);
  const ssb = valid.reduce((s, g) => s + g.values.length * (mean(g.values) - grand) ** 2, 0);
  const ssw = valid.reduce((s, g) => s + g.values.reduce((a, x) => a + (x - mean(g.values)) ** 2, 0), 0);
  const df1 = valid.length - 1;
  const df2 = all.length - valid.length;
  if (df2 <= 0 || ssw === 0) return null;
  const f = ssb / df1 / (ssw / df2);
  return {
    name: "One-way ANOVA",
    statistic: f,
    pValue: fPValue(f, df1, df2),
    df: df1,
    effect: { label: "Eta squared", value: ssb / (ssb + ssw) },
    detail: `${valid.length} groups, ${all.length} observations`,
  };
}

// ---------- regression ----------

function solve(A: number[][], b: number[]): number[] | null {
  const n = A.length;
  const M = A.map((row, i) => [...row, b[i]]);
  for (let i = 0; i < n; i++) {
    let piv = i;
    for (let r = i + 1; r < n; r++) if (Math.abs(M[r][i]) > Math.abs(M[piv][i])) piv = r;
    if (Math.abs(M[piv][i]) < 1e-12) return null;
    [M[i], M[piv]] = [M[piv], M[i]];
    for (let r = 0; r < n; r++) {
      if (r === i) continue;
      const f = M[r][i] / M[i][i];
      for (let c = i; c <= n; c++) M[r][c] -= f * M[i][c];
    }
  }
  return M.map((row, i) => row[n] / row[i]);
}

export interface Regression {
  coefficients: { name: string; value: number }[];
  r2: number;
  adjR2: number;
  rmse: number;
  n: number;
  predict: (x: number[]) => number;
}

export function ols(X: number[][], y: number[], names: string[]): Regression | null {
  const n = y.length;
  const k = names.length;
  if (n <= k + 1) return null;
  const design = X.map((row) => [1, ...row]);
  const p = k + 1;
  const XtX = Array.from({ length: p }, (_, i) =>
    Array.from({ length: p }, (_, j) => design.reduce((s, row) => s + row[i] * row[j], 0)),
  );
  const Xty = Array.from({ length: p }, (_, i) => design.reduce((s, row, r) => s + row[i] * y[r], 0));
  const beta = solve(XtX, Xty);
  if (!beta) return null;
  const yhat = design.map((row) => row.reduce((s, v, i) => s + v * beta[i], 0));
  const ybar = mean(y);
  const ssTot = y.reduce((s, v) => s + (v - ybar) ** 2, 0);
  const ssRes = y.reduce((s, v, i) => s + (v - yhat[i]) ** 2, 0);
  const r2 = ssTot ? 1 - ssRes / ssTot : 0;
  return {
    coefficients: [{ name: "Intercept", value: beta[0] }, ...names.map((nm, i) => ({ name: nm, value: beta[i + 1] }))],
    r2,
    adjR2: 1 - ((1 - r2) * (n - 1)) / (n - k - 1),
    rmse: Math.sqrt(ssRes / n),
    n,
    predict: (x: number[]) => beta[0] + x.reduce((s, v, i) => s + v * beta[i + 1], 0),
  };
}

export function kMeans(points: number[][], k: number, iterations = 25) {
  if (points.length < k) return null;
  const dim = points[0].length;
  const centroids = points.slice(0, k).map((p) => [...p]);
  let assign = new Array(points.length).fill(0);
  for (let it = 0; it < iterations; it++) {
    assign = points.map((p) => {
      let best = 0;
      let bestD = Infinity;
      centroids.forEach((c, ci) => {
        const d = c.reduce((s, v, i) => s + (v - p[i]) ** 2, 0);
        if (d < bestD) {
          bestD = d;
          best = ci;
        }
      });
      return best;
    });
    for (let ci = 0; ci < k; ci++) {
      const members = points.filter((_, i) => assign[i] === ci);
      if (!members.length) continue;
      for (let d = 0; d < dim; d++) centroids[ci][d] = mean(members.map((m) => m[d]));
    }
  }
  const inertia = points.reduce(
    (s, p, i) => s + centroids[assign[i]].reduce((a, v, d) => a + (v - p[d]) ** 2, 0),
    0,
  );
  return { centroids, assign, inertia };
}

// ---------- forecasting ----------

export type ForecastMethod = "naive" | "mean" | "moving_average" | "linear_trend" | "holt";

export interface ForecastPoint {
  label: string;
  actual: number | null;
  fitted: number | null;
  forecast: number | null;
  lower: number | null;
  upper: number | null;
}

export interface ForecastResult {
  points: ForecastPoint[];
  rmse: number;
  mae: number;
  mape: number;
  method: ForecastMethod;
}

function fitSeries(y: number[], method: ForecastMethod, horizon: number): { fitted: number[]; future: number[] } {
  const n = y.length;
  const fitted: number[] = [];
  const future: number[] = [];
  const window = Math.max(2, Math.min(7, Math.round(n / 8)));
  switch (method) {
    case "naive": {
      for (let i = 0; i < n; i++) fitted.push(i === 0 ? y[0] : y[i - 1]);
      for (let h = 0; h < horizon; h++) future.push(y[n - 1]);
      break;
    }
    case "mean": {
      const m = mean(y);
      for (let i = 0; i < n; i++) fitted.push(m);
      for (let h = 0; h < horizon; h++) future.push(m);
      break;
    }
    case "moving_average": {
      for (let i = 0; i < n; i++) {
        const slice = y.slice(Math.max(0, i - window), i);
        fitted.push(slice.length ? mean(slice) : y[i]);
      }
      const last = mean(y.slice(-window));
      for (let h = 0; h < horizon; h++) future.push(last);
      break;
    }
    case "linear_trend": {
      const xs = y.map((_, i) => i);
      const mx = mean(xs);
      const my = mean(y);
      const denom = xs.reduce((s, x) => s + (x - mx) ** 2, 0) || 1;
      const slope = xs.reduce((s, x, i) => s + (x - mx) * (y[i] - my), 0) / denom;
      const intercept = my - slope * mx;
      for (let i = 0; i < n; i++) fitted.push(intercept + slope * i);
      for (let h = 1; h <= horizon; h++) future.push(intercept + slope * (n - 1 + h));
      break;
    }
    case "holt": {
      const alpha = 0.5;
      const beta = 0.2;
      let level = y[0];
      let trend = y.length > 1 ? y[1] - y[0] : 0;
      for (let i = 0; i < n; i++) {
        const f = level + trend;
        fitted.push(i === 0 ? y[0] : f);
        const prevLevel = level;
        level = alpha * y[i] + (1 - alpha) * (level + trend);
        trend = beta * (level - prevLevel) + (1 - beta) * trend;
      }
      for (let h = 1; h <= horizon; h++) future.push(level + h * trend);
      break;
    }
  }
  return { fitted, future };
}

export function forecast(
  labels: string[],
  values: number[],
  method: ForecastMethod,
  horizon: number,
): ForecastResult | null {
  if (values.length < 5) return null;
  const { fitted, future } = fitSeries(values, method, horizon);
  const residuals = values.map((v, i) => v - fitted[i]).slice(1);
  const rmse = Math.sqrt(mean(residuals.map((r) => r * r)));
  const mae = mean(residuals.map((r) => Math.abs(r)));
  const scale = mean(values.map(Math.abs)) || 1;
  const pcts = values
    .slice(1)
    .map((v, i) => Math.abs(residuals[i]) / Math.max(Math.abs(v), scale * 0.1));
  const mape = (pcts.length ? mean(pcts) : 0) * 100;
  const points: ForecastPoint[] = values.map((v, i) => ({
    label: labels[i],
    actual: v,
    fitted: fitted[i],
    forecast: null,
    lower: null,
    upper: null,
  }));
  future.forEach((f, h) => {
    const band = 1.96 * rmse * Math.sqrt(h + 1);
    points.push({
      label: `+${h + 1}`,
      actual: null,
      fitted: null,
      forecast: f,
      lower: f - band,
      upper: f + band,
    });
  });
  return { points, rmse, mae, mape, method };
}
