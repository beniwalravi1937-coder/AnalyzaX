"use client";

import React from "react";
import { StatisticalFinding as FindingType } from "@/types/statistics";

interface StatisticalFindingProps {
  finding: FindingType;
}

export const StatisticalFinding: React.FC<StatisticalFindingProps> = ({ finding }) => {
  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case "high":
      case "critical":
        return { border: "#ef4444", bg: "rgba(239, 68, 68, 0.08)", text: "#ef4444" };
      case "medium":
        return { border: "#f59e0b", bg: "rgba(245, 158, 11, 0.08)", text: "#f59e0b" };
      case "low":
        return { border: "#3b82f6", bg: "rgba(59, 130, 246, 0.08)", text: "#3b82f6" };
      default:
        return { border: "#10b981", bg: "rgba(16, 185, 129, 0.08)", text: "#10b981" };
    }
  };

  const style = getSeverityStyle(finding.severity);

  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: "var(--radius-md, 8px)",
        background: "var(--bg-surface, rgba(255, 255, 255, 0.02))",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
        borderLeft: `4px solid ${style.border}`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.4rem" }}>
        <h4 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)" }}>
          {finding.title}
        </h4>
        <span
          style={{
            fontSize: "0.6875rem",
            padding: "0.15rem 0.4rem",
            borderRadius: "4px",
            background: style.bg,
            color: style.text,
            fontWeight: 600,
            textTransform: "uppercase",
          }}
        >
          {finding.category.replace(/_/g, " ")}
        </span>
      </div>

      <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
        {finding.description}
      </p>

      {finding.evidence && (
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "monospace", marginBottom: "0.4rem" }}>
          Evidence: {finding.evidence}
        </div>
      )}

      {finding.limitations && finding.limitations.length > 0 && (
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
          Limitations: {finding.limitations.join("; ")}
        </div>
      )}
    </div>
  );
};
