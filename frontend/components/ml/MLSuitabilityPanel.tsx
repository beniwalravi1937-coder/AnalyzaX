"use client";

import React from "react";
import { SuitabilityReport, SuitabilitySeverity } from "@/types/ml";

interface MLSuitabilityPanelProps {
  report: SuitabilityReport | null;
  isLoading: boolean;
  onRefresh: () => void;
}

export const MLSuitabilityPanel: React.FC<MLSuitabilityPanelProps> = ({
  report,
  isLoading,
  onRefresh,
}) => {
  if (isLoading) {
    return (
      <div
        style={{
          padding: "1rem",
          borderRadius: "8px",
          background: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          color: "var(--text-secondary)",
          fontSize: "0.875rem",
        }}
      >
        <span className="spinner" style={{ marginRight: "0.5rem" }} />
        Evaluating dataset ML suitability and scanning for data leakage...
      </div>
    );
  }

  if (!report) {
    return (
      <div
        style={{
          padding: "1rem",
          borderRadius: "8px",
          background: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          color: "var(--text-secondary)",
          fontSize: "0.875rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span>No suitability scan performed yet.</span>
        <button type="button" onClick={onRefresh} className="btn btn-secondary btn-sm">
          Run Suitability Check
        </button>
      </div>
    );
  }

  const getSeverityBadge = (severity: SuitabilitySeverity) => {
    switch (severity) {
      case "CRITICAL":
        return <span className="badge badge-error">CRITICAL</span>;
      case "HIGH":
        return <span className="badge badge-warning" style={{ background: "#f59e0b22", color: "#f59e0b" }}>HIGH</span>;
      case "MEDIUM":
        return <span className="badge badge-warning">MEDIUM</span>;
      case "LOW":
        return <span className="badge badge-info">LOW</span>;
      case "INFO":
      default:
        return <span className="badge badge-neutral">INFO</span>;
    }
  };

  return (
    <div
      style={{
        borderRadius: "8px",
        background: "var(--bg-surface)",
        border: `1px solid ${report.is_suitable ? "var(--border-subtle)" : "var(--error-border, #ef444455)"}`,
        padding: "1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span
              style={{
                display: "inline-block",
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                background: report.is_suitable ? "var(--color-success, #10b981)" : "var(--color-error, #ef4444)",
              }}
            />
            <h4 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600 }}>
              {report.is_suitable ? "Dataset Ready for Machine Learning" : "Suitability Warning: Action Recommended"}
            </h4>
          </div>
          <p style={{ margin: "0.25rem 0 0 1.25rem", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            {report.summary}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {report.dataset_row_count.toLocaleString()} rows · {report.dataset_col_count} cols
          </span>
          <button type="button" onClick={onRefresh} className="btn btn-secondary btn-sm" style={{ fontSize: "0.75rem" }}>
            Re-check
          </button>
        </div>
      </div>

      {/* Recommended Task & Imbalance Stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
          padding: "0.75rem",
          borderRadius: "6px",
          background: "var(--bg-subtle)",
          fontSize: "0.8125rem",
        }}
      >
        <div>
          <span style={{ color: "var(--text-muted)", display: "block" }}>Recommended Task:</span>
          <strong style={{ textTransform: "capitalize" }}>{report.recommended_task?.replace("_", " ") || "Not specified"}</strong>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)", display: "block" }}>Candidate Target:</span>
          <strong>{report.recommended_target || "None (Clustering)"}</strong>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)", display: "block" }}>Usable Features:</span>
          <strong>{report.recommended_features.length} recommended ({Object.keys(report.excluded_features).length} excluded)</strong>
        </div>
        {report.imbalance_ratio !== undefined && report.imbalance_ratio !== null && (
          <div>
            <span style={{ color: "var(--text-muted)", display: "block" }}>Class Imbalance Ratio:</span>
            <strong>{(report.imbalance_ratio * 100).toFixed(1)}% (minority/majority)</strong>
          </div>
        )}
      </div>

      {/* Issues List */}
      {report.issues.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Diagnostic Findings ({report.issues.length})
          </span>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "240px", overflowY: "auto" }}>
            {report.issues.map((issue, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.75rem",
                  padding: "0.625rem 0.75rem",
                  borderRadius: "6px",
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-subtle)",
                  fontSize: "0.8125rem",
                }}
              >
                <div>{getSeverityBadge(issue.severity)}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                    {issue.title} {issue.column && <code style={{ fontSize: "0.75rem", color: "var(--color-indigo)" }}>[{issue.column}]</code>}
                  </div>
                  <div style={{ color: "var(--text-secondary)", marginTop: "0.125rem" }}>{issue.message}</div>
                  {issue.action_recommendation && (
                    <div style={{ color: "var(--text-muted)", marginTop: "0.25rem", fontStyle: "italic", fontSize: "0.75rem" }}>
                      Recommendation: {issue.action_recommendation}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
