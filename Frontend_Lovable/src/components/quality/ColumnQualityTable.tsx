"use client";

import React, { useState } from "react";
import { ColumnQualitySummary, QualitySeverity } from "@/types";
import { SearchIcon } from "@/components/icons";

interface ColumnQualityTableProps {
  columns: ColumnQualitySummary[];
  onSelectColumn?: (columnName: string) => void;
}

export function ColumnQualityTable({
  columns,
  onSelectColumn,
}: ColumnQualityTableProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredColumns = columns.filter((col) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      col.column_name.toLowerCase().includes(term) ||
      col.semantic_type.toLowerCase().includes(term) ||
      col.physical_type.toLowerCase().includes(term)
    );
  });

  const getSeverityBadge = (sev?: QualitySeverity | null) => {
    if (!sev) {
      return (
        <span
          style={{
            padding: "0.15rem 0.4rem",
            borderRadius: "10px",
            fontSize: "0.6875rem",
            fontWeight: 600,
            color: "#10b981",
            backgroundColor: "rgba(16, 185, 129, 0.12)",
          }}
        >
          CLEAN
        </span>
      );
    }
    const colors: Record<QualitySeverity, { color: string; bg: string }> = {
      CRITICAL: { color: "#f43f5e", bg: "rgba(244, 63, 94, 0.15)" },
      HIGH: { color: "#f97316", bg: "rgba(249, 115, 22, 0.15)" },
      MEDIUM: { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
      LOW: { color: "#6366f1", bg: "rgba(99, 102, 241, 0.15)" },
      INFO: { color: "#94a3b8", bg: "rgba(148, 163, 184, 0.15)" },
    };
    const c = colors[sev] || colors.INFO;
    return (
      <span
        style={{
          padding: "0.15rem 0.4rem",
          borderRadius: "10px",
          fontSize: "0.6875rem",
          fontWeight: 700,
          color: c.color,
          backgroundColor: c.bg,
        }}
      >
        {sev}
      </span>
    );
  };

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        overflow: "hidden",
      }}
    >
      {/* Table Header */}
      <div
        style={{
          padding: "1rem 1.25rem",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Column-Level Quality Scorecard
          </h3>
          <p style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Field-by-field breakdown of integrity, completeness, and semantic conformity.
          </p>
        </div>

        {/* Search */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            backgroundColor: "rgba(255, 255, 255, 0.04)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-sm)",
            padding: "0.35rem 0.65rem",
            minWidth: "200px",
          }}
        >
          <SearchIcon size={14} style={{ color: "var(--text-faint)" }} />
          <input
            type="text"
            placeholder="Search column..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text-primary)",
              fontSize: "0.8125rem",
              width: "100%",
            }}
          />
        </div>
      </div>

      {/* Columns Table */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            textAlign: "left",
            fontSize: "0.8125rem",
          }}
        >
          <thead>
            <tr
              style={{
                borderBottom: "1px solid var(--border-subtle)",
                backgroundColor: "rgba(255, 255, 255, 0.01)",
                color: "var(--text-muted)",
                fontSize: "0.6875rem",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              <th style={{ padding: "0.75rem 1rem" }}>Column</th>
              <th style={{ padding: "0.75rem 1rem", width: "120px" }}>Types</th>
              <th style={{ padding: "0.75rem 1rem", width: "160px" }}>Health Score</th>
              <th style={{ padding: "0.75rem 1rem", width: "110px" }}>Missing %</th>
              <th style={{ padding: "0.75rem 1rem", width: "110px" }}>Unique %</th>
              <th style={{ padding: "0.75rem 1rem", width: "100px" }}>Issues</th>
              <th style={{ padding: "0.75rem 1rem", width: "110px" }}>Worst Severity</th>
            </tr>
          </thead>
          <tbody>
            {filteredColumns.map((col) => {
              const score = col.quality_score;
              const scoreColor =
                score >= 90
                  ? "#10b981"
                  : score >= 75
                  ? "#6366f1"
                  : score >= 60
                  ? "#f59e0b"
                  : "#f43f5e";

              return (
                <tr
                  key={col.column_name}
                  onClick={() => onSelectColumn?.(col.column_name)}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    cursor: onSelectColumn ? "pointer" : "default",
                    transition: "background-color 0.1s ease",
                  }}
                >
                  {/* Column Name */}
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <code
                      style={{
                        fontWeight: 600,
                        color: "var(--text-primary)",
                        fontSize: "0.8125rem",
                      }}
                    >
                      {col.column_name}
                    </code>
                  </td>

                  {/* Types */}
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {col.physical_type}
                    </div>
                    <div
                      style={{
                        fontSize: "0.6875rem",
                        color: "var(--text-faint)",
                        fontStyle: "italic",
                      }}
                    >
                      {col.semantic_type}
                    </div>
                  </td>

                  {/* Quality Score Bar */}
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                      }}
                    >
                      <span
                        style={{
                          fontWeight: 700,
                          color: scoreColor,
                          fontSize: "0.8125rem",
                          fontFamily: "var(--font-mono, monospace)",
                          width: "35px",
                        }}
                      >
                        {score.toFixed(0)}
                      </span>
                      <div
                        style={{
                          flex: 1,
                          height: "5px",
                          backgroundColor: "rgba(255, 255, 255, 0.06)",
                          borderRadius: "3px",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.max(0, Math.min(100, score))}%`,
                            height: "100%",
                            backgroundColor: scoreColor,
                            borderRadius: "3px",
                          }}
                        />
                      </div>
                    </div>
                  </td>

                  {/* Missing % */}
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <span
                      style={{
                        fontWeight: col.null_percentage > 0 ? 600 : 400,
                        color:
                          col.null_percentage >= 20
                            ? "#f43f5e"
                            : col.null_percentage >= 5
                            ? "#f59e0b"
                            : "var(--text-secondary)",
                      }}
                    >
                      {col.null_percentage.toFixed(1)}%
                    </span>
                  </td>

                  {/* Unique % */}
                  <td style={{ padding: "0.75rem 1rem", color: "var(--text-secondary)" }}>
                    {col.unique_percentage.toFixed(1)}%
                  </td>

                  {/* Issues Count */}
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <span
                      style={{
                        fontWeight: 600,
                        color:
                          col.issues_count > 0 ? "var(--text-primary)" : "var(--text-faint)",
                      }}
                    >
                      {col.issues_count}
                    </span>
                  </td>

                  {/* Highest Severity */}
                  <td style={{ padding: "0.75rem 1rem" }}>
                    {getSeverityBadge(col.highest_severity)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
