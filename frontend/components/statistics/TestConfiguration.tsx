"use client";

import React from "react";
import { MethodCatalogItem } from "@/types/statistics";

interface TestConfigurationProps {
  methodItem: MethodCatalogItem;
  columns: string[];
  targetColumns: string[];
  groupColumns: string[];
  alpha: number;
  confidenceLevel: number;
  alternative: string;
  multipleTesting: string;
  onTargetChange: (cols: string[]) => void;
  onGroupChange: (cols: string[]) => void;
  onAlphaChange: (alpha: number) => void;
  onConfidenceChange: (conf: number) => void;
  onAlternativeChange: (alt: string) => void;
  onMultipleTestingChange: (method: string) => void;
  onRun: () => void;
  isLoading: boolean;
}

export const TestConfiguration: React.FC<TestConfigurationProps> = ({
  methodItem,
  columns,
  targetColumns,
  groupColumns,
  alpha,
  confidenceLevel,
  alternative,
  multipleTesting,
  onTargetChange,
  onGroupChange,
  onAlphaChange,
  onConfidenceChange,
  onAlternativeChange,
  onMultipleTestingChange,
  onRun,
  isLoading,
}) => {
  const isMultiTarget = ["descriptive_summary", "correlation_matrix", "covariance_matrix"].includes(methodItem.method);
  const needsGroup = ["t_test_welch", "t_test_ind", "mann_whitney_u", "anova_oneway", "kruskal_wallis", "ols_regression"].includes(methodItem.method);
  const isRegression = methodItem.method === "ols_regression";

  const toggleTarget = (col: string) => {
    if (isMultiTarget) {
      if (targetColumns.includes(col)) {
        onTargetChange(targetColumns.filter((c) => c !== col));
      } else {
        onTargetChange([...targetColumns, col]);
      }
    } else {
      onTargetChange([col]);
    }
  };

  const toggleGroup = (col: string) => {
    if (isRegression) {
      // Multiple predictors allowed
      if (groupColumns.includes(col)) {
        onGroupChange(groupColumns.filter((c) => c !== col));
      } else {
        onGroupChange([...groupColumns, col]);
      }
    } else {
      onGroupChange([col]);
    }
  };

  return (
    <div
      style={{
        padding: "1.25rem",
        borderRadius: "var(--radius-md, 8px)",
        background: "var(--bg-surface, rgba(255, 255, 255, 0.02))",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
      }}
    >
      <div>
        <h4 style={{ margin: "0 0 0.25rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>
          Configure: {methodItem.name}
        </h4>
        <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)" }}>
          {methodItem.description}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: needsGroup ? "1fr 1fr" : "1fr", gap: "1.25rem" }}>
        {/* Target Columns */}
        <div>
          <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "0.5rem" }}>
            {isRegression ? "Dependent Variable (Outcome Y)" : (isMultiTarget ? "Target Columns (Select 1 or more)" : "Target / Outcome Column")}
          </label>
          <div
            style={{
              maxHeight: "160px",
              overflowY: "auto",
              padding: "0.5rem",
              borderRadius: "6px",
              background: "var(--bg-subtle)",
              border: "1px solid var(--border-subtle)",
              display: "flex",
              flexWrap: "wrap",
              gap: "0.4rem",
            }}
          >
            {columns.map((col) => {
              const isSelected = targetColumns.includes(col);
              return (
                <button
                  key={col}
                  type="button"
                  onClick={() => toggleTarget(col)}
                  className={`btn btn-xs ${isSelected ? "btn-primary" : "btn-secondary"}`}
                >
                  {col}
                </button>
              );
            })}
          </div>
        </div>

        {/* Group Columns (if needed) */}
        {needsGroup && (
          <div>
            <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "0.5rem" }}>
              {isRegression ? "Independent Predictors (X)" : "Grouping / Factor Column"}
            </label>
            <div
              style={{
                maxHeight: "160px",
                overflowY: "auto",
                padding: "0.5rem",
                borderRadius: "6px",
                background: "var(--bg-subtle)",
                border: "1px solid var(--border-subtle)",
                display: "flex",
                flexWrap: "wrap",
                gap: "0.4rem",
              }}
            >
              {columns
                .filter((c) => !targetColumns.includes(c))
                .map((col) => {
                  const isSelected = groupColumns.includes(col);
                  return (
                    <button
                      key={col}
                      type="button"
                      onClick={() => toggleGroup(col)}
                      className={`btn btn-xs ${isSelected ? "btn-primary" : "btn-secondary"}`}
                    >
                      {col}
                    </button>
                  );
                })}
            </div>
          </div>
        )}
      </div>

      {/* Advanced Statistical Parameters Bar */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "1rem",
          paddingTop: "0.75rem",
          borderTop: "1px solid var(--border-subtle)",
        }}
      >
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
            Significance Level (α)
          </label>
          <select
            value={alpha}
            onChange={(e) => onAlphaChange(parseFloat(e.target.value))}
            className="input input-sm"
            style={{ width: "100%" }}
          >
            <option value={0.01}>0.01 (99% confidence)</option>
            <option value={0.05}>0.05 (95% default)</option>
            <option value={0.10}>0.10 (90% exploratory)</option>
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
            Confidence Level
          </label>
          <select
            value={confidenceLevel}
            onChange={(e) => onConfidenceChange(parseFloat(e.target.value))}
            className="input input-sm"
            style={{ width: "100%" }}
          >
            <option value={0.90}>90%</option>
            <option value={0.95}>95% (Default)</option>
            <option value={0.99}>99%</option>
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
            Alternative Hypothesis
          </label>
          <select
            value={alternative}
            onChange={(e) => onAlternativeChange(e.target.value)}
            className="input input-sm"
            style={{ width: "100%" }}
          >
            <option value="two-sided">Two-Sided (≠)</option>
            <option value="greater">Greater (&gt;)</option>
            <option value="less">Less (&lt;)</option>
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
            Multiple-Testing Adjustment
          </label>
          <select
            value={multipleTesting}
            onChange={(e) => onMultipleTestingChange(e.target.value)}
            className="input input-sm"
            style={{ width: "100%" }}
          >
            <option value="none">None (Raw p-values)</option>
            <option value="bonferroni">Bonferroni</option>
            <option value="holm">Holm Step-Down</option>
            <option value="fdr_bh">Benjamini-Hochberg (FDR)</option>
          </select>
        </div>
      </div>

      {/* Action Button */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          onClick={onRun}
          disabled={targetColumns.length === 0 || isLoading}
          className="btn btn-primary"
        >
          {isLoading ? "Computing Deterministic Statistics..." : "Execute Statistical Analysis"}
        </button>
      </div>
    </div>
  );
};
