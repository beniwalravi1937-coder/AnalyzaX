"use client";

import React from "react";
import { ChartSpec, ChartType, StructuredFilter } from "@/types";
import { VisualizationFilters } from "./VisualizationFilters";
import { SlidersIcon, RefreshIcon } from "@/components/icons";

interface ChartBuilderProps {
  spec: ChartSpec;
  onChange: (updatedSpec: ChartSpec) => void;
  availableColumns: { name: string; type?: string; is_numeric?: boolean; is_temporal?: boolean }[];
  onPreview: () => void;
  isLoading?: boolean;
}

interface ChartTypeOption {
  type: ChartType;
  label: string;
  tier: number;
  tierLabel: string;
  isSupported: boolean;
}

const CHART_TYPES: ChartTypeOption[] = [
  // Tier 1 — Core Production Charts
  { type: "bar", label: "Bar Chart", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "horizontal_bar", label: "Horizontal Bar", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "grouped_bar", label: "Grouped Bar", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "stacked_bar", label: "Stacked Bar", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "percent_stacked_bar", label: "100% Stacked Bar", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "line", label: "Line Chart", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "multi_line", label: "Multi-Series Line", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "area", label: "Area Chart", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "stacked_area", label: "Stacked Area", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "histogram", label: "Histogram", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "boxplot", label: "Box Plot", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "scatter", label: "Scatter Plot", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "heatmap", label: "Heatmap", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "donut", label: "Donut Chart", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "kpi_card", label: "KPI Metric Card", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },
  { type: "table", label: "Data Table", tier: 1, tierLabel: "Tier 1 — Core Production", isSupported: true },

  // Tier 2 — Advanced Analytical Charts
  { type: "treemap", label: "Treemap", tier: 2, tierLabel: "Tier 2 — Advanced Analytical", isSupported: true },
  { type: "bubble", label: "Bubble Chart", tier: 2, tierLabel: "Tier 2 — Advanced Analytical", isSupported: true },
  { type: "violin", label: "Violin Plot", tier: 2, tierLabel: "Tier 2 — Advanced Analytical", isSupported: true },
  { type: "pareto", label: "Pareto Chart", tier: 2, tierLabel: "Tier 2 — Advanced Analytical", isSupported: true },
  { type: "waterfall", label: "Waterfall Chart", tier: 2, tierLabel: "Tier 2 — Advanced Analytical", isSupported: true },
  { type: "funnel", label: "Funnel Chart", tier: 2, tierLabel: "Tier 2 — Advanced Analytical", isSupported: true },

  // Tier 3 — Specialized / Extensible (Deferred)
  { type: "sankey", label: "Sankey Diagram (Deferred)", tier: 3, tierLabel: "Tier 3 — Specialized (Deferred)", isSupported: false },
  { type: "radar", label: "Radar Chart (Deferred)", tier: 3, tierLabel: "Tier 3 — Specialized (Deferred)", isSupported: false },
  { type: "candlestick", label: "Candlestick (Deferred)", tier: 3, tierLabel: "Tier 3 — Specialized (Deferred)", isSupported: false },
];

const COLOR_SCHEMES = [
  { id: "analyzax_dark", label: "AnalyzaX Dark (Indigo/Cyan)" },
  { id: "analyzax_light", label: "AnalyzaX Clean" },
  { id: "ocean", label: "Ocean Breeze (Blue/Teal)" },
  { id: "emerald", label: "Emerald City (Green/Lime)" },
  { id: "sunset", label: "Sunset Glow (Orange/Rose)" },
  { id: "cyberpunk", label: "Cyberpunk Neon (Purple/Yellow)" },
  { id: "monochrome", label: "Monochrome Steel" },
];

