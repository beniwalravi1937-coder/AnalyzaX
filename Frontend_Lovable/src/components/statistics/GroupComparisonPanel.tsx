"use client";

import React from "react";

interface GroupComparisonPanelProps {
  statistics: Record<string, any>;
}

export const GroupComparisonPanel: React.FC<GroupComparisonPanelProps> = ({ statistics }) => {
  const summaries = statistics.group_summaries || (
    statistics.group1_summary && statistics.group2_summary
      ? [statistics.group1_summary, statistics.group2_summary]
      : []
  );
  const postHoc = statistics.post_hoc_comparisons || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Group Summaries */}
      <div>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>Group Estimates</h4>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                <th style={{ padding: "0.5rem" }}>Group</th>
                <th style={{ padding: "0.5rem" }}>Count (n)</th>
                <th style={{ padding: "0.5rem" }}>Mean</th>
                <th style={{ padding: "0.5rem" }}>Std. Dev</th>
                <th style={{ padding: "0.5rem" }}>Std. Error</th>
              </tr>
            </thead>
            <tbody>
              {summaries.map((g: any) => (
                <tr key={g.group} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "0.5rem", fontWeight: 600 }}>{g.group}</td>
                  <td style={{ padding: "0.5rem" }}>{g.count}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{g.mean != null ? g.mean.toFixed(4) : (g.median?.toFixed(4) ?? "-")}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{g.std != null ? g.std.toFixed(4) : "-"}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{g.se != null ? g.se.toFixed(4) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Post-Hoc Pairwise Comparisons */}
      {postHoc.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>
            Post-Hoc Pairwise Comparisons (Multiple Testing Adjusted)
          </h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                  <th style={{ padding: "0.5rem" }}>Comparison</th>
                  <th style={{ padding: "0.5rem" }}>Mean Diff</th>
                  <th style={{ padding: "0.5rem" }}>Raw p-value</th>
                  <th style={{ padding: "0.5rem" }}>Adjusted p-value</th>
                  <th style={{ padding: "0.5rem" }}>Decision</th>
                </tr>
              </thead>
              <tbody>
                {postHoc.map((pair: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.5rem", fontWeight: 600 }}>{pair.group1} vs {pair.group2}</td>
                    <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{pair.mean_difference?.toFixed(4) ?? "-"}</td>
                    <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>
                      {pair.raw_p_value < 0.0001 ? "< 0.0001" : pair.raw_p_value.toFixed(4)}
                    </td>
                    <td style={{ padding: "0.5rem", fontFamily: "monospace", color: pair.is_significant ? "var(--primary)" : "inherit" }}>
                      {pair.adjusted_p_value < 0.0001 ? "< 0.0001" : pair.adjusted_p_value.toFixed(4)}
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      <span
                        style={{
                          padding: "0.15rem 0.4rem",
                          borderRadius: "4px",
                          fontSize: "0.75rem",
                          background: pair.is_significant ? "rgba(16, 185, 129, 0.15)" : "rgba(156, 163, 175, 0.15)",
                          color: pair.is_significant ? "#10b981" : "#9ca3af",
                          fontWeight: 600,
                        }}
                      >
                        {pair.is_significant ? "Significant Difference" : "No Difference"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
