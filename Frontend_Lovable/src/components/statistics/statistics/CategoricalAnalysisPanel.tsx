"use client";

import React from "react";

interface CategoricalAnalysisPanelProps {
  statistics: Record<string, any>;
}

export const CategoricalAnalysisPanel: React.FC<CategoricalAnalysisPanelProps> = ({ statistics }) => {
  const table = statistics.contingency_table || {};
  const rows = table.rows || [];
  const colSummaries = table.column_summaries || [];
  const fisher = statistics.fisher_exact_test;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Fisher's Exact details if 2x2 */}
      {fisher && (
        <div style={{ padding: "1rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
          <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>Fisher's Exact Test (2×2 Exact Inference)</h4>
          <div style={{ display: "flex", gap: "2rem", fontSize: "0.8125rem" }}>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Odds Ratio: </span>
              <strong style={{ fontFamily: "monospace" }}>{fisher.odds_ratio}</strong>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Exact p-value: </span>
              <strong style={{ fontFamily: "monospace" }}>{fisher.p_value < 0.0001 ? "< 0.0001" : fisher.p_value}</strong>
            </div>
            {fisher.confidence_interval_95 && (
              <div>
                <span style={{ color: "var(--text-muted)" }}>95% CI for OR: </span>
                <strong style={{ fontFamily: "monospace" }}>
                  [{fisher.confidence_interval_95[0]}, {fisher.confidence_interval_95[1]}]
                </strong>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Contingency Table Grid */}
      <div>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>
          Contingency Table ({table.row_variable} × {table.column_variable})
        </h4>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "center" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                <th style={{ padding: "0.5rem", textAlign: "left" }}>{table.row_variable}</th>
                {table.column_categories?.map((cat: string) => (
                  <th key={cat} style={{ padding: "0.5rem" }}>{cat}</th>
                ))}
                <th style={{ padding: "0.5rem" }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r: any) => (
                <tr key={r.row_category} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "0.5rem", fontWeight: 600, textAlign: "left" }}>{r.row_category}</td>
                  {r.cells?.map((cell: any, idx: number) => (
                    <td key={idx} style={{ padding: "0.5rem" }}>
                      <div style={{ fontWeight: 600 }}>{cell.observed}</div>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                        Exp: {cell.expected} | Res: {cell.residual > 0 ? `+${cell.residual}` : cell.residual}
                      </div>
                    </td>
                  ))}
                  <td style={{ padding: "0.5rem", fontWeight: 700 }}>
                    {r.row_total} ({r.row_percentage_of_total}%)
                  </td>
                </tr>
              ))}
              {/* Column Totals Row */}
              <tr style={{ borderTop: "2px solid var(--border-subtle)", fontWeight: 700 }}>
                <td style={{ padding: "0.5rem", textAlign: "left" }}>Total</td>
                {colSummaries.map((c: any, idx: number) => (
                  <td key={idx} style={{ padding: "0.5rem" }}>
                    {c.column_total} ({c.column_percentage_of_total}%)
                  </td>
                ))}
                <td style={{ padding: "0.5rem" }}>{table.grand_total} (100%)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
