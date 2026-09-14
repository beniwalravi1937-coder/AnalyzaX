"use client";

import React from "react";
import {
  EyeIcon,
  DownloadIcon,
  SaveIcon,
  BarChartIcon,
  RefreshIcon,
  TagIcon,
} from "@/components/icons";

interface ChartToolbarProps {
  viewMode: "chart" | "table";
  onToggleViewMode: () => void;
  onToggleInspector: () => void;
  isInspectorOpen: boolean;
  onFullscreen?: () => void;
  onExportPng?: () => void;
  onExportCsv?: () => void;
  onSave?: () => void;
  isSaving?: boolean;
}

export function ChartToolbar({
  viewMode,
  onToggleViewMode,
  onToggleInspector,
  isInspectorOpen,
  onFullscreen,
  onExportPng,
  onExportCsv,
  onSave,
  isSaving,
}: ChartToolbarProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0.5rem 0.75rem",
        borderBottom: "1px solid var(--border-subtle)",
        backgroundColor: "rgba(15, 23, 42, 0.4)",
        gap: "0.5rem",
        flexWrap: "wrap",
      }}
    >
      {/* Left controls: View toggles */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
        <button
          onClick={onToggleViewMode}
          className="btn btn-secondary btn-sm"
          style={{
            fontSize: "0.75rem",
            padding: "0.25rem 0.6rem",
            display: "flex",
            alignItems: "center",
            gap: "0.3rem",
          }}
          title={viewMode === "chart" ? "View underlying data table" : "View chart visualization"}
        >
          <BarChartIcon size={14} />
          {viewMode === "chart" ? "View Data" : "View Chart"}
        </button>

        <button
          onClick={onToggleInspector}
          className={`btn btn-secondary btn-sm ${isInspectorOpen ? "active" : ""}`}
          style={{
            fontSize: "0.75rem",
            padding: "0.25rem 0.6rem",
            display: "flex",
            alignItems: "center",
            gap: "0.3rem",
            borderColor: isInspectorOpen ? "var(--brand-primary, #6366f1)" : undefined,
          }}
          title="Inspect ChartSpec and Provenance metadata"
        >
          <EyeIcon size={14} />
          Inspector
        </button>
      </div>

      {/* Right controls: Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
        {onExportCsv && (
          <button
            onClick={onExportCsv}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            title="Export data as CSV"
          >
            <DownloadIcon size={13} />
            CSV
          </button>
        )}

        {onExportPng && (
          <button
            onClick={onExportPng}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            title="Export chart as PNG image"
          >
            <DownloadIcon size={13} />
            PNG
          </button>
        )}

        {onFullscreen && (
          <button
            onClick={onFullscreen}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            title="Expand Fullscreen"
          >
            ⛶
          </button>
        )}

        {onSave && (
          <button
            onClick={onSave}
            disabled={isSaving}
            className="btn btn-primary btn-sm"
            style={{
              fontSize: "0.75rem",
              padding: "0.25rem 0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
            }}
          >
            <SaveIcon size={13} />
            {isSaving ? "Saving..." : "Save Chart"}
          </button>
        )}
      </div>
    </div>
  );
}
