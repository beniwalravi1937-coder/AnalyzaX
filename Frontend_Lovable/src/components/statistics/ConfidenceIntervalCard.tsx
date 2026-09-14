"use client";

import React from "react";
import { ConfidenceInterval } from "@/types/statistics";

interface ConfidenceIntervalCardProps {
  ci: ConfidenceInterval;
}

export const ConfidenceIntervalCard: React.FC<ConfidenceIntervalCardProps> = ({ ci }) => {
  const pct = Math.round(ci.level * 100);
  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: "var(--radius-md, 8px)",
        background: "var(--bg-subtle, rgba(255, 255, 255, 0.03))",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
          {ci.metric_name.replace(/_/g, " ")}
        </span>
        <span
          style={{
            fontSize: "0.7rem",
            padding: "0.15rem 0.4rem",
            borderRadius: "4px",
            background: "var(--primary-subtle, rgba(59, 130, 246, 0.15))",
            color: "var(--primary, #3b82f6)",
            fontWeight: 600,
          }}
        >
          {pct}% CI
        </span>
      </div>

      <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "monospace" }}>
        [{ci.lower.toFixed(4)}, {ci.upper.toFixed(4)}]
      </div>

      <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
        {ci.margin_of_error != null && (
          <span>
            Margin of Error (MOE): <strong>±{ci.margin_of_error.toFixed(4)}</strong>
          </span>
        )}
        {ci.standard_error != null && (
          <span>
            SE: <strong>{ci.standard_error.toFixed(4)}</strong>
          </span>
        )}
      </div>
    </div>
  );
};
