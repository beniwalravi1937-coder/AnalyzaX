"use client";

import React, { useState, useMemo } from "react";
import { EDAResponse, UnivariateNumeric, UnivariateCategorical, DatetimeAnalysis } from "@/types";
import { EdaVisualizer } from "./EdaVisualizer";
import { SectionCard } from "@/components/ui/SectionCard";
import { SearchIcon } from "@/components/icons";

interface UnivariateTabProps {
  report: EDAResponse;
}

export function UnivariateTab({ report }: UnivariateTabProps) {
  const charts = report.charts || [];
  const numeric: UnivariateNumeric[] = (report as any).univariate?.numeric || report.numeric_analyses || [];
  const categorical: UnivariateCategorical[] = (report as any).univariate?.categorical || report.categorical_analyses || [];
  const datetime: DatetimeAnalysis[] = (report as any).univariate?.datetime || report.datetime_analyses || [];

  const [filterType, setFilterType] = useState<"all" | "numeric" | "categorical" | "datetime">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // All columns unified list
  const allColumns = useMemo(() => {
    const list: { name: string; type: "numeric" | "categorical" | "datetime"; data: any }[] = [];
    numeric.forEach((n: UnivariateNumeric) => list.push({ name: n.column, type: "numeric", data: n }));
    categorical.forEach((c: UnivariateCategorical) => list.push({ name: c.column, type: "categorical", data: c }));
    datetime.forEach((d: DatetimeAnalysis) => list.push({ name: d.column, type: "datetime", data: d }));
    return list;
  }, [numeric, categorical, datetime]);

  // Filtered columns
  const filteredColumns = useMemo(() => {
    return allColumns.filter((col) => {
      const matchesType = filterType === "all" || col.type === filterType;
      const matchesSearch = col.name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [allColumns, filterType, searchQuery]);

  // Selected column
  const [selectedColName, setSelectedColName] = useState<string>(
    allColumns.length > 0 ? allColumns[0].name : ""
  );

  const selectedCol = useMemo(() => {
    return allColumns.find((c) => c.name === selectedColName) || (allColumns.length > 0 ? allColumns[0] : null);
  }, [allColumns, selectedColName]);

  // Get charts for selected column
  const colCharts = useMemo(() => {
    if (!selectedCol) return [];
    if (selectedCol.type === "numeric") {
      return charts.filter(
        (c) => c.chart_id === `hist_${selectedCol.name}` || c.chart_id === `box_${selectedCol.name}`
      );
    }
    if (selectedCol.type === "categorical") {
      return charts.filter((c) => c.chart_id === `bar_${selectedCol.name}`);
    }
    if (selectedCol.type === "datetime") {
      return charts.filter((c) => c.chart_id === `line_${selectedCol.name}`);
    }
    return [];
  }, [selectedCol, charts]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "1.5rem", alignItems: "start" }}>
      {/* Left Sidebar: Column Selector & Search */}
      <div className="card" style={{ padding: "1.25rem" }}>
        {/* Search */}
        <div style={{ position: "relative", marginBottom: "1rem" }}>
          <SearchIcon
            size={14}
            style={{
              position: "absolute",
              left: "10px",
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-muted)",
            }}
          />
          <input
            type="text"
            placeholder="Search columns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input"
            style={{ paddingLeft: "2rem", width: "100%", fontSize: "0.8125rem" }}
          />
        </div>

        {/* Type Filter Pills */}
        <div style={{ display: "flex", gap: "0.35rem", marginBottom: "1rem", flexWrap: "wrap" }}>
          {(["all", "numeric", "categorical", "datetime"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`btn ${filterType === t ? "btn-primary" : "btn-ghost"}`}
              style={{
                fontSize: "0.6875rem",
                padding: "0.25rem 0.55rem",
                textTransform: "capitalize",
              }}
            >
              {t} {t === "all" ? `(${allColumns.length})` : ""}
            </button>
          ))}
        </div>

        {/* Column List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", maxHeight: "600px", overflowY: "auto" }}>
          {filteredColumns.length === 0 ? (
            <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.75rem" }}>
              No columns match criteria
            </div>
          ) : (
            filteredColumns.map((col) => {
              const isSelected = selectedCol?.name === col.name;
              const typeBadge =
                col.type === "numeric"
                  ? "badge-indigo"
                  : col.type === "categorical"
                  ? "badge-emerald"
                  : "badge-amber";

              return (
                <button
                  key={col.name}
                  onClick={() => setSelectedColName(col.name)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.6rem 0.75rem",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: isSelected ? "var(--color-primary-soft)" : "transparent",
                    border: isSelected ? "1px solid var(--color-primary)" : "1px solid transparent",
                    color: isSelected ? "var(--text-primary)" : "var(--text-secondary)",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "all 0.15s ease",
                    width: "100%",
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.8125rem",
                      fontWeight: isSelected ? 600 : 400,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      marginRight: "0.5rem",
                    }}
                    title={col.name}
                  >
                    {col.name}
                  </span>
                  <span className={`badge ${typeBadge}`} style={{ fontSize: "0.625rem", textTransform: "uppercase" }}>
                    {col.type.slice(0, 3)}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Right Content: Selected Column Deep Drilldown */}
      <div>
        {selectedCol ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {/* Header / Meta Card */}
            <div className="card" style={{ padding: "1.25rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
                      {selectedCol.name}
                    </h3>
                    <span className="badge badge-primary" style={{ textTransform: "uppercase", fontSize: "0.6875rem" }}>
                      {selectedCol.type}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                    Missing: {selectedCol.data.missing_count || 0} ({(selectedCol.data.missing_percentage || 0).toFixed(2)}%)
                  </div>
                </div>

                {selectedCol.type === "numeric" && selectedCol.data.distribution_shape && (
                  <span className="badge badge-indigo" style={{ fontSize: "0.75rem", padding: "0.4rem 0.8rem" }}>
                    Shape: {selectedCol.data.distribution_shape.replace("_", " ").toUpperCase()}
                  </span>
                )}
                {selectedCol.type === "categorical" && selectedCol.data.cardinality_class && (
                  <span className="badge badge-emerald" style={{ fontSize: "0.75rem", padding: "0.4rem 0.8rem" }}>
                    Cardinality: {selectedCol.data.cardinality_class.toUpperCase()}
                  </span>
                )}
              </div>
            </div>

            {/* Numeric Feature Specific View */}
            {selectedCol.type === "numeric" && (
              <NumericDetailView num={selectedCol.data as UnivariateNumeric} charts={colCharts} />
            )}

            {/* Categorical Feature Specific View */}
            {selectedCol.type === "categorical" && (
              <CategoricalDetailView cat={selectedCol.data as UnivariateCategorical} charts={colCharts} />
            )}

            {/* Datetime Feature Specific View */}
            {selectedCol.type === "datetime" && (
              <DatetimeDetailView dt={selectedCol.data as DatetimeAnalysis} charts={colCharts} />
            )}
          </div>
        ) : (
          <div className="card" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
            Select a column to view statistical distribution details.
          </div>
        )}
      </div>
    </div>
  );
}

