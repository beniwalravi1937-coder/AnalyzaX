"use client";

import React from "react";
import { DimensionScore, QualityDimension } from "@/types";

interface DimensionCardsProps {
  dimensions: Record<QualityDimension, DimensionScore>;
  selectedDimension?: QualityDimension | null;
  onSelectDimension?: (dim: QualityDimension | null) => void;
}

const DIMENSION_CONFIG: Record<
  QualityDimension,
  { label: string; weight: string; description: string }
> = {
  COMPLETENESS: {
    label: "Completeness",
    weight: "25% wt",
    description: "Missing values, empty cells, structural nulls, and blank strings.",
  },
  VALIDITY: {
    label: "Validity",
    weight: "25% wt",
    description: "Type consistency, range bounds, coordinate validity, and format checks.",
  },
  UNIQUENESS: {
    label: "Uniqueness",
    weight: "20% wt",
    description: "Identical full-row duplicates and entity replication rates.",
  },
  CONSISTENCY: {
    label: "Consistency",
    weight: "15% wt",
    description: "Categorical casing conflicts, whitespace variations, and string standards.",
  },
  INTEGRITY: {
    label: "Integrity",
    weight: "10% wt",
    description: "Primary key collisions, null identifiers, and entity constraints.",
  },
  ANOMALY_RISK: {
    label: "Anomaly Risk",
    weight: "5% wt",
    description: "Statistical outlier frequency and extreme distribution tails.",
  },
};

export function DimensionCards({
  dimensions,
  selectedDimension,
  onSelectDimension,
}: DimensionCardsProps) {
  const dimensionKeys = Object.keys(DIMENSION_CONFIG) as QualityDimension[];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "1rem",
        marginBottom: "1.5rem",
      }}
    >
      {dimensionKeys.map((dimKey) => {
        const dimData = dimensions[dimKey];
        const config = DIMENSION_CONFIG[dimKey];
        const isSelected = selectedDimension === dimKey;

        const score = dimData?.score ?? 100;
        const issueCount = dimData?.issue_count ?? 0;

        const scoreColor =
          score >= 90
            ? "#10b981"
            : score >= 75
            ? "#6366f1"
            : score >= 60
            ? "#f59e0b"
            : "#f43f5e";

        return (
          <div
            key={dimKey}
            onClick={() =>
              onSelectDimension?.(isSelected ? null : dimKey)
            }
            style={{
              padding: "1rem",
              backgroundColor: isSelected
                ? "rgba(99, 102, 241, 0.08)"
                : "var(--bg-surface)",
              border: isSelected
                ? "1px solid var(--primary, #6366f1)"
                : "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              cursor: onSelectDimension ? "pointer" : "default",
              transition: "all 0.15s ease",
            }}
          >
            {/* Header */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <span
                style={{
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                }}
              >
                {config.label}
              </span>
              <span
                style={{
                  fontSize: "0.625rem",
                  padding: "0.15rem 0.4rem",
                  borderRadius: "var(--radius-xs, 4px)",
                  backgroundColor: "rgba(255, 255, 255, 0.05)",
                  color: "var(--text-muted)",
                }}
              >
                {config.weight}
              </span>
            </div>

            {/* Score & Progress */}
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                justifyContent: "space-between",
                marginBottom: "0.5rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "baseline", gap: "0.25rem" }}>
                <span
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 800,
                    color: scoreColor,
                    fontFamily: "var(--font-mono, monospace)",
                    lineHeight: 1,
                  }}
                >
                  {score.toFixed(0)}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>
                  / 100
                </span>
              </div>

              <span
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.45rem",
                  borderRadius: "12px",
                  backgroundColor:
                    issueCount === 0
                      ? "rgba(16, 185, 129, 0.12)"
                      : "rgba(244, 63, 94, 0.12)",
                  color: issueCount === 0 ? "#10b981" : "#f43f5e",
                }}
              >
                {issueCount} {issueCount === 1 ? "issue" : "issues"}
              </span>
            </div>

            {/* Score Progress Bar */}
            <div
              style={{
                width: "100%",
                height: "4px",
                backgroundColor: "rgba(255, 255, 255, 0.06)",
                borderRadius: "2px",
                overflow: "hidden",
                marginBottom: "0.5rem",
              }}
            >
              <div
                style={{
                  width: `${Math.max(0, Math.min(100, score))}%`,
                  height: "100%",
                  backgroundColor: scoreColor,
                  borderRadius: "2px",
                  transition: "width 0.4s ease",
                }}
              />
            </div>

            {/* Subtext description */}
            <p
              style={{
                fontSize: "0.6875rem",
                color: "var(--text-muted)",
                margin: 0,
                lineHeight: 1.35,
              }}
            >
              {dimData?.description || config.description}
            </p>
          </div>
        );
      })}
    </div>
  );
}
