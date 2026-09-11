"use client";

import React, { useState } from "react";
import { QualityDimension, QualityIssue, QualitySeverity } from "@/types";
import { SearchIcon, AlertCircleIcon } from "@/components/icons";

interface QualityIssuesTableProps {
  issues: QualityIssue[];
  selectedSeverity?: QualitySeverity | null;
  selectedDimension?: QualityDimension | null;
  onSelectSeverity?: (sev: QualitySeverity | null) => void;
  onSelectDimension?: (dim: QualityDimension | null) => void;
}

export function QualityIssuesTable({
  issues,
  selectedSeverity,
  selectedDimension,
  onSelectSeverity,
  onSelectDimension,
}: QualityIssuesTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedIssueId, setExpandedIssueId] = useState<string | null>(null);

  // Filter issues in memory
  const filteredIssues = issues.filter((issue) => {
    if (selectedSeverity && issue.severity !== selectedSeverity) return false;
    if (selectedDimension && issue.dimension !== selectedDimension) return false;
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      const matchCol = issue.column_name?.toLowerCase().includes(term);
      const matchDesc = issue.description.toLowerCase().includes(term);
      const matchType = issue.issue_type.toLowerCase().includes(term);
      if (!matchCol && !matchDesc && !matchType) return false;
    }
    return true;
  });

  const getSeverityBadge = (sev: QualitySeverity) => {
    switch (sev) {
      case "CRITICAL":
        return { color: "#f43f5e", bg: "rgba(244, 63, 94, 0.15)" };
      case "HIGH":
        return { color: "#f97316", bg: "rgba(249, 115, 22, 0.15)" };
      case "MEDIUM":
        return { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" };
      case "LOW":
        return { color: "#6366f1", bg: "rgba(99, 102, 241, 0.15)" };
      default:
        return { color: "#94a3b8", bg: "rgba(148, 163, 184, 0.15)" };
    }
  };

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        overflow: "hidden",
        marginBottom: "1.5rem",
      }}
    >
      {/* Table Controls */}
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
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Detected Quality Issues
          </h3>
          <span
            style={{
              fontSize: "0.75rem",
              padding: "0.15rem 0.5rem",
              borderRadius: "12px",
              backgroundColor: "rgba(255, 255, 255, 0.05)",
              color: "var(--text-muted)",
              fontWeight: 600,
            }}
          >
            {filteredIssues.length} of {issues.length}
          </span>
        </div>

        {/* Search input */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            backgroundColor: "rgba(255, 255, 255, 0.04)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-sm)",
            padding: "0.35rem 0.65rem",
            minWidth: "220px",
          }}
        >
          <SearchIcon size={14} style={{ color: "var(--text-faint)" }} />
          <input
            type="text"
            placeholder="Search column, issue type..."
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
          {searchTerm && (
            <button
              type="button"
              onClick={() => setSearchTerm("")}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-faint)",
                cursor: "pointer",
                padding: 0,
                fontSize: "0.75rem",
              }}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Issues Table */}
      {filteredIssues.length === 0 ? (
        <div
          style={{
            padding: "3rem 1rem",
            textAlign: "center",
            color: "var(--text-muted)",
          }}
        >
          <AlertCircleIcon size={24} style={{ margin: "0 auto 0.5rem", color: "var(--text-faint)" }} />
          <p style={{ margin: 0, fontSize: "0.875rem" }}>
            No quality issues match the selected filters.
          </p>
        </div>
      ) : (
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
                <th style={{ padding: "0.75rem 1rem", width: "100px" }}>Severity</th>
                <th style={{ padding: "0.75rem 1rem", width: "180px" }}>Issue Type</th>
                <th style={{ padding: "0.75rem 1rem", width: "130px" }}>Dimension</th>
                <th style={{ padding: "0.75rem 1rem", width: "140px" }}>Column</th>
                <th style={{ padding: "0.75rem 1rem", width: "120px" }}>Affected Rows</th>
                <th style={{ padding: "0.75rem 1rem" }}>Description & Recommended Action</th>
                <th style={{ padding: "0.75rem 1rem", width: "70px", textAlign: "right" }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {filteredIssues.map((issue) => {
                const isExpanded = expandedIssueId === issue.issue_id;
                const badge = getSeverityBadge(issue.severity);

                return (
                  <React.Fragment key={issue.issue_id}>
                    <tr
                      onClick={() =>
                        setExpandedIssueId(isExpanded ? null : issue.issue_id)
                      }
                      style={{
                        borderBottom: "1px solid var(--border-subtle)",
                        cursor: "pointer",
                        backgroundColor: isExpanded
                          ? "rgba(255, 255, 255, 0.02)"
                          : "transparent",
                        transition: "background-color 0.1s ease",
                      }}
                    >
                      {/* Severity */}
                      <td style={{ padding: "0.75rem 1rem" }}>
                        <span
                          style={{
                            display: "inline-block",
                            padding: "0.15rem 0.45rem",
                            borderRadius: "10px",
                            fontSize: "0.6875rem",
                            fontWeight: 700,
                            color: badge.color,
                            backgroundColor: badge.bg,
                            border: `1px solid ${badge.color}40`,
                          }}
                        >
                          {issue.severity}
                        </span>
                      </td>

                      {/* Issue Type */}
                      <td
                        style={{
                          padding: "0.75rem 1rem",
                          fontWeight: 600,
                          color: "var(--text-primary)",
                          fontFamily: "var(--font-mono, monospace)",
                          fontSize: "0.75rem",
                        }}
                      >
                        {issue.issue_type}
                      </td>

                      {/* Dimension */}
                      <td style={{ padding: "0.75rem 1rem", color: "var(--text-muted)" }}>
                        {issue.dimension}
                      </td>

                      {/* Column */}
                      <td style={{ padding: "0.75rem 1rem" }}>
                        {issue.column_name ? (
                          <code
                            style={{
                              padding: "0.15rem 0.35rem",
                              borderRadius: "4px",
                              backgroundColor: "rgba(255, 255, 255, 0.05)",
                              fontSize: "0.75rem",
                            }}
                          >
                            {issue.column_name}
                          </code>
                        ) : (
                          <span style={{ color: "var(--text-faint)", fontStyle: "italic" }}>
                            Dataset-wide
                          </span>
                        )}
                      </td>

                      {/* Affected Rows */}
                      <td style={{ padding: "0.75rem 1rem" }}>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                          {issue.affected_rows.toLocaleString()}
                        </div>
                        <div style={{ fontSize: "0.6875rem", color: "var(--text-faint)" }}>
                          {issue.affected_percentage.toFixed(1)}% of rows
                        </div>
                      </td>

                      {/* Description */}
                      <td style={{ padding: "0.75rem 1rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                        {issue.description}
                      </td>

                      {/* Expand Action */}
                      <td style={{ padding: "0.75rem 1rem", textAlign: "right" }}>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--primary, #6366f1)",
                            fontWeight: 600,
                          }}
                        >
                          {isExpanded ? "▲" : "▼"}
                        </span>
                      </td>
                    </tr>

                    {/* Expanded Detail Panel */}
                    {isExpanded && (
                      <tr
                        style={{
                          backgroundColor: "rgba(255, 255, 255, 0.015)",
                          borderBottom: "1px solid var(--border-subtle)",
                        }}
                      >
                        <td colSpan={7} style={{ padding: "1rem 1.5rem" }}>
                          <div
                            style={{
                              display: "grid",
                              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                              gap: "1.25rem",
                              fontSize: "0.75rem",
                            }}
                          >
                            {/* Recommended Cleaning Action for Phase 6 */}
                            <div
                              style={{
                                padding: "0.85rem",
                                backgroundColor: "rgba(99, 102, 241, 0.05)",
                                border: "1px solid rgba(99, 102, 241, 0.2)",
                                borderRadius: "var(--radius-sm)",
                              }}
                            >
                              <div
                                style={{
                                  fontWeight: 600,
                                  color: "var(--primary, #6366f1)",
                                  marginBottom: "0.35rem",
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "0.35rem",
                                }}
                              >
                                <span>⚡ Recommended Action (Phase 6 Cleaning)</span>
                              </div>
                              <p style={{ margin: 0, color: "var(--text-primary)", lineHeight: 1.4 }}>
                                {issue.recommended_action}
                              </p>
                              <div style={{ marginTop: "0.5rem", fontSize: "0.6875rem", color: "var(--text-faint)" }}>
                                Rule ID: <code>{issue.rule_id}</code> • Confidence: {(issue.confidence * 100).toFixed(0)}%
                              </div>
                            </div>

                            {/* Deterministic Evidence / Parameters */}
                            <div
                              style={{
                                padding: "0.85rem",
                                backgroundColor: "rgba(0, 0, 0, 0.2)",
                                border: "1px solid var(--border-subtle)",
                                borderRadius: "var(--radius-sm)",
                              }}
                            >
                              <div style={{ fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                                Statistical Evidence & Parameters
                              </div>
                              <pre
                                style={{
                                  margin: 0,
                                  fontSize: "0.6875rem",
                                  color: "var(--text-secondary)",
                                  fontFamily: "var(--font-mono, monospace)",
                                  whiteSpace: "pre-wrap",
                                }}
                              >
                                {JSON.stringify(issue.evidence, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