function NumericDetailView({ num, charts }: { num: UnivariateNumeric; charts: any[] }) {
  const mean = num.parametric?.mean ?? num.mean ?? 0;
  const std = num.parametric?.std ?? num.std ?? 0;
  const median = num.non_parametric?.median ?? num.median ?? 0;
  const iqr = num.non_parametric?.iqr ?? num.iqr ?? 0;
  const min = num.non_parametric?.min ?? num.min ?? 0;
  const max = num.non_parametric?.max ?? num.max ?? 0;
  const skewness = num.parametric?.skewness ?? num.skewness ?? 0;
  const kurtosis = num.parametric?.kurtosis ?? num.kurtosis ?? 0;
  const outlierCount = num.outliers?.outlier_count ?? num.outlier_count_tukey ?? 0;
  const outlierPct = num.outliers?.outlier_percentage ?? num.outlier_percentage ?? 0;

  const histChart = charts.find((c) => c.chart_type === "histogram");
  const boxChart = charts.find((c) => c.chart_type === "box");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Metrics Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem" }}>
        <MetricCard label="Mean" value={mean.toFixed(2)} />
        <MetricCard label="Std Dev" value={std.toFixed(2)} />
        <MetricCard label="Median (Q2)" value={median.toFixed(2)} />
        <MetricCard label="IQR" value={iqr.toFixed(2)} />
        <MetricCard label="Min" value={min.toFixed(2)} />
        <MetricCard label="Max" value={max.toFixed(2)} />
        <MetricCard label="Skewness" value={skewness.toFixed(2)} />
        <MetricCard label="Kurtosis" value={kurtosis.toFixed(2)} />
        <MetricCard
          label="Outliers"
          value={`${outlierCount} (${outlierPct.toFixed(1)}%)`}
          highlight={outlierCount > 0}
        />
      </div>

      {/* Visualizations: Histogram & Box Plot */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.25rem" }}>
        {histChart && (
          <SectionCard title="Frequency Distribution" subtitle={histChart.description || "Histogram with equal-width bins"}>
            <EdaVisualizer spec={histChart} height={240} />
          </SectionCard>
        )}

        {boxChart && (
          <SectionCard title="Quantiles & Outlier Spread" subtitle={boxChart.description || "Box plot with 1.5x IQR fences"}>
            <EdaVisualizer spec={boxChart} height={200} />
          </SectionCard>
        )}
      </div>
    </div>
  );
}

