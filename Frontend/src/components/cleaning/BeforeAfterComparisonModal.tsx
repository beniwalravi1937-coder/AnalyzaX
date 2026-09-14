"use client";

import React from "react";
import { QualityComparison, DatasetVersion } from "@/types";
import { CheckIcon, CloseIcon, ArrowRightIcon } from "@/components/icons";
import Link from "next/link";

interface BeforeAfterComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  comparison: QualityComparison | null;
  newVersion: DatasetVersion | null;
  datasetId: string;
}

export function BeforeAfterComparisonModal({
  isOpen,
  onClose,
  comparison,
  newVersion,
  datasetId,
}: BeforeAfterComparisonModalProps) {
  if (!isOpen || !comparison || !newVersion) return null;

  const isPositive = comparison.score_delta >= 0;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1200,
        padding: "1rem",
      }}
    >
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "14px",
          width: "100%",
          maxWidth: "560px",
          overflow: "hidden",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                backgroundColor: "rgba(16, 185, 129, 0.15)",
                color: "#10b981",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CheckIcon size={18} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: "1.05rem", color: "var(--text-primary)" }}>
                Pipeline Successfully Applied
              </h3>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                Created immutable version <strong>{newVersion.version_id}</strong> ({newVersion.version_label})
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-tertiary)",
              cursor: "pointer",
            }}
          >
            <CloseIcon size={18} />
          </button>
        </div>

        {/* Content */}
        <div
          style={{
            padding: "1.5rem",
            display: "flex",
            flexDirection: "column",
            gap: "1.25rem",
            maxHeight: "70vh",
            overflowY: "auto",
          }}
        >
          {/* Quality Scorecard Hero */}
          <div
            style={{
              padding: "1.25rem",
              borderRadius: "10px",
              backgroundColor: "var(--bg-canvas)",
              border: "1px solid var(--border-subtle)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-around",
              textAlign: "center",
            }}
          >
            <div>
              <span style={{ fontSize: "0.72rem", color: "var(--text-tertiary)", fontWeight: 600 }}>
                BEFORE ({comparison.before_version_id})
              </span>
              <div style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-secondary)" }}>
                {comparison.before_score.toFixed(1)}
              </div>
              <span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)" }}>
                Grade: {comparison.before_grade}
              </span>
            </div>

            <div style={{ color: "var(--text-tertiary)" }}>
              <ArrowRightIcon size={20} />
            </div>

            <div>
              <span style={{ fontSize: "0.72rem", color: "var(--accent-primary)", fontWeight: 600 }}>
                AFTER ({comparison.after_version_id})
              </span>
              <div style={{ fontSize: "1.6rem", fontWeight: 700, color: "#10b981" }}>
                {comparison.after_score.toFixed(1)}
              </div>
              <span style={{ fontSize: "0.7rem", color: "#10b981", fontWeight: 600 }}>
                Grade: {comparison.after_grade}
              </span>
            </div>

            <div
              style={{
                padding: "0.5rem 0.75rem",
                borderRadius: "8px",
                backgroundColor: isPositive ? "rgba(16, 185, 129, 0.12)" : "rgba(244, 63, 94, 0.12)",
                border: `1px solid ${isPositive ? "rgba(16, 185, 129, 0.3)" : "rgba(244, 63, 94, 0.3)"}`,
              }}
            >
              <div
                style={{
                  fontSize: "1.1rem",
                  fontWeight: 800,
                  color: isPositive ? "#10b981" : "#f43f5e",
                }}
              >
                {isPositive ? `+${comparison.score_delta.toFixed(1)}` : comparison.score_delta.toFixed(1)}%
              </div>
              <span style={{ fontSize: "0.68rem", color: "var(--text-tertiary)" }}>
                Quality Delta
              </span>
            </div>
          </div>

          {/* Quick Metrics */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div
              style={{
                padding: "0.75rem 1rem",
                backgroundColor: "var(--bg-canvas)",
                borderRadius: "8px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <span style={{ fontSize: "0.72rem", color: "var(--text-tertiary)" }}>
                Quality Issues
              </span>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {comparison.before_total_issues} → {comparison.after_total_issues}
              </div>
              <span style={{ fontSize: "0.7rem", color: "#10b981", fontWeight: 600 }}>
                {comparison.issues_delta > 0
                  ? `-${comparison.issues_delta} issues resolved`
                  : "No new issues"}
              </span>
            </div>

            <div
              style={{
                padding: "0.75rem 1rem",
                backgroundColor: "var(--bg-canvas)",
                borderRadius: "8px",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <span style={{ fontSize: "0.72rem", color: "var(--text-tertiary)" }}>
                Row Count
              </span>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {comparison.metrics_comparison.rows_before} → {comparison.metrics_comparison.rows_after}
              </div>
              <span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)" }}>
                Cleaned dataset active
              </span>
            </div>
          </div>

          {/* Detailed Improvements List */}
          {comparison.improvements.length > 0 && (
            <div>
              <h4
                style={{
                  margin: "0 0 0.5rem 0",
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  color: "var(--text-secondary)",
                }}
              >
                Key Improvements
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                {comparison.improvements.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      fontSize: "0.78rem",
                      color: "var(--text-primary)",
                    }}
                  >
                    <div
                      style={{
                        width: "16px",
                        height: "16px",
                        borderRadius: "50%",
                        backgroundColor: "rgba(16, 185, 129, 0.15)",
                        color: "#10b981",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <CheckIcon size={10} />
                    </div>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "1rem 1.5rem",
            borderTop: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Link
              href={`/quality?dataset=${datasetId}`}
              style={{
                fontSize: "0.78rem",
                color: "var(--accent-primary)",
                textDecoration: "none",
                fontWeight: 600,
              }}
            >
              Inspect Quality Scorecard →
            </Link>
          </div>

          <button
            onClick={onClose}
            style={{
              padding: "0.5rem 1.25rem",
              fontSize: "0.82rem",
              fontWeight: 600,
              borderRadius: "6px",
              border: "none",
              backgroundColor: "var(--accent-primary)",
              color: "#ffffff",
              cursor: "pointer",
            }}
          >
            Continue in Clean Workspace
          </button>
        </div>
      </div>
    </div>
  );
}
