"use client";

import React from "react";
import { EDAResponse, EDAFinding } from "@/types";
import { EdaVisualizer } from "./EdaVisualizer";
import { SectionCard } from "@/components/ui/SectionCard";
import { AlertCircleIcon, CheckIcon, EDAIcon } from "@/components/icons";

interface OverviewTabProps {
  report: EDAResponse;
  onSelectTab: (tab: string) => void;
}

export function OverviewTab({ report, onSelectTab }: OverviewTabProps) {
  const { overview, findings, charts } = report;

  const missingChart = charts.find((c) => c.chart_id === "missingness_bars");
  const criticalFindings = findings.filter(
    (f) => f.severity === "critical" || f.severity === "warning"
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* 1. Top KPI Metric Cards */}
      <div className="grid-4" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
        {/* Row Count */}
        <div className="card" style={{ padding: "1.25rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
            Total Observations
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.35rem" }}>
            {overview.row_count.toLocaleString()}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Dataset Version: <span style={{ fontFamily: "var(--font-mono)", color: "var(--color-primary)" }}>{overview.version_id}</span>
          </div>
        </div>

        {/* Column Composition */}
        <div className="card" style={{ padding: "1.25rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
            Feature Columns
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.35rem" }}>
            {overview.column_count}
          </div>
          <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.4rem", flexWrap: "wrap" }}>
            <span className="badge badge-indigo" style={{ fontSize: "0.6875rem" }}>
              {overview.numeric_columns_count} Num
            </span>
            <span className="badge badge-emerald" style={{ fontSize: "0.6875rem" }}>
              {overview.categorical_columns_count} Cat
            </span>
            <span className="badge badge-amber" style={{ fontSize: "0.6875rem" }}>
              {overview.datetime_columns_count} Date
            </span>
          </div>
        </div>

        {/* Missing Cells */}
        <div className="card" style={{ padding: "1.25rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
            Data Sparsity
          </div>
          <div
            style={{
              fontSize: "1.75rem",
              fontWeight: 700,
              color: overview.missing_percentage > 5 ? "#f43f5e" : "#10b981",
              marginTop: "0.35rem",
            }}
          >
            {overview.missing_percentage.toFixed(2)}%
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            {overview.total_missing_cells.toLocaleString()} missing cells
          </div>
        </div>

        {/* Duplicate Rows & Anomalies */}
        <div className="card" style={{ padding: "1.25rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
            Integrity & Outliers
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.35rem" }}>
            {overview.anomalies_detected_count}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            {overview.duplicate_rows_count} duplicate rows ({overview.duplicate_percentage.toFixed(1)}%)
          </div>
        </div>
      </div>

      {/* 2. Middle Section: Automated Findings & Missingness Chart */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: "1.5rem" }}>
        {/* Top Insights / Findings Preview */}
        <SectionCard
          title="Automated EDA Findings"
          subtitle={`${findings.length} analytical discoveries detected`}
          action={
            <button
              onClick={() => onSelectTab("findings")}
              className="btn btn-ghost"
              style={{ fontSize: "0.75rem" }}
            >
              View All ({findings.length}) →
            </button>
          }
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "320px", overflowY: "auto" }}>
            {criticalFindings.length === 0 ? (
              <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                <CheckIcon size={24} style={{ color: "#10b981", margin: "0 auto 0.5rem" }} />
                No critical data quality or distribution anomalies detected.
              </div>
            ) : (
              criticalFindings.slice(0, 4).map((f) => (
                <FindingSummaryCard key={f.finding_id || (f as any).id || f.title} finding={f} />
              ))
            )}
          </div>
        </SectionCard>

        {/* Missingness Profile Chart */}
        <SectionCard
          title="Feature Missingness Rate"
          subtitle={
            missingChart
              ? missingChart.description || "Percentage of missing values per column"
              : "No column has missing values"
          }
        >
          {missingChart && missingChart.data && missingChart.data.length > 0 ? (
            <EdaVisualizer spec={missingChart} height={260} />
          ) : (
            <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
              <CheckIcon size={24} style={{ color: "#10b981", margin: "0 auto 0.5rem" }} />
              100% complete dataset. No missing values across any column.
            </div>
          )}
        </SectionCard>
      </div>

      {/* 3. Quick Action Jump Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem" }}>
        <div
          className="card"
          style={{ padding: "1.25rem", cursor: "pointer", border: "1px solid var(--border-subtle)", transition: "all 0.2s" }}
          onClick={() => onSelectTab("univariate")}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "1.2rem" }}>📊</span>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Univariate Feature Explorer
            </h4>
          </div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Inspect distributions, histograms, box plots, IQR fences, and cardinality for all {overview.column_count} features.
          </p>
        </div>

        <div
          className="card"
          style={{ padding: "1.25rem", cursor: "pointer", border: "1px solid var(--border-subtle)", transition: "all 0.2s" }}
          onClick={() => onSelectTab("correlations")}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "1.2rem" }}>🔥</span>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Correlation Matrix
            </h4>
          </div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Explore Pearson, Spearman, and Kendall rank correlations across {overview.numeric_columns_count} numerical variables.
          </p>
        </div>

        <div
          className="card"
          style={{ padding: "1.25rem", cursor: "pointer", border: "1px solid var(--border-subtle)", transition: "all 0.2s" }}
          onClick={() => onSelectTab("relationships")}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "1.2rem" }}>⚡</span>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Relationship Studio
            </h4>
          </div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Select any pair of features to generate dynamic scatter plots, regression lines, or ANOVA category distributions.
          </p>
        </div>
      </div>
    </div>
  );
}

function FindingSummaryCard({ finding }: { finding: EDAFinding }) {
  const normSev = String(finding.severity || "").toLowerCase();
  const isCritical = normSev === "critical" || normSev === "high";
  const isWarning = normSev === "warning" || normSev === "medium";
  const badgeClass = isCritical ? "badge-rose" : (isWarning ? "badge-amber" : "badge-indigo");
  const msg = finding.message || finding.description || "";

  return (
    <div
      style={{
        padding: "0.75rem 1rem",
        backgroundColor: isCritical
          ? "rgba(244, 63, 94, 0.06)"
          : isWarning
          ? "rgba(245, 158, 11, 0.06)"
          : "rgba(99, 102, 241, 0.06)",
        border: `1px solid ${
          isCritical
            ? "rgba(244, 63, 94, 0.2)"
            : isWarning
            ? "rgba(245, 158, 11, 0.2)"
            : "rgba(99, 102, 241, 0.2)"
        }`,
        borderRadius: "var(--radius-sm)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.25rem" }}>
        <span className={`badge ${badgeClass}`} style={{ fontSize: "0.6875rem", textTransform: "uppercase" }}>
          {normSev || "INFO"}
        </span>
        <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "capitalize" }}>
          {finding.category}
        </span>
      </div>
      <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
        {finding.title}
      </div>
      {msg && (
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.2rem", lineHeight: 1.4 }}>
          {msg}
        </div>
      )}
    </div>
  );
}
