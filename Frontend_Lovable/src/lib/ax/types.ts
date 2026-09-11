export type ColKind = "numeric" | "categorical" | "temporal" | "boolean";

export type Row = Record<string, string | number | null>;

export interface ColumnProfile {
  name: string;
  kind: ColKind;
  missing: number;
  missingPct: number;
  unique: number;
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
  outliers?: number;
  top?: Array<{ value: string; count: number }>;
}

export interface DatasetProfile {
  rowCount: number;
  colCount: number;
  missingCells: number;
  duplicateRows: number;
  qualityScore: number;
  issues: number;
  columns: ColumnProfile[];
}

export type StepKind =
  | "drop_column"
  | "impute_median"
  | "impute_mode"
  | "trim_whitespace"
  | "drop_duplicates"
  | "drop_missing_rows"
  | "cast_numeric"
  | "clip_outliers";

export interface TransformStep {
  id: string;
  kind: StepKind;
  column?: string;
  label: string;
  detail: string;
}

export interface Recommendation extends Omit<TransformStep, "id"> {
  id: string;
  severity: "high" | "medium" | "low";
  reason: string;
}

export interface DatasetVersion {
  id: string;
  label: string;
  createdAt: number;
  steps: TransformStep[];
  columns: string[];
  rows: Row[];
}

export interface Dataset {
  id: string;
  name: string;
  createdAt: number;
  columns: string[];
  versions: DatasetVersion[];
  activeVersionId: string;
}

export type ChartType = "bar" | "line" | "area" | "pie" | "scatter";
export type Agg = "sum" | "avg" | "count" | "min" | "max";

export interface ChartSpec {
  id: string;
  title: string;
  type: ChartType;
  x: string;
  y: string;
  agg: Agg;
  limit: number;
}
