"use client";

import React from "react";
import { MLTaskType } from "@/types/ml";

interface TaskTargetSelectorProps {
  taskType: MLTaskType;
  onTaskTypeChange: (task: MLTaskType) => void;
  targetColumn: string;
  onTargetColumnChange: (target: string) => void;
  columns: string[];
  recommendedTask?: MLTaskType;
  recommendedTarget?: string;
  classDistribution?: Record<string, number>;
}

const TASK_OPTIONS: Array<{ type: MLTaskType; label: string; desc: string }> = [
  {
    type: "regression",
    label: "Regression",
    desc: "Predict continuous numerical quantities (e.g. price, duration, sales, score).",
  },
  {
    type: "binary_classification",
    label: "Binary Classification",
    desc: "Predict two discrete outcomes (e.g. churn yes/no, fraud, pass/fail).",
  },
  {
    type: "multiclass_classification",
    label: "Multiclass Classification",
    desc: "Predict one category among three or more discrete classes.",
  },
  {
    type: "clustering",
    label: "Unsupervised Clustering",
    desc: "Partition observations into homogeneous clusters without a predefined target.",
  },
];

export const TaskTargetSelector: React.FC<TaskTargetSelectorProps> = ({
  taskType,
  onTaskTypeChange,
  targetColumn,
  onTargetColumnChange,
  columns,
  recommendedTask,
  recommendedTarget,
  classDistribution,
}) => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Task Type Cards */}
      <div>
        <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.5rem" }}>
          1. Select Machine Learning Task
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.75rem" }}>
          {TASK_OPTIONS.map((opt) => {
            const isSelected = taskType === opt.type;
            const isRec = recommendedTask === opt.type;
            return (
              <div
                key={opt.type}
                onClick={() => onTaskTypeChange(opt.type)}
                style={{
                  padding: "0.875rem",
                  borderRadius: "8px",
                  cursor: "pointer",
                  border: isSelected ? "2px solid var(--color-primary, #6366f1)" : "1px solid var(--border-subtle)",
                  background: isSelected ? "var(--bg-active, #6366f112)" : "var(--bg-surface)",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                  <span style={{ fontWeight: 600, fontSize: "0.875rem", color: isSelected ? "var(--color-primary, #6366f1)" : "var(--text-primary)" }}>
                    {opt.label}
                  </span>
                  {isRec && <span className="badge badge-info" style={{ fontSize: "0.6875rem" }}>Recommended</span>}
                </div>
                <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.35 }}>
                  {opt.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Target Column Selection (for supervised tasks) */}
      {taskType !== "clustering" ? (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.375rem" }}>
            <label htmlFor="ml-target-column-select" style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary, #f1f5f9)" }}>
              2. Prediction Target Column <span style={{ color: "var(--color-error, #ef4444)" }}>*</span>
            </label>
            {recommendedTarget && (
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted, #94a3b8)" }}>
                Auto-detected candidate: <strong style={{ color: "var(--color-primary, #818cf8)" }}>{recommendedTarget}</strong>
              </span>
            )}
          </div>

          <select
            id="ml-target-column-select"
            aria-label="Select Target Variable"
            value={targetColumn}
            onChange={(e) => onTargetColumnChange(e.target.value)}
            className="input"
            style={{ width: "100%", padding: "0.5rem 0.75rem", fontSize: "0.875rem", borderRadius: "6px" }}
          >
            <option value="" disabled>
              {columns.length === 0
                ? "-- Loading or no columns available --"
                : `-- Select target column to predict (${columns.length} columns available) --`}
            </option>
            {recommendedTarget && columns.includes(recommendedTarget) && (
              <optgroup label="★ Recommended Target Candidate">
                <option value={recommendedTarget}>
                  {recommendedTarget} (Recommended for {taskType.replace("_", " ")})
                </option>
              </optgroup>
            )}
            <optgroup label="All Dataset Columns">
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col} {col === recommendedTarget ? "★" : ""}
                </option>
              ))}
            </optgroup>
          </select>

          {/* Inline validation warning when no target column is selected */}
          {!targetColumn && columns.length > 0 && (
            <div
              style={{
                marginTop: "0.5rem",
                padding: "0.4rem 0.75rem",
                borderRadius: "6px",
                background: "rgba(245, 158, 11, 0.1)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                color: "#f59e0b",
                fontSize: "0.75rem",
              }}
            >
              ⚠️ Please select a target column to predict for {taskType.replace("_", " ")}.
            </div>
          )}

          {/* Class distribution preview for classification */}
          {classDistribution && Object.keys(classDistribution).length > 0 && (
            <div
              style={{
                marginTop: "0.75rem",
                padding: "0.625rem 0.75rem",
                borderRadius: "6px",
                background: "var(--bg-subtle, #1e293b50)",
                border: "1px solid var(--border-subtle, #334155)",
                fontSize: "0.75rem",
              }}
            >
              <span style={{ fontWeight: 600, color: "var(--text-muted, #94a3b8)", display: "block", marginBottom: "0.375rem" }}>
                Target Class Frequencies:
              </span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
                {Object.entries(classDistribution).map(([cls, cnt]) => (
                  <span key={cls} style={{ background: "var(--bg-surface, #1e293b)", padding: "0.2rem 0.5rem", borderRadius: "4px", border: "1px solid var(--border-subtle, #334155)" }}>
                    <strong>{cls}:</strong> {cnt.toLocaleString()}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div
          style={{
            padding: "0.75rem",
            borderRadius: "6px",
            background: "var(--bg-subtle)",
            border: "1px solid var(--border-subtle)",
            fontSize: "0.8125rem",
            color: "var(--text-secondary)",
          }}
        >
          ℹ️ Unsupervised Clustering discovers natural clusters across feature vectors without requiring a target variable.
        </div>
      )}
    </div>
  );
};
