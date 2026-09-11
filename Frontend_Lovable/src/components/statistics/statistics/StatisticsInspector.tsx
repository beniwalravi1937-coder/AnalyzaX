"use client";

import React from "react";
import { StatisticalResult } from "@/types/statistics";

interface StatisticsInspectorProps {
  result: StatisticalResult;
  isOpen: boolean;
  onClose: () => void;
}

export const StatisticsInspector: React.FC<StatisticsInspectorProps> = ({ result, isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        bottom: 0,
        width: "480px",
        maxWidth: "90vw",
        background: "var(--bg-canvas, #0f172a)",
        borderLeft: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.1))",
        boxShadow: "-4px 0 24px rgba(0, 0, 0, 0.4)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "1.25rem",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 700 }}>Provenance & Reproducibility</h3>
        <button type="button" onClick={onClose} className="btn btn-xs btn-secondary">
          Close
        </button>
      </div>

      {/* Content */}
      <div style={{ padding: "1.25rem", overflowY: "auto", display: "flex", flexDirection: "column", gap: "1.25rem", fontSize: "0.8125rem" }}>
        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "0.25rem" }}>Analysis ID</div>
          <div style={{ fontFamily: "monospace", wordBreak: "break-all" }}>{result.result_id}</div>
        </div>

        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "0.25rem" }}>Dataset & Version Provenance</div>
          <div style={{ fontWeight: 600 }}>{result.dataset_id}</div>
          <div style={{ color: "var(--primary)", fontWeight: 600 }}>Version: {result.dataset_version_id}</div>
        </div>

        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "0.25rem" }}>Execution Engine & Libraries</div>
          <div>Engine Version: <strong>v{result.provenance?.statistics_engine_version || "10.0.0"}</strong></div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>
            Deterministic stack: SciPy, statsmodels, NumPy, Polars
          </div>
        </div>

        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "0.25rem" }}>Missing-Data Accounting</div>
          <div>Original observations: <strong>{result.missing_data_report?.original_observations}</strong></div>
          <div>Used in calculation: <strong>{result.missing_data_report?.used_observations}</strong></div>
          <div>Excluded: <strong>{result.missing_data_report?.excluded_observations}</strong></div>
          <div>Policy: <strong>{result.missing_data_report?.missing_policy}</strong></div>
          {result.missing_data_report?.exclusion_reason && (
            <div style={{ fontStyle: "italic", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              Reason: {result.missing_data_report.exclusion_reason}
            </div>
          )}
        </div>

        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "0.25rem" }}>Raw Parameters</div>
          <pre
            style={{
              padding: "0.75rem",
              borderRadius: "6px",
              background: "rgba(0, 0, 0, 0.3)",
              border: "1px solid var(--border-subtle)",
              overflowX: "auto",
              fontSize: "0.75rem",
            }}
          >
            {JSON.stringify(result.parameters, null, 2)}
          </pre>
        </div>

        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: "0.25rem" }}>Limitations & Caution</div>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            {result.limitations?.map((lim, idx) => (
              <li key={idx}>{lim}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
