"use client";

import React from "react";
import { StatisticalResult } from "@/types/statistics";

interface StatisticsSummaryProps {
  result: StatisticalResult;
  onOpenInspector: () => void;
}

export const StatisticsSummary: React.FC<StatisticsSummaryProps> = ({ result, onOpenInspector }) => {
  const interp = result.interpretation || {};
  const rawP = result.p_values?.primary ?? result.statistics?.p_value;
  const primaryP = typeof rawP === "number" ? rawP : null;
  const rawStat = result.statistics?.statistic ?? result.statistics?.f_statistic;
  const statVal = typeof rawStat === "number" ? rawStat : null;
  const statName = typeof result.statistics?.test_statistic_name === "string" ? result.statistics.test_statistic_name : "Statistic";
  const alpha = typeof result.parameters?.alpha === "number" ? result.parameters.alpha : 0.05;

  const isSignificant = primaryP != null ? primaryP < alpha : null;

  return (
    <div
      style={{
        padding: "1.25rem",
        borderRadius: "var(--radius-md, 8px)",
        background: "var(--bg-surface, rgba(255, 255, 255, 0.02))",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
            Statistical Inference Summary
          </div>
          <h3 style={{ margin: "0.25rem 0", fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {result.method.replace(/_/g, " ").toUpperCase()}
          </h3>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          {isSignificant !== null && (
            <span
              style={{
                fontSize: "0.75rem",
                padding: "0.25rem 0.6rem",
                borderRadius: "4px",
                background: isSignificant ? "rgba(16, 185, 129, 0.15)" : "rgba(156, 163, 175, 0.15)",
                color: isSignificant ? "#10b981" : "#9ca3af",
                fontWeight: 700,
                border: `1px solid ${isSignificant ? "rgba(16, 185, 129, 0.3)" : "rgba(156, 163, 175, 0.3)"}`,
              }}
            >
              {isSignificant ? "Significant (Reject H₀)" : "Inconclusive (Fail to Reject H₀)"}
            </span>
          )}
          <button type="button" onClick={onOpenInspector} className="btn btn-xs btn-secondary">
            Inspect Provenance
          </button>
        </div>
      </div>

      {/* Main Narrative Card */}
      <div
        style={{
          padding: "1rem",
          borderRadius: "6px",
          background: "var(--bg-subtle, rgba(255, 255, 255, 0.03))",
          fontSize: "0.875rem",
          lineHeight: 1.6,
          color: "var(--text-secondary)",
        }}
      >
        <p style={{ margin: "0 0 0.5rem 0" }}>
          <strong>Observation:</strong> {interp.observed_summary || "Calculations completed."}
        </p>
        {interp.effect_magnitude && (
          <p style={{ margin: "0 0 0.5rem 0" }}>
            <strong>Magnitude:</strong> {interp.effect_magnitude}
          </p>
        )}
        {interp.assumptions_impact && (
          <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            <strong>Diagnostics:</strong> {interp.assumptions_impact}
          </p>
        )}
        {interp.causality_caveat && (
          <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
            {interp.causality_caveat}
          </p>
        )}
      </div>

      {/* Key Numbers Bar */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1.5rem", fontSize: "0.8125rem" }}>
        {statVal != null && (
          <div>
            <span style={{ color: "var(--text-muted)" }}>{statName}: </span>
            <strong style={{ fontFamily: "monospace", fontSize: "0.9375rem" }}>{Number(statVal).toFixed(4)}</strong>
          </div>
        )}
        {primaryP != null && (
          <div>
            <span style={{ color: "var(--text-muted)" }}>p-value: </span>
            <strong style={{ fontFamily: "monospace", fontSize: "0.9375rem", color: isSignificant ? "var(--primary)" : "inherit" }}>
              {primaryP < 0.0001 ? "< 0.0001" : primaryP.toFixed(4)}
            </strong>
          </div>
        )}
        <div>
          <span style={{ color: "var(--text-muted)" }}>Alpha (α): </span>
          <strong style={{ fontFamily: "monospace" }}>{alpha}</strong>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)" }}>Sample Analyzed: </span>
          <strong>{result.missing_data_report?.used_observations ?? "-"}</strong>
          {result.missing_data_report?.excluded_observations ? (
            <span style={{ color: "var(--text-muted)", marginLeft: "0.25rem" }}>
              ({result.missing_data_report.excluded_observations} excluded)
            </span>
          ) : null}
        </div>
      </div>
    </div>
  );
};
