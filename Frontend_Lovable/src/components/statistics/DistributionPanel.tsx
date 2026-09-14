"use client";

import React from "react";

interface DistributionPanelProps {
  statistics: Record<string, any>;
}

export const DistributionPanel: React.FC<DistributionPanelProps> = ({ statistics }) => {
  const bins = statistics.histogram_bins || [];
  const outliers = statistics.outliers || {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Outlier Boundaries */}
      <div style={{ padding: "1rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>Tukey Outlier Boundaries (IQR)</h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", fontSize: "0.8125rem" }}>
          <div>
            <div style={{ color: "var(--text-muted)" }}>Mild Outliers (1.5 × IQR)</div>
            <div style={{ fontWeight: 600, fontFamily: "monospace" }}>
              [{outliers.mild_bounds?.[0]}, {outliers.mild_bounds?.[1]}]
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              Detected: {outliers.mild_outlier_count || 0} ({outliers.mild_outlier_percentage || 0}%)
            </div>
          </div>
          <div>
            <div style={{ color: "var(--text-muted)" }}>Extreme Outliers (3.0 × IQR)</div>
            <div style={{ fontWeight: 600, fontFamily: "monospace" }}>
              [{outliers.extreme_bounds?.[0]}, {outliers.extreme_bounds?.[1]}]
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              Detected: {outliers.extreme_outlier_count || 0} ({outliers.extreme_outlier_percentage || 0}%)
            </div>
          </div>
        </div>
      </div>

      {/* Histogram Bins Table */}
      <div>
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>Binned Frequency Table</h4>
        <div style={{ overflowX: "auto", maxHeight: "250px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                <th style={{ padding: "0.4rem" }}>Bin Range</th>
                <th style={{ padding: "0.4rem" }}>Count</th>
                <th style={{ padding: "0.4rem" }}>Percentage</th>
                <th style={{ padding: "0.4rem" }}>Expected Normal</th>
              </tr>
            </thead>
            <tbody>
              {bins.map((b: any, idx: number) => (
                <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "0.4rem", fontFamily: "monospace" }}>[{b.bin_start}, {b.bin_end})</td>
                  <td style={{ padding: "0.4rem", fontWeight: 600 }}>{b.count}</td>
                  <td style={{ padding: "0.4rem" }}>{b.percentage}%</td>
                  <td style={{ padding: "0.4rem", color: "var(--text-muted)" }}>{b.expected_normal_count ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
