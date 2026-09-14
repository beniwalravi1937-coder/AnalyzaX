"use client";

import React from "react";
import { QualitySeverity } from "@/types";

interface IssueSummaryBarProps {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  total: number;
  selectedSeverity?: QualitySeverity | null;
  onSelectSeverity?: (sev: QualitySeverity | null) => void;
}

export function IssueSummaryBar({
  critical,
  high,
  medium,
  low,
  info,
  total,
  selectedSeverity,
  onSelectSeverity,
}: IssueSummaryBarProps) {
  const chips: { severity: QualitySeverity; count: number; color: string; bg: string }[] = [
    { severity: "CRITICAL", count: critical, color: "#f43f5e", bg: "rgba(244, 63, 94, 0.12)" },
    { severity: "HIGH", count: high, color: "#f97316", bg: "rgba(249, 115, 22, 0.12)" },
    { severity: "MEDIUM", count: medium, color: "#f59e0b", bg: "rgba(245, 158, 11, 0.12)" },
    { severity: "LOW", count: low, color: "#6366f1", bg: "rgba(99, 102, 241, 0.12)" },
    { severity: "INFO", count: info, color: "#94a3b8", bg: "rgba(148, 163, 184, 0.12)" },
  ];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "0.75rem",
        padding: "0.75rem 1rem",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        marginBottom: "1rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
          Issues Filter:
        </span>
        <button
          type="button"
          onClick={() => onSelectSeverity?.(null)}
          style={{
            padding: "0.2rem 0.6rem",
            borderRadius: "12px",
            fontSize: "0.75rem",
            fontWeight: 600,
            border: selectedSeverity === null || selectedSeverity === undefined
              ? "1px solid var(--primary, #6366f1)"
              : "1px solid transparent",
            backgroundColor: selectedSeverity === null || selectedSeverity === undefined
              ? "rgba(99, 102, 241, 0.15)"
              : "rgba(255, 255, 255, 0.04)",
            color: selectedSeverity === null || selectedSeverity === undefined
              ? "var(--text-primary)"
              : "var(--text-muted)",
            cursor: "pointer",
          }}
        >
          All ({total})
        </button>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
        {chips.map(({ severity, count, color, bg }) => {
          const isSelected = selectedSeverity === severity;
          return (
            <button
              key={severity}
              type="button"
              onClick={() => onSelectSeverity?.(isSelected ? null : severity)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.35rem",
                padding: "0.2rem 0.6rem",
                borderRadius: "12px",
                fontSize: "0.75rem",
                fontWeight: 600,
                border: isSelected ? `1px solid ${color}` : "1px solid transparent",
                backgroundColor: isSelected ? bg : "rgba(255, 255, 255, 0.03)",
                color: isSelected ? color : count > 0 ? color : "var(--text-faint)",
                opacity: count === 0 && !isSelected ? 0.6 : 1,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: color,
                }}
              />
              <span>{severity}</span>
              <span
                style={{
                  padding: "0.05rem 0.35rem",
                  borderRadius: "8px",
                  backgroundColor: "rgba(0, 0, 0, 0.2)",
                  fontSize: "0.6875rem",
                }}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