function CategoricalDetailView({ cat, charts }: { cat: UnivariateCategorical; charts: any[] }) {
  const barChart = charts.find((c) => c.chart_type === "bar");
  const totalCount = cat.total_count ?? cat.count ?? 0;
  const missingPct = cat.missing_percentage ?? (totalCount > 0 ? (cat.null_count / totalCount) * 100 : 0);
  const entropyVal = cat.shannon_entropy ?? cat.entropy;
  const cardClass = cat.cardinality_class ?? (cat.is_high_cardinality ? "high" : "low");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Metrics Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "0.75rem" }}>
        <MetricCard label="Unique Values" value={cat.unique_count.toLocaleString()} />
        <MetricCard label="Total Count" value={totalCount.toLocaleString()} />
        <MetricCard label="Missing" value={`${missingPct.toFixed(1)}%`} />
        {entropyVal !== undefined && entropyVal !== null && (
          <MetricCard label="Shannon Entropy" value={entropyVal.toFixed(2)} />
        )}
        <MetricCard label="Cardinality" value={String(cardClass).toUpperCase()} />
      </div>

      {/* Bar Chart & Top Categories */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.25rem" }}>
        {barChart && (
          <SectionCard title="Top Categories Distribution" subtitle={barChart.description || "Frequency distribution"}>
            <EdaVisualizer spec={barChart} height={280} />
          </SectionCard>
        )}

        {/* Top Categories Table */}
        <SectionCard title="Top Frequency Breakdown" subtitle={`Showing top ${cat.top_categories.length} classes`}>
          <div style={{ overflowX: "auto" }}>
            <table className="table" style={{ width: "100%", fontSize: "0.8125rem" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left" }}>Category</th>
                  <th style={{ textAlign: "right" }}>Count</th>
                  <th style={{ textAlign: "right" }}>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {cat.top_categories.map((c, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500, color: "var(--text-primary)" }}>{c.category}</td>
                    <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{c.count.toLocaleString()}</td>
                    <td style={{ textAlign: "right", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                      {c.percentage.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

function DatetimeDetailView({ dt, charts }: { dt: DatetimeAnalysis; charts: any[] }) {
  const lineChart = charts.find((c) => c.chart_type === "line");
  const earliest = dt.earliest || dt.min_timestamp || "N/A";
  const latest = dt.latest || dt.max_timestamp || "N/A";
  const span = dt.span_days != null ? `${dt.span_days.toFixed(0)} days` : "N/A";
  const freq = dt.inferred_frequency || dt.detected_frequency || "Irregular";
  const missingPct = dt.missing_percentage ?? (dt.count > 0 ? (dt.null_count / dt.count) * 100 : 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Metrics Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "0.75rem" }}>
        <MetricCard label="Earliest Timestamp" value={earliest ? String(earliest).slice(0, 19) : "N/A"} />
        <MetricCard label="Latest Timestamp" value={latest ? String(latest).slice(0, 19) : "N/A"} />
        <MetricCard label="Temporal Span" value={span} />
        <MetricCard label="Inferred Frequency" value={freq} />
        <MetricCard label="Completeness" value={`${(100 - missingPct).toFixed(1)}%`} />
      </div>

      {lineChart && (
        <SectionCard title="Temporal Timeline Trend" subtitle={lineChart.description || "Activity over time"}>
          <EdaVisualizer spec={lineChart} height={240} />
        </SectionCard>
      )}
    </div>
  );
}

function MetricCard({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div
      className="card"
      style={{
        padding: "0.75rem",
        backgroundColor: highlight ? "rgba(244, 63, 94, 0.05)" : "var(--bg-card)",
        border: highlight ? "1px solid rgba(244, 63, 94, 0.3)" : "1px solid var(--border-subtle)",
      }}
    >
      <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {label}
      </div>
      <div
        style={{
          fontSize: "1.125rem",
          fontWeight: 600,
          color: highlight ? "#f43f5e" : "var(--text-primary)",
          fontFamily: "var(--font-mono)",
          marginTop: "0.2rem",
        }}
      >
        {value}
      </div>
    </div>
  );
}
