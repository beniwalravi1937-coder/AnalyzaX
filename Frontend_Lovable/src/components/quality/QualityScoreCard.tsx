"use client";

import React, { useState } from "react";
import { DataQualityReportResponse } from "@/types";
import { CheckIcon, AlertCircleIcon, RefreshIcon } from "@/components/icons";

interface QualityScoreCardProps {
  report: DataQualityReportResponse;
  datasetName?: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function QualityScoreCard({
  report,
  datasetName,
  onRefresh,
  isRefreshing = false,
}: QualityScoreCardProps) {
  const [showFormula, setShowFormula] = useState(false);

  const score = report.overall_score;
  const grade = report.overall_grade;

  // Grade badge styling
  const gradeBadgeClass =
    score >= 90
      ? "badge-emerald"
      : score >= 75
      ? "badge-indigo"
      : score >= 60
      ? "badge-amber"
      : "badge-rose";

  const scoreColor =
    score >= 90
      ? "#10b981"
      : score >= 75
      ? "#6366f1"
      : score >= 60
      ? "#f59e0b"
      : "#f43f5e";

  return (
    <div
      style={{
        padding: "1.5rem",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "1.5rem",
        }}
      >
        {/* Left Side: Score & Rating */}
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          {/* Radial/Circular Score Display */}
          <div
            style={{
              width: "84px",
              height: "84px",
              borderRadius: "50%",
              background: `conic-gradient(${scoreColor} ${score * 3.6}deg, rgba(255, 255, 255, 0.06) 0deg)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "6px",
              boxShadow: `0 0 20px -5px ${scoreColor}40`,
            }}
          >
            <div
              style={{
                width: "100%",
                height: "100%",
                borderRadius: "50%",
                backgroundColor: "var(--bg-surface)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <span
                style={{
                  fontSize: "1.35rem",
                  fontWeight: 800,
                  color: "var(--text-primary)",
                  lineHeight: 1,
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {score.toFixed(1)}
              </span>
              <span
                style={{
                  fontSize: "0.625rem",
                  color: "var(--text-muted)",
                  marginTop: "2px",
                  fontWeight: 600,
                }}
              >
                / 100
              </span>
            </div>
          </div>

          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h2
                style={{
                  fontSize: "1.25rem",
                  fontWeight: 700,
                  color: "var(--text-primary)",
                  margin: 0,
                }}
              >
                Overall Dataset Health
              </h2>
              <span className={`badge ${gradeBadgeClass}`} style={{ fontWeight: 700 }}>
                {grade}
              </span>
            </div>

            <p
              style={{
                fontSize: "0.8125rem",
                color: "var(--text-muted)",
                marginTop: "0.25rem",
                marginBottom: "0.5rem",
                maxWidth: "500px",
                lineHeight: 1.4,
              }}
            >
              {datasetName ? (
                <>
                  Evaluated on <strong>{datasetName}</strong> ({report.dataset_version}) •{" "}
                </>
              ) : null}
              {report.total_issues === 0
                ? "Optimal quality standards met. Zero anomalies detected."
                : `${report.total_issues} quality issue(s) identified across ${report.affected_columns} column(s).`}
            </p>

            <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-faint)" }}>
                Engine: <code>{report.quality_report_version}</code>
              </span>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-faint)" }}>
                Audited in {report.execution_time_ms.toFixed(1)}ms
              </span>
              <button
                type="button"
                onClick={() => setShowFormula(!showFormula)}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  color: "var(--primary, #6366f1)",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                {showFormula ? "Hide formula" : "How is this score computed?"}
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Refresh Button */}
        {onRefresh && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onRefresh}
            disabled={isRefreshing}
            style={{ fontSize: "0.8125rem", padding: "0.4rem 0.85rem" }}
          >
            <RefreshIcon
              size={14}
              style={{
                animation: isRefreshing ? "spin 1s linear infinite" : "none",
              }}
            />
            <span>{isRefreshing ? "Auditing..." : "Re-audit Dataset"}</span>
          </button>
        )}
      </div>

      {/* Expandable Scoring Formula & Rationale */}
      {showFormula && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "1rem",
            backgroundColor: "rgba(255, 255, 255, 0.02)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-sm)",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
            Deterministic Scoring Methodology ({report.quality_report_version})
          </div>
          <p style={{ margin: "0 0 0.5rem 0" }}>{report.scoring_explanation}</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.5rem" }}>
            <div>Completeness: <strong>25% weight</strong></div>
            <div>Validity: <strong>25% weight</strong></div>
            <div>Uniqueness: <strong>20% weight</strong></div>
            <div>Consistency: <strong>15% weight</strong></div>
            <div>Integrity: <strong>10% weight</strong></div>
            <div>Anomaly Risk: <strong>5% weight</strong></div>
          </div>
        </div>
      )}
    </div>
  );
}
