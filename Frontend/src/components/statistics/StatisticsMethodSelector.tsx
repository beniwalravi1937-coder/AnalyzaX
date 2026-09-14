"use client";

import React, { useState } from "react";
import { MethodCatalogItem } from "@/types/statistics";

interface StatisticsMethodSelectorProps {
  methods: MethodCatalogItem[];
  selectedMethod: string;
  onSelectMethod: (method: string) => void;
}

export const StatisticsMethodSelector: React.FC<StatisticsMethodSelectorProps> = ({
  methods,
  selectedMethod,
  onSelectMethod,
}) => {
  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");

  const beginnerOptions = [
    {
      id: "compare_two",
      title: "Compare Two Groups",
      desc: "Test if an outcome differs between two distinct groups (e.g. Treatment vs Control).",
      defaultMethod: "t_test_welch",
    },
    {
      id: "compare_multi",
      title: "Compare Multiple Groups",
      desc: "Evaluate differences across 3 or more groups with post-hoc comparisons.",
      defaultMethod: "anova_oneway",
    },
    {
      id: "correlation",
      title: "Find Relationships & Correlations",
      desc: "Examine strength, direction, and significance of association between numerical variables.",
      defaultMethod: "pearson",
    },
    {
      id: "distribution",
      title: "Analyze Distribution & Outliers",
      desc: "Inspect histograms, normality tests, and Tukey IQR outlier fences.",
      defaultMethod: "distribution_analysis",
    },
    {
      id: "categorical",
      title: "Test Categorical Association",
      desc: "Contingency table analysis, Chi-Square independence, and Fisher's exact test.",
      defaultMethod: "chi_square",
    },
    {
      id: "regression",
      title: "Fit Linear Model (OLS)",
      desc: "Inferential linear regression with coefficient standard errors, R², and diagnostics.",
      defaultMethod: "ols_regression",
    },
    {
      id: "descriptive",
      title: "Summary Statistics",
      desc: "Comprehensive parametric and non-parametric descriptive statistics.",
      defaultMethod: "descriptive_summary",
    },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Mode Switcher */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
          Analytical Intent & Method
        </span>
        <div style={{ display: "flex", gap: "0.25rem", background: "var(--bg-subtle)", padding: "0.2rem", borderRadius: "6px" }}>
          <button
            type="button"
            onClick={() => setMode("beginner")}
            className={`btn btn-xs ${mode === "beginner" ? "btn-primary" : "btn-ghost"}`}
          >
            Guided
          </button>
          <button
            type="button"
            onClick={() => setMode("advanced")}
            className={`btn btn-xs ${mode === "advanced" ? "btn-primary" : "btn-ghost"}`}
          >
            Advanced Catalog
          </button>
        </div>
      </div>

      {mode === "beginner" ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.75rem" }}>
          {beginnerOptions.map((opt) => {
            const isSelected = selectedMethod === opt.defaultMethod;
            return (
              <div
                key={opt.id}
                onClick={() => onSelectMethod(opt.defaultMethod)}
                style={{
                  padding: "0.875rem 1rem",
                  borderRadius: "8px",
                  background: isSelected ? "var(--primary-subtle, rgba(59, 130, 246, 0.12))" : "var(--bg-surface, rgba(255, 255, 255, 0.02))",
                  border: `1px solid ${isSelected ? "var(--primary, #3b82f6)" : "var(--border-subtle, rgba(255, 255, 255, 0.08))"}`,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.875rem", color: isSelected ? "var(--primary)" : "var(--text-primary)", marginBottom: "0.25rem" }}>
                  {opt.title}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                  {opt.desc}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "0.5rem" }}>
            {methods.map((m) => {
              const isSelected = selectedMethod === m.method;
              return (
                <div
                  key={m.method}
                  onClick={() => onSelectMethod(m.method)}
                  style={{
                    padding: "0.75rem 1rem",
                    borderRadius: "6px",
                    background: isSelected ? "var(--primary-subtle, rgba(59, 130, 246, 0.12))" : "var(--bg-surface, rgba(255, 255, 255, 0.02))",
                    border: `1px solid ${isSelected ? "var(--primary, #3b82f6)" : "var(--border-subtle, rgba(255, 255, 255, 0.08))"}`,
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.2rem" }}>
                    <span style={{ fontWeight: 600, fontSize: "0.8125rem", color: isSelected ? "var(--primary)" : "var(--text-primary)" }}>
                      {m.name}
                    </span>
                    <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      {m.category}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.3 }}>
                    {m.description}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
