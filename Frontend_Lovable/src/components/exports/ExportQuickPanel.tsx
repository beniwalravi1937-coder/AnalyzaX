"use client";

import React, { useState } from "react";
import {
  ExportFormat,
  ExportSourceType,
  SOURCE_TYPE_LABELS,
  FORMAT_LABELS,
  TABULAR_FORMATS,
  ExportJob,
} from "@/types/exports";
import { createExport, downloadExport } from "@/services/exportApi";

interface ExportQuickPanelProps {
  datasetId: string;
  versionId?: string;
}

const SOURCE_OPTIONS: { type: ExportSourceType; icon: string }[] = [
  { type: "DATASET", icon: "📊" },
  { type: "SQL_RESULT", icon: "🔍" },
  { type: "PROFILE", icon: "📋" },
  { type: "QUALITY_REPORT", icon: "✅" },
  { type: "EDA_RESULT", icon: "🔬" },
  { type: "STATISTICS_RESULT", icon: "📈" },
  { type: "ML_RESULT", icon: "🤖" },
  { type: "FORECAST_RESULT", icon: "📉" },
  { type: "DASHBOARD", icon: "🖥️" },
  { type: "AI_ANALYST_SESSION", icon: "💡" },
];

export function ExportQuickPanel({ datasetId, versionId }: ExportQuickPanelProps) {
  const [selectedSource, setSelectedSource] = useState<ExportSourceType>("DATASET");
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("CSV");
  const [isExporting, setIsExporting] = useState(false);
  const [result, setResult] = useState<ExportJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    setResult(null);

    try {
      const job = await createExport({
        dataset_id: datasetId,
        version_id: versionId,
        source_type: selectedSource,
        format: selectedFormat,
      });

      setResult(job);

      if (job.status === "COMPLETED") {
        await downloadExport(job.job_id);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Export failed";
      setError(message);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Source Type Selector */}
      <div>
        <label
          style={{
            display: "block",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--text-muted)",
            marginBottom: "0.5rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Export Source
        </label>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
            gap: "0.5rem",
          }}
        >
          {SOURCE_OPTIONS.map(({ type, icon }) => (
            <button
              key={type}
              type="button"
              onClick={() => setSelectedSource(type)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.625rem 0.75rem",
                borderRadius: "6px",
                border: `1px solid ${selectedSource === type ? "var(--primary)" : "var(--border-subtle)"}`,
                background: selectedSource === type ? "rgba(99, 102, 241, 0.1)" : "var(--bg-secondary)",
                color: selectedSource === type ? "var(--primary)" : "var(--text-primary)",
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                textAlign: "left",
              }}
            >
              <span style={{ fontSize: "1rem" }}>{icon}</span>
              <span>{SOURCE_TYPE_LABELS[type]}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Format Selector */}
      <div>
        <label
          style={{
            display: "block",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--text-muted)",
            marginBottom: "0.5rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Output Format
        </label>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {TABULAR_FORMATS.map((fmt) => (
            <button
              key={fmt}
              type="button"
              onClick={() => setSelectedFormat(fmt)}
              className={`btn btn-sm ${selectedFormat === fmt ? "btn-primary" : "btn-secondary"}`}
              style={{ minWidth: "80px" }}
            >
              {FORMAT_LABELS[fmt]}
            </button>
          ))}
        </div>
      </div>

      {/* Export Button */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleExport}
          disabled={isExporting}
          style={{ minWidth: "140px" }}
        >
          {isExporting ? (
            <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span
                style={{
                  width: "14px",
                  height: "14px",
                  border: "2px solid rgba(255,255,255,0.3)",
                  borderTopColor: "white",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              Exporting...
            </span>
          ) : (
            <>⬇ Export Now</>
          )}
        </button>

        {result && result.status === "COMPLETED" && (
          <span
            style={{
              fontSize: "0.8125rem",
              color: "var(--success)",
              display: "flex",
              alignItems: "center",
              gap: "0.375rem",
            }}
          >
            ✓ Exported ({((result.file_size_bytes || 0) / 1024).toFixed(1)} KB,{" "}
            {result.row_count ?? 0} rows)
          </span>
        )}

        {result && result.status === "FAILED" && (
          <span style={{ fontSize: "0.8125rem", color: "var(--danger)" }}>
            ✕ {result.error_message || "Export failed"}
          </span>
        )}

        {error && (
          <span style={{ fontSize: "0.8125rem", color: "var(--danger)" }}>
            ✕ {error}
          </span>
        )}
      </div>

      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
