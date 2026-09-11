"use client";

import React from "react";
import { MLExperiment } from "@/types/ml";

interface MLExperimentHistoryProps {
  experiments: MLExperiment[];
  onSelectExperiment: (experimentId: string) => void;
  isLoading: boolean;
}

export const MLExperimentHistory: React.FC<MLExperimentHistoryProps> = ({
  experiments,
  onSelectExperiment,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
        <span className="spinner" style={{ marginRight: "0.5rem" }} />
        Loading experiment history...
      </div>
    );
  }

  if (!experiments || experiments.length === 0) {
    return (
      <div
        style={{
          padding: "2.5rem",
          textAlign: "center",
          color: "var(--text-muted)",
          fontSize: "0.875rem",
          borderRadius: "8px",
          border: "1px dashed var(--border-subtle)",
        }}
      >
        No ML experiments recorded yet for this dataset.
      </div>
    );
  }

  return (
    <div
      style={{
        borderRadius: "8px",
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        overflow: "hidden",
      }}
    >
      <div style={{ padding: "0.875rem 1rem", borderBottom: "1px solid var(--border-subtle)" }}>
        <h4 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600 }}>
          Experiment History ({experiments.length})
        </h4>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "var(--bg-subtle)", borderBottom: "1px solid var(--border-subtle)" }}>
              <th style={{ padding: "0.625rem 1rem" }}>Experiment ID</th>
              <th style={{ padding: "0.625rem 1rem" }}>Version</th>
              <th style={{ padding: "0.625rem 1rem" }}>Task</th>
              <th style={{ padding: "0.625rem 1rem" }}>Target</th>
              <th style={{ padding: "0.625rem 1rem" }}>Models</th>
              <th style={{ padding: "0.625rem 1rem" }}>Status</th>
              <th style={{ padding: "0.625rem 1rem" }}>Created</th>
              <th style={{ padding: "0.625rem 1rem", textAlign: "right" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {experiments.map((exp) => (
              <tr
                key={exp.experiment_id}
                style={{
                  borderBottom: "1px solid var(--border-subtle)",
                  transition: "background 0.15s ease",
                }}
              >
                <td style={{ padding: "0.75rem 1rem", fontFamily: "monospace", fontWeight: 600 }}>
                  {exp.experiment_id}
                </td>
                <td style={{ padding: "0.75rem 1rem" }}>
                  <span className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>
                    {exp.dataset_version_id}
                  </span>
                </td>
                <td style={{ padding: "0.75rem 1rem", textTransform: "capitalize" }}>
                  {exp.task_type.replace("_", " ")}
                </td>
                <td style={{ padding: "0.75rem 1rem" }}>
                  {exp.target_column ? <strong>{exp.target_column}</strong> : <span style={{ color: "var(--text-muted)" }}>None</span>}
                </td>
                <td style={{ padding: "0.75rem 1rem", color: "var(--text-secondary)" }}>
                  {exp.models.length} model(s)
                </td>
                <td style={{ padding: "0.75rem 1rem" }}>
                  <span
                    className={`badge ${
                      exp.status === "COMPLETED"
                        ? "badge-success"
                        : exp.status === "FAILED"
                        ? "badge-error"
                        : exp.status === "RUNNING"
                        ? "badge-info"
                        : "badge-neutral"
                    }`}
                    style={{ fontSize: "0.6875rem" }}
                  >
                    {exp.status}
                  </span>
                </td>
                <td style={{ padding: "0.75rem 1rem", color: "var(--text-muted)", fontSize: "0.75rem" }}>
                  {new Date(exp.created_at).toLocaleString()}
                </td>
                <td style={{ padding: "0.75rem 1rem", textAlign: "right" }}>
                  <button
                    type="button"
                    onClick={() => onSelectExperiment(exp.experiment_id)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: "0.6875rem" }}
                  >
                    Load Results
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
