"use client";

import React, { useState } from "react";

interface CorrelationMatrixProps {
  statistics: Record<string, any>;
}

export const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({ statistics }) => {
  const columns: string[] = statistics.columns || [];
  const matrix: any[][] = statistics.matrix || [];
  const rankedPairs: any[] = statistics.ranked_pairs || [];
  const [activeTab, setActiveTab] = useState<"matrix" | "ranked">("matrix");

  const getHeatmapColor = (r: number | null) => {
    if (r === null) return "rgba(156, 163, 175, 0.1)";
    if (r > 0) {
      const alpha = Math.min(0.85, Math.max(0.1, r));
      return `rgba(59, 130, 246, ${alpha})`;
    } else {
      const alpha = Math.min(0.85, Math.max(0.1, Math.abs(r)));
      return `rgba(239, 68, 68, ${alpha})`;
    }
  };

  return (
    <div>
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button
          type="button"
          onClick={() => setActiveTab("matrix")}
          className={`btn btn-sm ${activeTab === "matrix" ? "btn-primary" : "btn-secondary"}`}
        >
          Heatmap Grid
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("ranked")}
          className={`btn btn-sm ${activeTab === "ranked" ? "btn-primary" : "btn-secondary"}`}
        >
          Ranked Relationships ({rankedPairs.length})
        </button>
      </div>

      {activeTab === "matrix" ? (
        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "collapse", fontSize: "0.75rem", textAlign: "center" }}>
            <thead>
              <tr>
                <th style={{ padding: "0.5rem", textAlign: "left" }}></th>
                {columns.map((col) => (
                  <th key={col} style={{ padding: "0.5rem", maxWidth: "80px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row, i) => (
                <tr key={columns[i]}>
                  <td style={{ padding: "0.5rem", fontWeight: 600, textAlign: "left", whiteSpace: "nowrap" }}>
                    {columns[i]}
                  </td>
                  {row.map((cell, j) => (
                    <td
                      key={j}
                      style={{
                        padding: "0.5rem 0.75rem",
                        background: getHeatmapColor(cell.r),
                        color: Math.abs(cell.r || 0) > 0.4 ? "#ffffff" : "var(--text-primary)",
                        fontWeight: 600,
                        fontFamily: "monospace",
                        border: "1px solid var(--border-subtle)",
                      }}
                      title={`Correlation: ${cell.r != null ? cell.r : 'N/A'}, p-val: ${cell.p_value != null ? cell.p_value : 'N/A'}`}
                    >
                      {cell.r != null ? cell.r.toFixed(2) : "-"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                <th style={{ padding: "0.5rem" }}>Variable 1</th>
                <th style={{ padding: "0.5rem" }}>Variable 2</th>
                <th style={{ padding: "0.5rem" }}>Correlation (r)</th>
                <th style={{ padding: "0.5rem" }}>p-value</th>
                <th style={{ padding: "0.5rem" }}>Significance</th>
              </tr>
            </thead>
            <tbody>
              {rankedPairs.map((pair, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "0.5rem", fontWeight: 600 }}>{pair.var1}</td>
                  <td style={{ padding: "0.5rem", fontWeight: 600 }}>{pair.var2}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{pair.r.toFixed(4)}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>
                    {pair.p_value < 0.0001 ? "< 0.0001" : pair.p_value.toFixed(4)}
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
                      {pair.is_significant ? "Significant" : "Not Significant"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
