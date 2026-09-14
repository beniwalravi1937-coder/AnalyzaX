"use client";

import React from "react";

interface RegressionSummaryProps {
  statistics: Record<string, any>;
}

export const RegressionSummary: React.FC<RegressionSummaryProps> = ({ statistics }) => {
  const coefficients = statistics.coefficients || [];
  const diagnostics = statistics.diagnostics || {};
  const r2 = statistics.r_squared ?? 0;
  const adjR2 = statistics.adjusted_r_squared ?? 0;
  const fStat = statistics.f_statistic ?? 0;
  const fPVal = statistics.f_p_value ?? 1;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Overview Metrics Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "1rem" }}>
        <div style={{ padding: "0.75rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>R² (Determination)</div>
          <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: "monospace" }}>{r2.toFixed(4)}</div>
        </div>
        <div style={{ padding: "0.75rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Adjusted R²</div>
          <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: "monospace" }}>{adjR2.toFixed(4)}</div>
        </div>
        <div style={{ padding: "0.75rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>F-Statistic</div>
          <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: "monospace" }}>{fStat.toFixed(2)}</div>
        </div>
        <div style={{ padding: "0.75rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Model p-value</div>
          <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: "monospace" }}>
            {fPVal < 0.0001 ? "< 0.0001" : fPVal.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Coefficients Table */}
      <div>
        <h4 style={{ margin: "0 0 0.75rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>Parameter Estimates</h4>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                <th style={{ padding: "0.5rem" }}>Parameter</th>
                <th style={{ padding: "0.5rem" }}>Coefficient (β)</th>
                <th style={{ padding: "0.5rem" }}>Std. Error</th>
                <th style={{ padding: "0.5rem" }}>t-statistic</th>
                <th style={{ padding: "0.5rem" }}>p-value</th>
                <th style={{ padding: "0.5rem" }}>95% Confidence Interval</th>
              </tr>
            </thead>
            <tbody>
              {coefficients.map((c: any) => (
                <tr key={c.parameter} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "0.5rem", fontWeight: 600 }}>{c.parameter}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{c.coefficient.toFixed(4)}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{c.standard_error.toFixed(4)}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{c.t_statistic.toFixed(3)}</td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace", color: c.is_significant ? "var(--primary)" : "inherit" }}>
                    {c.p_value < 0.0001 ? "< 0.0001" : c.p_value.toFixed(4)}
                  </td>
                  <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>
                    [{c.confidence_interval[0].toFixed(4)}, {c.confidence_interval[1].toFixed(4)}]
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Regression Diagnostics Breakdown */}
      <div>
        <h4 style={{ margin: "0 0 0.75rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>Diagnostic Indicators</h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", fontSize: "0.8125rem" }}>
          {diagnostics.breusch_pagan && (
            <div style={{ padding: "0.75rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
              <strong>Breusch-Pagan:</strong> p = {diagnostics.breusch_pagan.p_value?.toFixed(4)}
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                {diagnostics.breusch_pagan.heteroscedasticity_concern ? "⚠️ Heteroscedasticity concern" : "✓ Homoscedasticity reasonable"}
              </div>
            </div>
          )}
          {diagnostics.durbin_watson && (
            <div style={{ padding: "0.75rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
              <strong>Durbin-Watson:</strong> DW = {diagnostics.durbin_watson.statistic?.toFixed(3)}
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                {diagnostics.durbin_watson.autocorrelation_concern ? "⚠️ Potential autocorrelation" : "✓ Errors independent"}
              </div>
            </div>
          )}
          {diagnostics.vif && Object.keys(diagnostics.vif).length > 0 && (
            <div style={{ padding: "0.75rem", borderRadius: "8px", background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)" }}>
              <strong>Multicollinearity (VIF):</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                {Object.entries(diagnostics.vif).map(([k, v]: [string, any]) => (
                  <span key={k} style={{ marginRight: "0.5rem" }}>
                    {k}: {v} {v > 5 ? "⚠️" : ""}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
