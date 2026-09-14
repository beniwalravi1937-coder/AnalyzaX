"use client";

import React, { useState } from "react";
import { ChartSpec, VisualizationEvent } from "@/types";
import { ChartRenderer } from "./ChartRenderer";
import { ChartToolbar } from "./ChartToolbar";
import { ChartInspector } from "./ChartInspector";
import { DataPointDetails } from "./DataPointDetails";
import { FullscreenChart } from "./FullscreenChart";
import { ChartLoadingState } from "./ChartLoadingState";
import { ChartErrorState } from "./ChartErrorState";
import { ChartEmptyState } from "./ChartEmptyState";

interface ChartContainerProps {
  spec: ChartSpec;
  data: Record<string, any>[];
  isLoading?: boolean;
  error?: string | null;
  warnings?: string[];
  onSave?: () => void;
  isSaving?: boolean;
  onFilterByValue?: (field: string, value: any) => void;
  height?: string | number;
  className?: string;
}

export function ChartContainer({
  spec,
  data,
  isLoading,
  error,
  warnings,
  onSave,
  isSaving,
  onFilterByValue,
  height = 420,
  className = "",
}: ChartContainerProps) {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedPoint, setSelectedPoint] = useState<{
    name?: string;
    value?: any;
    seriesName?: string;
    dataIndex?: number;
    raw?: any;
  } | null>(null);

  // Handle point clicks
  const handlePointClick = (event: {
    name?: string;
    value?: any;
    seriesName?: string;
    dataIndex?: number;
    raw?: any;
  }) => {
    setSelectedPoint({
      name: event.name,
      value: event.value,
      seriesName: event.seriesName,
      dataIndex: event.dataIndex,
      raw: event.raw,
    });
  };

  // CSV Export utility
  const handleExportCsv = () => {
    if (!data || data.length === 0) return;
    const headers = Object.keys(data[0]);
    const csvRows: string[] = [];
    csvRows.push(headers.join(","));

    for (const row of data) {
      const values = headers.map((header) => {
        const val = row[header];
        if (val === null || val === undefined) return "";
        const escaped = String(val).replace(/"/g, '""');
        return `"${escaped}"`;
      });
      csvRows.push(values.join(","));
    }

    const csvContent = csvRows.join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `${(spec.title || "visualization").toLowerCase().replace(/[^a-z0-9]/g, "_")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // PNG Export utility
  const handleExportPng = () => {
    const canvas = document.querySelector(".analyzax-chart-canvas canvas") as HTMLCanvasElement;
    if (canvas) {
      const url = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.download = `${(spec.title || "visualization").toLowerCase().replace(/[^a-z0-9]/g, "_")}.png`;
      link.href = url;
      link.click();
    }
  };

  // Extract columns for table view
  const tableColumns = data.length > 0 ? Object.keys(data[0]) : [];

  return (
    <div
      className={`card ${className}`}
      style={{
        display: "flex",
        flexDirection: "column",
        backgroundColor: "var(--bg-surface, #0f172a)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Title & Badges Header */}
      <div
        style={{
          padding: "0.75rem 1rem 0.5rem 1rem",
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "1rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              {spec.title || "Visualization"}
            </h3>
            <span
              style={{
                fontSize: "0.65rem",
                padding: "0.15rem 0.45rem",
                borderRadius: "0.25rem",
                backgroundColor: "rgba(99, 102, 241, 0.15)",
                color: "var(--brand-primary, #6366f1)",
                textTransform: "uppercase",
                fontWeight: 600,
                letterSpacing: "0.025em",
              }}
            >
              {spec.chart_type}
            </span>
            {spec.sampling?.is_sampled && (
              <span
                style={{
                  fontSize: "0.65rem",
                  padding: "0.15rem 0.45rem",
                  borderRadius: "0.25rem",
                  backgroundColor: "rgba(245, 158, 11, 0.15)",
                  color: "var(--status-warning, #f59e0b)",
                  fontWeight: 600,
                }}
                title={`Sampled: ${spec.sampling.sample_size} of ${spec.sampling.original_row_count} rows`}
              >
                ⚡ Sampled ({spec.sampling.sample_size?.toLocaleString()} rows)
              </span>
            )}
            {spec.top_n?.enabled && (
              <span
                style={{
                  fontSize: "0.65rem",
                  padding: "0.15rem 0.45rem",
                  borderRadius: "0.25rem",
                  backgroundColor: "rgba(16, 185, 129, 0.15)",
                  color: "var(--status-success, #10b981)",
                  fontWeight: 600,
                }}
              >
                Top {spec.top_n.n} + Other
              </span>
            )}
          </div>
          {spec.subtitle && (
            <div style={{ fontSize: "0.775rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
              {spec.subtitle}
            </div>
          )}
        </div>

        {/* Toolbar */}
        <ChartToolbar
          viewMode={viewMode}
          onToggleViewMode={() => setViewMode(viewMode === "chart" ? "table" : "chart")}
          onToggleInspector={() => setIsInspectorOpen(!isInspectorOpen)}
          isInspectorOpen={isInspectorOpen}
          onFullscreen={() => setIsFullscreen(true)}
          onExportPng={handleExportPng}
          onExportCsv={handleExportCsv}
          onSave={onSave}
          isSaving={isSaving}
        />
      </div>

      {/* Main Content Area */}
      <div style={{ position: "relative", flex: 1, minHeight: typeof height === "number" ? `${height}px` : height }}>
        {isLoading ? (
          <ChartLoadingState height={height} />
        ) : error ? (
          <ChartErrorState error={error} warnings={warnings} height={height} />
        ) : data.length === 0 ? (
          <ChartEmptyState height={height} />
        ) : viewMode === "table" ? (
          /* Tabular Data View (Accessibility & Raw Check) */
          <div
            style={{
              height: typeof height === "number" ? `${height}px` : height,
              overflow: "auto",
              padding: "0.5rem 1rem",
              backgroundColor: "rgba(10, 15, 29, 0.5)",
            }}
          >
            <table
              className="table"
              style={{
                width: "100%",
                fontSize: "0.775rem",
                borderCollapse: "collapse",
                textAlign: "left",
              }}
            >
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  {tableColumns.map((col) => (
                    <th
                      key={col}
                      style={{
                        padding: "0.5rem 0.75rem",
                        color: "var(--text-secondary)",
                        fontWeight: 600,
                        position: "sticky",
                        top: 0,
                        backgroundColor: "var(--bg-surface, #0f172a)",
                      }}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    style={{
                      borderBottom: "1px solid rgba(255,255,255,0.05)",
                    }}
                  >
                    {tableColumns.map((col) => (
                      <td key={col} style={{ padding: "0.4rem 0.75rem", color: "var(--text-primary)" }}>
                        {row[col] !== null && row[col] !== undefined ? String(row[col]) : "null"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* ECharts Canvas Renderer */
          <div className="analyzax-chart-canvas" style={{ width: "100%", height: "100%" }}>
            <ChartRenderer
              spec={spec}
              data={data}
              height={height}
              onPointClick={handlePointClick}
            />
          </div>
        )}
      </div>

      {/* Point details drawer when clicked */}
      <DataPointDetails
        dataPoint={selectedPoint}
        onClose={() => setSelectedPoint(null)}
        onFilterByValue={onFilterByValue}
        xField={spec.x_axis?.field}
      />

      {/* Chart Inspector Panel */}
      <ChartInspector
        spec={spec}
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
      />

      {/* Fullscreen View Modal */}
      <FullscreenChart
        isOpen={isFullscreen}
        onClose={() => setIsFullscreen(false)}
        spec={spec}
        data={data}
        onPointClick={handlePointClick}
      />
    </div>
  );
}
