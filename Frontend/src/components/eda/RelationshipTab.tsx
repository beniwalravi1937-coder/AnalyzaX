"use client";

import React, { useState, useEffect } from "react";
import { EDAResponse, ChartSpec } from "@/types";
import { api } from "@/services/api";
import { EdaVisualizer } from "./EdaVisualizer";
import { SectionCard } from "@/components/ui/SectionCard";

interface RelationshipTabProps {
  report: EDAResponse;
  initialColX?: string;
  initialColY?: string;
}

export function RelationshipTab({
  report,
  initialColX,
  initialColY,
}: RelationshipTabProps) {
  const overview = report.overview;
  const numeric = (report as any).univariate?.numeric || report.numeric_analyses || [];
  const categorical = (report as any).univariate?.categorical || report.categorical_analyses || [];
  const allCols = [
    ...numeric.map((n: any) => ({ name: n.column, type: "numeric" })),
    ...categorical.map((c: any) => ({ name: c.column, type: "categorical" })),
  ];

  const defaultX = initialColX || (allCols.length > 0 ? allCols[0].name : "");
  const defaultY =
    initialColY ||
    (allCols.length > 1
      ? allCols[1].name
      : allCols.length > 0
      ? allCols[0].name
      : "");

  const [colX, setColX] = useState<string>(defaultX);
  const [colY, setColY] = useState<string>(defaultY);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [relationshipData, setRelationshipData] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync when props change (e.g. from clicking on correlation table)
  useEffect(() => {
    if (initialColX) setColX(initialColX);
    if (initialColY) setColY(initialColY);
  }, [initialColX, initialColY]);

  const runAnalysis = async (x: string, y: string) => {
    if (!x || !y) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.analyzeRelationship(
        overview.dataset_id,
        x,
        y,
        overview.version_id
      );
      setRelationshipData(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to analyze relationship");
    } finally {
      setIsLoading(false);
    }
  };

  // Run initial analysis once on mount or when x/y change from parent
  useEffect(() => {
    if (colX && colY) {
      runAnalysis(colX, colY);
    }
  }, [colX, colY]);

  // Build ChartSpec for visualizer from relationship response
  const buildChartSpec = (): ChartSpec | null => {
    if (!relationshipData) return null;
    const rel = relationshipData.relationship;

    // 1. Numeric vs Numeric -> Scatter
    if (relationshipData.type === "numeric_numeric" && rel) {
      const samplePts = (rel.sample_points || []).map((pt: any) => ({
        x: pt.x,
        y: pt.y,
      }));

      return {
        chart_id: `scatter_${rel.column_x}_${rel.column_y}`,
        chart_type: "scatter",
        title: `${rel.column_x} vs ${rel.column_y}`,
        description: `Pearson r = ${rel.correlation > 0 ? "+" : ""}${rel.correlation.toFixed(2)}${
          rel.regression ? `, R² = ${rel.regression.r_squared.toFixed(2)}` : ""
        }`,
        x: rel.column_x,
        y: rel.column_y,
        data: samplePts,
        sampling: rel.sampling,
      };
    }

    // 2. Numeric vs Categorical -> Grouped Bar / Distribution
    if (
      (relationshipData.type === "numeric_categorical" ||
        relationshipData.type === "categorical_numeric") &&
      rel
    ) {
      const groups = rel.groups || [];
      const barData = groups.map((g: any) => ({
        category: g.group_name,
        count: g.mean,
        percentage: g.median,
      }));

      return {
        chart_id: `grouped_${rel.numeric_column}_by_${rel.categorical_column}`,
        chart_type: "bar",
        title: `${rel.numeric_column} by ${rel.categorical_column} (Group Mean)`,
        description: `ANOVA F-stat: ${rel.anova?.f_statistic?.toFixed(2) || "N/A"} (p = ${
          rel.anova?.p_value !== undefined ? rel.anova.p_value.toFixed(4) : "N/A"
        })`,
        x: rel.categorical_column,
        y: "mean",
        data: barData,
      };
    }

    return null;
  };

  const chartSpec = buildChartSpec();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Selector Controls Bar */}
      <div
        className="card"
        style={{
          padding: "1.25rem",
          display: "flex",
          alignItems: "center",
          gap: "1.25rem",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            Variable X:
          </label>
          <select
            value={colX}
            onChange={(e) => setColX(e.target.value)}
            className="input"
            style={{ width: "200px", fontSize: "0.8125rem" }}
          >
            {allCols.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.type.slice(0, 3)})
              </option>
            ))}
          </select>
        </div>

        <div style={{ fontSize: "1.25rem", color: "var(--text-muted)" }}>↔</div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            Variable Y:
          </label>
          <select
            value={colY}
            onChange={(e) => setColY(e.target.value)}
            className="input"
            style={{ width: "200px", fontSize: "0.8125rem" }}
          >
            {allCols.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.type.slice(0, 3)})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => runAnalysis(colX, colY)}
          disabled={isLoading || colX === colY}
          className="btn btn-primary"
          style={{ fontSize: "0.8125rem", padding: "0.5rem 1.25rem" }}
        >
          {isLoading ? "Analyzing..." : "Analyze Relationship"}
        </button>

        {colX === colY && (
          <span style={{ fontSize: "0.75rem", color: "#f43f5e" }}>
            Select two distinct features.
          </span>
        )}
      </div>

      {/* Error display */}
      {errorMsg && (
        <div
          style={{
            padding: "1rem",
            backgroundColor: "rgba(244, 63, 94, 0.1)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "var(--radius-sm)",
            color: "#f43f5e",
            fontSize: "0.8125rem",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Relationship Visualization & Results */}
      {relationshipData && !isLoading && (
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "1.5rem", alignItems: "start" }}>
          {/* Chart Display */}
          <SectionCard
            title={chartSpec?.title || "Feature Relationship"}
            subtitle={chartSpec?.description || "Visual distribution"}
          >
            {chartSpec ? (
              <EdaVisualizer spec={chartSpec} height={320} />
            ) : (
              <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
                No plot available for this relationship pair.
              </div>
            )}
          </SectionCard>

          {/* Statistical Breakdown Card */}
          <SectionCard title="Relationship Statistics" subtitle="Deterministic metrics & inference">
            {relationshipData.type === "numeric_numeric" && relationshipData.relationship && (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  <StatItem
                    label="Pearson Correlation (r)"
                    value={relationshipData.relationship.correlation.toFixed(3)}
                    highlight={Math.abs(relationshipData.relationship.correlation) > 0.6}
                  />
                  <StatItem
                    label="Coefficient of Determination (R²)"
                    value={
                      relationshipData.relationship.regression
                        ? relationshipData.relationship.regression.r_squared.toFixed(3)
                        : "N/A"
                    }
                  />
                  <StatItem
                    label="Regression Slope (m)"
                    value={
                      relationshipData.relationship.regression
                        ? relationshipData.relationship.regression.slope.toFixed(4)
                        : "N/A"
                    }
                  />
                  <StatItem
                    label="Regression Intercept (b)"
                    value={
                      relationshipData.relationship.regression
                        ? relationshipData.relationship.regression.intercept.toFixed(2)
                        : "N/A"
                    }
                  />
                </div>

                {relationshipData.relationship.regression && (
                  <div
                    style={{
                      padding: "0.75rem",
                      backgroundColor: "rgba(99, 102, 241, 0.08)",
                      border: "1px solid rgba(99, 102, 241, 0.25)",
                      borderRadius: "var(--radius-sm)",
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.8125rem",
                      color: "#818cf8",
                    }}
                  >
                    Equation: <strong>y = {relationshipData.relationship.regression.slope.toFixed(3)}x {relationshipData.relationship.regression.intercept >= 0 ? "+" : "-"} {Math.abs(relationshipData.relationship.regression.intercept).toFixed(2)}</strong>
                  </div>
                )}
              </div>
            )}

            {(relationshipData.type === "numeric_categorical" ||
              relationshipData.type === "categorical_numeric") &&
              relationshipData.relationship && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                    <StatItem
                      label="ANOVA F-Statistic"
                      value={
                        relationshipData.relationship.anova?.f_statistic !== undefined
                          ? relationshipData.relationship.anova.f_statistic.toFixed(2)
                          : "N/A"
                      }
                    />
                    <StatItem
                      label="ANOVA p-value"
                      value={
                        relationshipData.relationship.anova?.p_value !== undefined
                          ? relationshipData.relationship.anova.p_value.toFixed(5)
                          : "N/A"
                      }
                      highlight={relationshipData.relationship.anova?.p_value < 0.05}
                    />
                    <StatItem
                      label="Correlation Ratio (η²)"
                      value={
                        relationshipData.relationship.correlation_ratio !== undefined
                          ? relationshipData.relationship.correlation_ratio.toFixed(3)
                          : "N/A"
                      }
                    />
                    <StatItem
                      label="Category Count"
                      value={String(relationshipData.relationship.groups?.length || 0)}
                    />
                  </div>

                  {/* Group Stats Table */}
                  <div style={{ overflowX: "auto" }}>
                    <table className="table" style={{ width: "100%", fontSize: "0.75rem" }}>
                      <thead>
                        <tr>
                          <th>Group</th>
                          <th style={{ textAlign: "right" }}>N</th>
                          <th style={{ textAlign: "right" }}>Mean</th>
                          <th style={{ textAlign: "right" }}>Median</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(relationshipData.relationship.groups || []).map((g: any, idx: number) => (
                          <tr key={idx}>
                            <td style={{ fontWeight: 600 }}>{g.group_name}</td>
                            <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{g.count}</td>
                            <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{g.mean.toFixed(2)}</td>
                            <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{g.median.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
          </SectionCard>
        </div>
      )}
    </div>
  );
}

function StatItem({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div
      style={{
        padding: "0.6rem 0.75rem",
        backgroundColor: "rgba(255, 255, 255, 0.02)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>{label}</div>
      <div
        style={{
          fontSize: "1.125rem",
          fontWeight: 600,
          color: highlight ? "#38bdf8" : "var(--text-primary)",
          fontFamily: "var(--font-mono)",
          marginTop: "0.2rem",
        }}
      >
        {value}
      </div>
    </div>
  );
}
