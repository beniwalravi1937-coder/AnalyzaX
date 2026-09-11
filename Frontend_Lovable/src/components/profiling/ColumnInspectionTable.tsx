"use client";

import React, { useState } from "react";
import { ColumnProfile } from "@/types";

interface ColumnInspectionTableProps {
  columns: ColumnProfile[];
}

function getSemanticBadgeColor(type: string): string {
  switch (type) {
    case "monetary":
      return "badge-emerald";
    case "percentage":
    case "ratio":
      return "badge-teal";
    case "identifier":
      return "badge-indigo";
    case "datetime":
    case "date":
    case "time":
      return "badge-amber";
    case "boolean":
      return "badge-purple";
    case "text":
      return "badge-rose";
    default:
      return "badge-neutral";
  }
}

export function ColumnInspectionTable({ columns }: ColumnInspectionTableProps) {
  const [expandedCol, setExpandedCol] = useState<string | null>(null);

  const toggleExpand = (colName: string) => {
    setExpandedCol((prev) => (prev === colName ? null : colName));
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ width: "32px", padding: "0.75rem 0.5rem" }}></th>
            <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>Column Name</th>
            <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>Physical Type</th>
            <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>Semantic Classification</th>
            <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>Missing (Nulls)</th>
            <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>Distinct / Cardinality</th>
            <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>Sample Values</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((col) => {
            const isExpanded = expandedCol === col.name;
            const badgeClass = getSemanticBadgeColor(col.semantic_type);

            return (
              <React.Fragment key={col.name}>
                <tr
                  onClick={() => toggleExpand(col.name)}
                  style={{
                    cursor: "pointer",
                    backgroundColor: isExpanded ? "rgba(99, 102, 241, 0.05)" : "transparent",
                    borderBottom: "1px solid var(--border-subtle)",
                    transition: "background 0.15s ease",
                  }}
                >
                  <td style={{ textAlign: "center", padding: "0.75rem 0.5rem", color: "var(--text-muted)" }}>
                    {isExpanded ? "▼" : "▶"}
                  </td>
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{col.name}</span>
                      {col.is_identifier_candidate && (
                        <span className="badge badge-indigo" style={{ fontSize: "0.625rem", padding: "0.1rem 0.35rem" }}>
                          ID
                        </span>
                      )}
                      {col.target_candidate && (
                        <span className="badge badge-emerald" style={{ fontSize: "0.625rem", padding: "0.1rem 0.35rem" }}>
                          Target
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <code
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.75rem",
                        backgroundColor: "rgba(255, 255, 255, 0.04)",
                        padding: "0.15rem 0.4rem",
                        borderRadius: "4px",
                        color: "var(--text-secondary)",
                      }}
                    >
                      {col.physical_type}
                    </code>
                  </td>
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <span className={`badge ${badgeClass}`} style={{ fontSize: "0.75rem", textTransform: "capitalize" }}>
                        {col.semantic_type.replace("_", " ")}
                      </span>
                      <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        {Math.round(col.semantic_confidence * 100)}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <span
                      style={{
                        fontSize: "0.8125rem",
                        color: col.null_count > 0 ? "var(--accent-amber)" : "var(--text-muted)",
                        fontWeight: col.null_count > 0 ? 500 : 400,
                      }}
                    >
                      {col.null_count.toLocaleString()} ({col.null_percentage}%)
                    </span>
                  </td>
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                      {col.unique_count.toLocaleString()}{" "}
                      <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                        ({Math.round(col.cardinality_ratio * 100)}%)
                      </span>
                    </span>
                  </td>
                  <td style={{ padding: "0.75rem 1rem" }}>
                    <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap", maxWidth: "260px" }}>
                      {col.sample_values.slice(0, 3).map((val, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: "0.6875rem",
                            padding: "0.15rem 0.35rem",
                            backgroundColor: "rgba(255, 255, 255, 0.04)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: "4px",
                            fontFamily: "var(--font-mono)",
                            color: "var(--text-secondary)",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            maxWidth: "80px",
                          }}
                          title={String(val)}
                        >
                          {val === null || val === undefined ? "null" : String(val)}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>

                {/* Expanded Details Drawer */}
                {isExpanded && (
                  <tr>
                    <td
                      colSpan={7}
                      style={{
                        padding: "1.25rem 1.5rem",
                        backgroundColor: "rgba(255, 255, 255, 0.015)",
                        borderBottom: "1px solid var(--border-subtle)",
                      }}
                    >
                      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                        {/* Target Variable Banner if applicable */}
                        {col.target_candidate && (
                          <div
                            style={{
                              padding: "0.6rem 0.85rem",
                              borderRadius: "var(--radius-md)",
                              backgroundColor: "rgba(16, 185, 129, 0.08)",
                              border: "1px solid rgba(16, 185, 129, 0.25)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                            }}
                          >
                            <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
                              <strong>Target Recommendation:</strong> {col.target_candidate.reason}
                            </span>
                            <span className="badge badge-emerald" style={{ fontSize: "0.6875rem" }}>
                              {col.target_candidate.task_type.replace("_", " ")} ({Math.round(col.target_candidate.confidence * 100)}% conf)
                            </span>
                          </div>
                        )}

                        {/* 1. Numerical Variables Metrics */}
                        {col.numeric_metrics && (
                          <div>
                            <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.8125rem", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Parametric & Non-Parametric Statistics
                            </h4>
                            <div className="grid-4" style={{ gap: "0.75rem", marginBottom: "0.75rem" }}>
                              <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Mean</div>
                                <div style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                                  {col.numeric_metrics.mean ?? "—"}
                                </div>
                              </div>
                              <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Median</div>
                                <div style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                                  {col.numeric_metrics.median ?? "—"}
                                </div>
                              </div>
                              <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Std Deviation</div>
                                <div style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                                  {col.numeric_metrics.stddev ?? "—"}
                                </div>
                              </div>
                              <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Min — Max</div>
                                <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                                  {col.numeric_metrics.min ?? "—"} to {col.numeric_metrics.max ?? "—"}
                                </div>
                              </div>
                            </div>

                            {/* Quantiles Bar */}
                            {col.numeric_metrics.quantiles && (
                              <div style={{ padding: "0.75rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
                                  <span>P0 (Min): {col.numeric_metrics.quantiles.p0}</span>
                                  <span>P25 (Q1): {col.numeric_metrics.quantiles.p25}</span>
                                  <span>P50 (Median): {col.numeric_metrics.quantiles.p50}</span>
                                  <span>P75 (Q3): {col.numeric_metrics.quantiles.p75}</span>
                                  <span>P100 (Max): {col.numeric_metrics.quantiles.p100}</span>
                                  <span>IQR: {col.numeric_metrics.quantiles.iqr}</span>
                                </div>
                                <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
                                  <span>Skewness: <strong style={{ color: "var(--text-secondary)" }}>{col.numeric_metrics.skewness ?? "—"}</strong></span>
                                  <span>Kurtosis: <strong style={{ color: "var(--text-secondary)" }}>{col.numeric_metrics.kurtosis ?? "—"}</strong></span>
                                  <span>Variance: <strong style={{ color: "var(--text-secondary)" }}>{col.numeric_metrics.variance ?? "—"}</strong></span>
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* 2. Categorical Distribution Metrics */}
                        {col.categorical_metrics && col.categorical_metrics.top_categories.length > 0 && (
                          <div>
                            <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.8125rem", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Top Frequent Categories ({col.categorical_metrics.top_categories.length} of {col.unique_count})
                            </h4>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                              {col.categorical_metrics.top_categories.slice(0, 8).map((cat, idx) => (
                                <div key={idx} style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.75rem" }}>
                                  <span style={{ width: "120px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--text-primary)" }}>
                                    {String(cat.value)}
                                  </span>
                                  <div style={{ flex: 1, backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "4px", height: "8px", overflow: "hidden" }}>
                                    <div
                                      style={{
                                        width: `${Math.min(100, Math.max(2, cat.percentage))}%`,
                                        height: "100%",
                                        backgroundColor: "var(--accent-indigo)",
                                        borderRadius: "4px",
                                      }}
                                    />
                                  </div>
                                  <span style={{ width: "90px", textAlign: "right", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                                    {cat.count.toLocaleString()} ({cat.percentage}%)
                                  </span>
                                </div>
                              ))}
                            </div>
                            {col.categorical_metrics.is_text && (
                              <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--accent-amber)" }}>
                                ⚠ Column identified as unstructured text (average length: {col.categorical_metrics.avg_length} chars, max: {col.categorical_metrics.max_length} chars).
                              </div>
                            )}
                          </div>
                        )}

                        {/* 3. Datetime Metrics */}
                        {col.datetime_metrics && col.datetime_metrics.min_timestamp && (
                          <div>
                            <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.8125rem", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Temporal Extents & Cadence
                            </h4>
                            <div className="grid-3" style={{ gap: "0.75rem" }}>
                              <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Earliest Timestamp</div>
                                <div style={{ fontSize: "0.8125rem", fontWeight: 500, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                                  {col.datetime_metrics.min_timestamp}
                                </div>
                              </div>
                              <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Latest Timestamp</div>
                                <div style={{ fontSize: "0.8125rem", fontWeight: 500, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                                  {col.datetime_metrics.max_timestamp}
                                </div>
                              </div>
                              <div style={{ padding: "0.6rem 0.8rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Periodicity Cadence</div>
                                <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--accent-amber)" }}>
                                  {col.datetime_metrics.detected_frequency ? col.datetime_metrics.detected_frequency.toUpperCase() : "IRREGULAR"}{" "}
                                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 400 }}>
                                    ({col.datetime_metrics.span_days} days span)
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* All Sample Values */}
                        <div>
                          <h4 style={{ margin: "0 0 0.4rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            Representative Non-Null Sample Values
                          </h4>
                          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                            {col.sample_values.map((s, idx) => (
                              <code
                                key={idx}
                                style={{
                                  fontSize: "0.75rem",
                                  padding: "0.2rem 0.5rem",
                                  backgroundColor: "rgba(255, 255, 255, 0.04)",
                                  border: "1px solid var(--border-subtle)",
                                  borderRadius: "4px",
                                  color: "var(--text-secondary)",
                                }}
                              >
                                {s === null ? "null" : String(s)}
                              </code>
                            ))}
                          </div>
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
  );
}
