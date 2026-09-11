"use client";

import React from "react";
import { FeatureImportanceItem } from "@/types/ml";

interface FeatureImportanceViewProps {
  items: FeatureImportanceItem[];
  modelName: string;
}

export const FeatureImportanceView: React.FC<FeatureImportanceViewProps> = ({
  items,
  modelName,
}) => {
  if (!items || items.length === 0) {
    return (
      <div
        style={{
          padding: "2rem",
          textAlign: "center",
          color: "var(--text-muted)",
          fontSize: "0.875rem",
          background: "var(--bg-surface)",
          borderRadius: "8px",
          border: "1px solid var(--border-subtle)",
        }}
      >
        Feature importance is not supported by {modelName} or no feature importances were extracted.
      </div>
    );
  }

  const maxImp = Math.max(...items.map((i) => i.importance), 0.0001);

  return (
    <div
      style={{
        borderRadius: "8px",
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        padding: "1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <div>
        <h4 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600 }}>
          Predictive Feature Influence: {modelName}
        </h4>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Ranked by tree impurity reduction or normalized absolute linear coefficient.
        </span>
      </div>

      {/* Explicit Non-Causality Disclaimer Alert */}
      <div
        style={{
          padding: "0.75rem 1rem",
          borderRadius: "6px",
          background: "var(--bg-subtle)",
          borderLeft: "4px solid var(--color-indigo, #6366f1)",
          fontSize: "0.8125rem",
          color: "var(--text-secondary)",
          lineHeight: 1.4,
        }}
      >
        <strong style={{ color: "var(--text-primary)" }}>⚠️ Non-Causality Notice: </strong>
        Feature importance quantifies mathematical signal strength and predictive association within this specific model.
        High importance does <strong>not</strong> prove that changing this variable causes changes in the target outcome.
      </div>

      {/* Feature Importance Table */}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "var(--bg-subtle)", borderBottom: "1px solid var(--border-subtle)" }}>
              <th style={{ padding: "0.625rem 0.75rem" }}>Rank</th>
              <th style={{ padding: "0.625rem 0.75rem" }}>Feature</th>
              <th style={{ padding: "0.625rem 0.75rem" }}>Source Column</th>
              <th style={{ padding: "0.625rem 0.75rem", minWidth: "160px" }}>Importance</th>
              <th style={{ padding: "0.625rem 0.75rem", textAlign: "right" }}>Weight (%)</th>
              {items.some((i) => i.coefficient !== null && i.coefficient !== undefined) && (
                <th style={{ padding: "0.625rem 0.75rem", textAlign: "right" }}>Coefficient</th>
              )}
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => {
              const pct = (item.importance * 100).toFixed(1);
              const barWidth = Math.round((item.importance / maxImp) * 100);

              return (
                <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "0.625rem 0.75rem", color: "var(--text-muted)" }}>#{idx + 1}</td>
                  <td style={{ padding: "0.625rem 0.75rem", fontWeight: 600 }}>{item.feature}</td>
                  <td style={{ padding: "0.625rem 0.75rem", color: "var(--text-secondary)" }}>
                    {item.source_column !== item.feature ? (
                      <span className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>
                        {item.source_column}
                      </span>
                    ) : (
                      item.source_column
                    )}
                  </td>
                  <td style={{ padding: "0.625rem 0.75rem" }}>
                    <div style={{ width: "100%", height: "8px", background: "var(--bg-subtle)", borderRadius: "4px", overflow: "hidden" }}>
                      <div
                        style={{
                          width: `${barWidth}%`,
                          height: "100%",
                          background: "var(--color-primary, #6366f1)",
                          borderRadius: "4px",
                        }}
                      />
                    </div>
                  </td>
                  <td style={{ padding: "0.625rem 0.75rem", textAlign: "right", fontFamily: "monospace", fontWeight: 600 }}>
                    {pct}%
                  </td>
                  {items.some((i) => i.coefficient !== null && i.coefficient !== undefined) && (
                    <td style={{ padding: "0.625rem 0.75rem", textAlign: "right", fontFamily: "monospace" }}>
                      {item.coefficient !== null && item.coefficient !== undefined ? item.coefficient : "—"}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
