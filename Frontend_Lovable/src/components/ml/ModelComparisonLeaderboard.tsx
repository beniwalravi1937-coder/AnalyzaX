"use client";

import React from "react";
import { MLModelRun } from "@/types/ml";

interface ModelComparisonLeaderboardProps {
  modelRuns: MLModelRun[];
  bestModelRunId?: string;
  primaryMetric: string;
  selectedRunId: string;
  onSelectRunId: (runId: string) => void;
}

export const ModelComparisonLeaderboard: React.FC<ModelComparisonLeaderboardProps> = ({
  modelRuns,
  bestModelRunId,
  primaryMetric,
  selectedRunId,
  onSelectRunId,
}) => {
  return (
    <div
      style={{
        borderRadius: "8px",
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: "0.875rem 1rem",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <h4 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600 }}>
            Model Comparison Leaderboard
          </h4>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Models evaluated on the same split and ranked by primary metric: <strong>{primaryMetric.toUpperCase()}</strong>
          </span>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "var(--bg-subtle)", borderBottom: "1px solid var(--border-subtle)" }}>
              <th style={{ padding: "0.625rem 1rem" }}>Model</th>
              <th style={{ padding: "0.625rem 1rem" }}>Validation ({primaryMetric})</th>
              <th style={{ padding: "0.625rem 1rem" }}>Test Score</th>
              <th style={{ padding: "0.625rem 1rem" }}>CV Mean ± Std</th>
              <th style={{ padding: "0.625rem 1rem" }}>vs. Baseline</th>
              <th style={{ padding: "0.625rem 1rem" }}>Train Time</th>
              <th style={{ padding: "0.625rem 1rem", textAlign: "right" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {modelRuns.map((run) => {
              const isBest = run.model_run_id === bestModelRunId;
              const isSelected = run.model_run_id === selectedRunId;
              const isBaseline = run.model_id.startsWith("dummy");
              const valMetric = run.metrics ? run.metrics[primaryMetric] : null;
              const testMetric = run.test_metrics ? run.test_metrics[primaryMetric] : null;

              return (
                <tr
                  key={run.model_run_id}
                  onClick={() => onSelectRunId(run.model_run_id)}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    background: isSelected ? "var(--bg-active, #6366f112)" : "transparent",
                    cursor: "pointer",
                    transition: "background 0.15s ease",
                  }}
                >
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <strong style={{ color: isSelected ? "var(--color-primary, #6366f1)" : "var(--text-primary)" }}>
                        {run.model_name}
                      </strong>
                      {isBest && <span className="badge badge-success" style={{ fontSize: "0.6875rem" }}>Top Rank</span>}
                      {isBaseline && <span className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>Baseline</span>}
                    </div>
                  </td>

                  <td style={{ padding: "0.75rem 1rem", fontWeight: 600, fontFamily: "monospace" }}>
                    {valMetric !== null && valMetric !== undefined ? String(valMetric) : "—"}
                  </td>

                  <td style={{ padding: "0.75rem 1rem", fontFamily: "monospace", color: "var(--text-secondary)" }}>
                    {testMetric !== null && testMetric !== undefined ? String(testMetric) : "—"}
                  </td>

                  <td style={{ padding: "0.75rem 1rem", fontFamily: "monospace", color: "var(--text-secondary)" }}>
                    {run.cv_metrics ? `${run.cv_metrics.mean} ± ${run.cv_metrics.std}` : "—"}
                  </td>

                  <td style={{ padding: "0.75rem 1rem" }}>
                    {run.baseline_comparison ? (
                      <span
                        style={{
                          color: run.baseline_comparison.outperforms_baseline ? "var(--color-success, #10b981)" : "var(--text-muted)",
                          fontWeight: 500,
                          fontSize: "0.75rem",
                        }}
                      >
                        {run.baseline_comparison.delta > 0 ? `+${run.baseline_comparison.delta}` : run.baseline_comparison.delta}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>

                  <td style={{ padding: "0.75rem 1rem", color: "var(--text-muted)", fontSize: "0.75rem" }}>
                    {run.duration_ms} ms
                  </td>

                  <td style={{ padding: "0.75rem 1rem", textAlign: "right" }}>
                    <button
                      type="button"
                      className={`btn btn-sm ${isSelected ? "btn-primary" : "btn-secondary"}`}
                      style={{ fontSize: "0.6875rem" }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRunId(run.model_run_id);
                      }}
                    >
                      {isSelected ? "Selected" : "Inspect"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
