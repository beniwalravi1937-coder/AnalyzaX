"use client";

import React, { useState, useMemo } from "react";
import { SQLQueryResponse, ChartSpec, ChartType } from "@/types";
import { EdaVisualizer } from "@/components/eda/EdaVisualizer";
import { SparklesIcon, BarChartIcon } from "@/components/icons";

interface SQLVisualizerProps {
  result: SQLQueryResponse | null;
}

export function SQLVisualizer({ result }: SQLVisualizerProps) {
  const columns = result?.columns || [];
  const rows = result?.rows || [];
  const suggestedCharts = result?.suggested_charts || [];

  const [selectedChartIdx, setSelectedChartIdx] = useState<number>(0);
  const [customChartType, setCustomChartType] = useState<string>("bar");
  const [customX, setCustomX] = useState<string>("");
  const [customY, setCustomY] = useState<string>("");

  const numCols = useMemo(() => columns.filter((c) => c.semantic_type === "numeric"), [columns]);
  const catCols = useMemo(() => columns.filter((c) => c.semantic_type === "categorical"), [columns]);
  const dateCols = useMemo(() => columns.filter((c) => c.semantic_type === "datetime"), [columns]);

  // Set default custom axes if available
  React.useEffect(() => {
    if (!customX && (catCols.length || dateCols.length || columns.length)) {
      setCustomX(catCols[0]?.name || dateCols[0]?.name || columns[0]?.name || "");
    }
    if (!customY && numCols.length) {
      setCustomY(numCols[0]?.name || "");
    }
  }, [columns, numCols, catCols, dateCols, customX, customY]);

  // Build active ChartSpec
  const activeChartSpec = useMemo<ChartSpec | null>(() => {
    if (!rows.length || !columns.length) return null;

    // If viewing one of the recommended charts:
    if (suggestedCharts.length > 0 && selectedChartIdx < suggestedCharts.length) {
      return suggestedCharts[selectedChartIdx];
    }

    // Build custom chart specification from user selection
    const xField = customX || columns[0]?.name;
    const yField = customY || (numCols[0]?.name || columns[1]?.name);

    if (customChartType === "bar") {
      const data = rows.slice(0, 30).map((r) => ({
        category: String(r[xField] ?? "Unknown"),
        value: Number(r[yField] ?? 0),
      }));
      return {
        chart_id: `custom_bar_${xField}_${yField}`,
        chart_type: "bar" as ChartType,
        title: `${yField} by ${xField}`,
        description: `Bar visualization of ${yField} across ${xField}`,
        dataset_id: result?.dataset_id || "",
        version_id: result?.version_id || "",
        x: "category",
        y: "value",
        data,
      };
    }

    if (customChartType === "line") {
      const data = rows.slice(0, 50).map((r) => ({
        timestamp: String(r[xField] ?? ""),
        value: Number(r[yField] ?? 0),
      }));
      return {
        chart_id: `custom_line_${xField}_${yField}`,
        chart_type: "line" as ChartType,
        title: `Trend of ${yField} over ${xField}`,
        description: `Timeline plot of ${yField}`,
        dataset_id: result?.dataset_id || "",
        version_id: result?.version_id || "",
        x: "timestamp",
        y: "value",
        data,
      };
    }

    if (customChartType === "scatter") {
      const data = rows.slice(0, 100).map((r) => ({
        x: Number(r[xField] ?? 0),
        y: Number(r[yField] ?? 0),
      }));
      return {
        chart_id: `custom_scatter_${xField}_${yField}`,
        chart_type: "scatter" as ChartType,
        title: `${yField} vs ${xField}`,
        description: `Correlation scatter plot`,
        dataset_id: result?.dataset_id || "",
        version_id: result?.version_id || "",
        x: "x",
        y: "y",
        data,
      };
    }

    // Histogram
    const values = rows
      .map((r) => Number(r[yField || xField]))
      .filter((v) => !isNaN(v));
    const min = Math.min(...values);
    const max = Math.max(...values);
    const binCount = Math.min(10, values.length);
    const step = (max - min) / binCount || 1;
    const bins = Array.from({ length: binCount }, (_, i) => ({
      bin_start: min + i * step,
      bin_end: min + (i + 1) * step,
      count: 0,
    }));
    values.forEach((v) => {
      const idx = Math.min(Math.floor((v - min) / step), binCount - 1);
      bins[idx].count += 1;
    });

    return {
      chart_id: `custom_hist_${yField || xField}`,
      chart_type: "histogram" as ChartType,
      title: `Distribution of ${yField || xField}`,
      description: `Frequency distribution`,
      dataset_id: result?.dataset_id || "",
      version_id: result?.version_id || "",
      x: "bin_start",
      y: "count",
      data: bins,
    };
  }, [rows, columns, suggestedCharts, selectedChartIdx, customChartType, customX, customY, numCols, result]);

  if (!result || !rows.length) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <BarChartIcon size={32} style={{ marginBottom: "0.75rem", opacity: 0.5 }} />
        <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>No result set to visualize</div>
        <div style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
          Execute a query that returns rows to generate automatic interactive charts.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Visualizer Controls Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.6rem 0.75rem",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        {/* Recommended Chart Badges */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <SparklesIcon size={12} color="var(--primary-light)" />
            Suggestions:
          </span>
          {suggestedCharts.map((chart, idx) => {
            const isActive = selectedChartIdx === idx;
            return (
              <button
                key={chart.chart_id || idx}
                type="button"
                onClick={() => setSelectedChartIdx(idx)}
                className={`btn btn-sm ${isActive ? "btn-primary" : "btn-secondary"}`}
                style={{ fontSize: "0.6875rem", padding: "0.2rem 0.6rem", height: "26px" }}
              >
                {chart.title}
              </button>
            );
          })}
        </div>

        {/* Custom Axis Pickers */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Type:</span>
          <select
            value={customChartType}
            onChange={(e) => {
              setCustomChartType(e.target.value);
              setSelectedChartIdx(999);
            }}
            className="input input-sm"
            style={{ width: "95px", height: "26px", fontSize: "0.6875rem", padding: "0.1rem 0.3rem" }}
          >
            <option value="bar">Bar Chart</option>
            <option value="line">Line Chart</option>
            <option value="scatter">Scatter Plot</option>
            <option value="histogram">Histogram</option>
          </select>

          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>X:</span>
          <select
            value={customX}
            onChange={(e) => {
              setCustomX(e.target.value);
              setSelectedChartIdx(999);
            }}
            className="input input-sm"
            style={{ width: "100px", height: "26px", fontSize: "0.6875rem", padding: "0.1rem 0.3rem" }}
          >
            {columns.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>

          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Y:</span>
          <select
            value={customY}
            onChange={(e) => {
              setCustomY(e.target.value);
              setSelectedChartIdx(999);
            }}
            className="input input-sm"
            style={{ width: "100px", height: "26px", fontSize: "0.6875rem", padding: "0.1rem 0.3rem" }}
          >
            {columns.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Chart Canvas Area */}
      <div style={{ flex: 1, overflow: "auto", padding: "1.25rem", display: "flex", justifyContent: "center" }}>
        {activeChartSpec ? (
          <div style={{ width: "100%", maxWidth: "900px" }}>
            <div style={{ marginBottom: "0.75rem" }}>
              <div style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)" }}>
                {activeChartSpec.title}
              </div>
              {activeChartSpec.description && (
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {activeChartSpec.description}
                </div>
              )}
            </div>
            <div
              className="card"
              style={{
                backgroundColor: "var(--bg-surface)",
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <EdaVisualizer spec={activeChartSpec} height={320} />
            </div>
          </div>
        ) : (
          <div style={{ color: "var(--text-muted)", fontSize: "0.8125rem", margin: "auto" }}>
            Unable to construct chart for the given axis combination.
          </div>
        )}
      </div>
    </div>
  );
}
