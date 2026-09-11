"use client";

import React from "react";
import { AssumptionCheck } from "@/types/statistics";

interface AssumptionPanelProps {
  assumptions: AssumptionCheck[];
}

export const AssumptionPanel: React.FC<AssumptionPanelProps> = ({ assumptions }) => {
  if (!assumptions || assumptions.length === 0) {
    return (
      <div style={{ padding: "1rem", color: "var(--text-muted)", fontSize: "0.875rem" }}>
        No explicit diagnostic assumptions required for this calculation.
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PASS":
        return { label: "Satisfied", bg: "rgba(16, 185, 129, 0.15)", text: "#10b981", border: "rgba(16, 185, 129, 0.3)" };
      case "WARNING":
        return { label: "Caution", bg: "rgba(245, 158, 11, 0.15)", text: "#f59e0b", border: "rgba(245, 158, 11, 0.3)" };
      case "VIOLATION":
        return { label: "Violation", bg: "rgba(239, 68, 68, 0.15)", text: "#ef4444", border: "rgba(239, 68, 68, 0.3)" };
      case "INSUFFICIENT_DATA":
        return { label: "Insufficient Data", bg: "rgba(156, 163, 175, 0.15)", text: "#9ca3af", border: "rgba(156, 163, 175, 0.3)" };
      default:
        return { label: status, bg: "rgba(156, 163, 175, 0.15)", text: "#9ca3af", border: "rgba(156, 163, 175, 0.3)" };
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {assumptions.map((check) => {
        const badge = getStatusBadge(check.status);
        return (
          <div
            key={check.check_id}
            style={{
              padding: "1rem",
              borderRadius: "var(--radius-md, 8px)",
              background: "var(--bg-surface, rgba(255, 255, 255, 0.02))",
              border: `1px solid ${check.status === "VIOLATION" ? badge.border : "var(--border-subtle, rgba(255, 255, 255, 0.08))"}`,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.4rem" }}>
              <div>
                <span style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.9375rem" }}>
                  {check.assumption}
                </span>
                <span style={{ marginLeft: "0.5rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  ({check.method})
                </span>
              </div>
              <span
                style={{
                  fontSize: "0.75rem",
                  padding: "0.2rem 0.5rem",
                  borderRadius: "4px",
                  background: badge.bg,
                  color: badge.text,
                  border: `1px solid ${badge.border}`,
                  fontWeight: 600,
                }}
              >
                {badge.label}
              </span>
            </div>

            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginBottom: "0.4rem" }}>
              {check.evidence}
            </div>

            {check.recommendation && (
              <div
                style={{
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                  background: "var(--bg-subtle, rgba(255, 255, 255, 0.03))",
                  padding: "0.5rem 0.75rem",
                  borderRadius: "4px",
                  borderLeft: `3px solid ${badge.text}`,
                }}
              >
                <strong>Recommendation:</strong> {check.recommendation}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