export function ChartBuilder({
  spec,
  onChange,
  availableColumns,
  onPreview,
  isLoading,
}: ChartBuilderProps) {
  const updateSpec = (fields: Partial<ChartSpec>) => {
    onChange({ ...spec, ...fields });
  };

  const updateXAxis = (fields: Partial<NonNullable<ChartSpec["x_axis"]>>) => {
    onChange({
      ...spec,
      x_axis: {
        field: "",
        ...(spec.x_axis || {}),
        ...fields,
      },
    });
  };

  const updateYAxis = (fields: Partial<NonNullable<ChartSpec["y_axis"]>>) => {
    onChange({
      ...spec,
      y_axis: {
        field: "",
        ...(spec.y_axis || {}),
        ...fields,
      },
    });
  };

  const handleFiltersChange = (filters: StructuredFilter[]) => {
    onChange({ ...spec, filters });
  };

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface, #0f172a)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        padding: "1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <SlidersIcon size={18} className="text-brand" />
          <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
            Visual Studio / Chart Builder
          </h3>
        </div>

        <button
          onClick={onPreview}
          disabled={isLoading}
          className="btn btn-primary btn-sm"
          style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
        >
          <RefreshIcon size={14} className={isLoading ? "animate-spin" : ""} />
          {isLoading ? "Rendering..." : "Preview & Hydrate"}
        </button>
      </div>

      {/* Row 1: Chart Type & Title */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "1rem" }}>
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
            Chart Type
          </label>
          <select
            value={spec.chart_type}
            onChange={(e) => updateSpec({ chart_type: e.target.value as ChartType })}
            className="input"
            style={{ width: "100%", fontSize: "0.825rem" }}
          >
            {Object.entries(
              CHART_TYPES.reduce((acc, curr) => {
                acc[curr.tierLabel] = acc[curr.tierLabel] || [];
                acc[curr.tierLabel].push(curr);
                return acc;
              }, {} as Record<string, ChartTypeOption[]>)
            ).map(([tierLabel, types]) => (
              <optgroup key={tierLabel} label={tierLabel}>
                {types.map((t) => (
                  <option key={t.type} value={t.type} disabled={!t.isSupported}>
                    {t.label}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
            Chart Title
          </label>
          <input
            type="text"
            value={spec.title || ""}
            onChange={(e) => updateSpec({ title: e.target.value })}
            placeholder="e.g., Total Revenue by Product Category"
            className="input"
            style={{ width: "100%", fontSize: "0.825rem" }}
          />
        </div>
      </div>

      {/* Row 2: X-Axis & Y-Axis Configurations */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        {/* X-Axis */}
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.375rem",
            padding: "0.75rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.6rem",
          }}
        >
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-primary)" }}>
            X-Axis (Dimension / Independent)
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.7rem", color: "var(--text-secondary)", marginBottom: "0.2rem" }}>
              Field
            </label>
            <select
              value={spec.x_axis?.field || ""}
              onChange={(e) => updateXAxis({ field: e.target.value })}
              className="input input-sm"
              style={{ width: "100%", fontSize: "0.775rem" }}
            >
              <option value="">(Select X column)</option>
              {availableColumns.map((col) => (
                <option key={col.name} value={col.name}>
                  {col.name} {col.type ? `(${col.type})` : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.7rem", color: "var(--text-secondary)", marginBottom: "0.2rem" }}>
              Axis Type
            </label>
            <select
              value={spec.x_axis?.type || "category"}
              onChange={(e) => updateXAxis({ type: e.target.value as any })}
              className="input input-sm"
              style={{ width: "100%", fontSize: "0.775rem" }}
            >
              <option value="category">Category (Discrete)</option>
              <option value="value">Value (Continuous Numeric)</option>
              <option value="time">Time (Temporal)</option>
            </select>
          </div>
        </div>

        {/* Y-Axis */}
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.375rem",
            padding: "0.75rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.6rem",
          }}
        >
          <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Y-Axis (Measure / Dependent)
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.7rem", color: "var(--text-secondary)", marginBottom: "0.2rem" }}>
              Field
            </label>
            <select
              value={spec.y_axis?.field || ""}
              onChange={(e) => updateYAxis({ field: e.target.value })}
              className="input input-sm"
              style={{ width: "100%", fontSize: "0.775rem" }}
            >
              <option value="">(Select Y column)</option>
              {availableColumns.map((col) => (
                <option key={col.name} value={col.name}>
                  {col.name} {col.type ? `(${col.type})` : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.7rem", color: "var(--text-secondary)", marginBottom: "0.2rem" }}>
              Aggregation Function
            </label>
            <select
              value={spec.y_axis?.aggregation || "none"}
              onChange={(e) =>
                updateYAxis({
                  aggregation: e.target.value === "none" ? undefined : (e.target.value as any),
                })
              }
              className="input input-sm"
              style={{ width: "100%", fontSize: "0.775rem" }}
            >
              <option value="none">None (Raw Values)</option>
              <option value="SUM">SUM</option>
              <option value="AVG">AVG (Average)</option>
              <option value="MEDIAN">MEDIAN</option>
              <option value="MIN">MIN</option>
              <option value="MAX">MAX</option>
              <option value="COUNT">COUNT</option>
              <option value="DISTINCT">COUNT DISTINCT</option>
            </select>
          </div>
        </div>
      </div>

      {/* Row 3: Dimensions, Series & Color */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
            Series / Breakdown Column (Optional)
          </label>
          <select
            value={spec.series_field || ""}
            onChange={(e) => updateSpec({ series_field: e.target.value || undefined })}
            className="input input-sm"
            style={{ width: "100%", fontSize: "0.775rem" }}
          >
            <option value="">(None - Single Series)</option>
            {availableColumns.map((col) => (
              <option key={col.name} value={col.name}>
                {col.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
            Color Palette
          </label>
          <select
            value={spec.color_scheme || "analyzax_dark"}
            onChange={(e) => updateSpec({ color_scheme: e.target.value })}
            className="input input-sm"
            style={{ width: "100%", fontSize: "0.775rem" }}
          >
            {COLOR_SCHEMES.map((scheme) => (
              <option key={scheme.id} value={scheme.id}>
                {scheme.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
            Top-N Grouping
          </label>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem" }}>
            <label style={{ fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <input
                type="checkbox"
                checked={spec.top_n?.enabled || false}
                onChange={(e) =>
                  updateSpec({
                    top_n: {
                      enabled: e.target.checked,
                      n: spec.top_n?.n || 10,
                      include_other: spec.top_n?.include_other ?? true,
                    },
                  })
                }
              />
              Enable Top-N
            </label>
            {spec.top_n?.enabled && (
              <input
                type="number"
                min={2}
                max={50}
                value={spec.top_n.n}
                onChange={(e) =>
                  updateSpec({
                    top_n: {
                      ...spec.top_n!,
                      n: parseInt(e.target.value, 10) || 10,
                    },
                  })
                }
                className="input input-sm"
                style={{ width: "60px", fontSize: "0.75rem", padding: "0.2rem 0.4rem" }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Row 4: Filters */}
      <VisualizationFilters
        filters={spec.filters || []}
        onChange={handleFiltersChange}
        availableColumns={availableColumns}
      />
    </div>
  );
}
