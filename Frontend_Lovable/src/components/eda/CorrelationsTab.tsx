"use client";

import React, { useState } from "react";
import { EDAResponse, CorrelationMatrix } from "@/types";
import { EdaVisualizer } from "./EdaVisualizer";
import { SectionCard } from "@/components/ui/SectionCard";

interface CorrelationsTabProps {
  report: EDAResponse;
  onChangeMethod?: (method: "pearson" | "spearman" | "kendall") => void;
  onInspectPair?: (colX: string, colY: string) => void;
  isRefreshing?: boolean;
}

export function CorrelationsTab({
  report,
  onChangeMethod,
  onInspectPair,
  isRefreshing = false,
}: CorrelationsTabProps) {
  const correlation: CorrelationMatrix | undefined =
    (report as any).bivariate?.correlation_matrix || report.correlation || undefined;
  const heatmapChart = (report.charts || []).find((c) => c.chart_id === "corr_heatmap");

  const [currentMethod, setCurrentMethod] = useState<string>(
    correlation?.method || "pearson"
  );

  const handleMethodChange = (method: "pearson" | "spearman" | "kendall") => {
    setCurrentMethod(method);
    if (onChangeMethod) {
      onChangeMethod(method);
    }
  };

  if (!correlation || correlation.columns.length < 2) {
    return (
      <div className="card" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <h3>Insufficient Numeric Features</h3>
        <p style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>
          Correlation matrices require at least two numerical columns. This dataset does not have enough numeric variables.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Top Header: Method Selector */}
      <div
        className="card"
        style={{
          padding: "1rem 1.25rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Multivariate Correlation Structure
          </h3>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Matrix computed across {correlation.columns.length} numeric features
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Method:</span>
          {(["pearson", "spearman", "kendall"] as const).map((m) => (
            <button
              key={m}
              onClick={() => handleMethodChange(m)}
              disabled={isRefreshing}
              className={`btn ${currentMethod === m ? "btn-primary" : "btn-ghost"}`}
              style={{
                fontSize: "0.75rem",
                padding: "0.3rem 0.75rem",
                textTransform: "capitalize",
              }}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Heatmap + Strong Pairs List */}
      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: "1.5rem", alignItems: "start" }}>
        {/* Correlation Heatmap */}
        <SectionCard
          title={`Correlation Heatmap (${currentMethod.toUpperCase()})`}
          subtitle="Click any cell to open the Relationship Studio for that feature pair"
        >
          {heatmapChart ? (
            <EdaVisualizer
              spec={heatmapChart}
              height={360}
              onCellClick={(x, y) => {
                if (x !== y && onInspectPair) {
                  onInspectPair(x, y);
                }
              }}
            />
          ) : (
            <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
              No correlation heatmap chart generated.
            </div>
          )}
        </SectionCard>

        {/* Top Correlated Pairs */}
        {(() => {
          const rankedPairs = correlation.ranked_pairs || correlation.top_correlations || [];
          return (
            <SectionCard
              title="Ranked Correlation Pairs"
              subtitle={`${rankedPairs.length} feature pairs ordered by linear dependency`}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", maxHeight: "420px", overflowY: "auto" }}>
                {rankedPairs.length === 0 ? (
                  <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                    No significant correlations identified.
                  </div>
                ) : (
                  rankedPairs.map((pair, i) => {
                    const r = pair.correlation;
                    const absR = Math.abs(r);
                    const isCollinear = absR >= 0.85;
                    const isStrong = absR >= 0.6;
                    const badgeColor = isCollinear
                      ? "badge-rose"
                      : isStrong
                      ? "badge-indigo"
                      : "badge-neutral";
                    const colA = pair.column_x || pair.column_a || "";
                    const colB = pair.column_y || pair.column_b || "";

                    return (
                      <div
                        key={i}
                        style={{
                          padding: "0.75rem 1rem",
                          backgroundColor: "rgba(255, 255, 255, 0.02)",
                          border: "1px solid var(--border-subtle)",
                          borderRadius: "var(--radius-sm)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: "0.75rem",
                        }}
                      >
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div
                            style={{
                              fontSize: "0.8125rem",
                              fontWeight: 600,
                              color: "var(--text-primary)",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {colA} <span style={{ color: "var(--text-muted)" }}>↔</span> {colB}
                          </div>
                          <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                            {isCollinear ? "⚠️ Multicollinear Risk" : isStrong ? "Strong Relationship" : "Moderate Relationship"}
                          </div>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                          <span
                            className={`badge ${badgeColor}`}
                            style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}
                          >
                            {r > 0 ? `+${r.toFixed(3)}` : r.toFixed(3)}
                          </span>

                          {onInspectPair && (
                            <button
                              onClick={() => onInspectPair(colA, colB)}
                              className="btn btn-ghost"
                              style={{ fontSize: "0.6875rem", padding: "0.25rem 0.5rem" }}
                              title="Inspect Scatter Plot in Relationship Studio"
                            >
                              Explore →
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </SectionCard>
          );
        })()}
      </div>
    </div>
  );
}
