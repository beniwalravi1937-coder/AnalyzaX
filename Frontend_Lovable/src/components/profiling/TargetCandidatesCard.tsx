"use client";

import React from "react";
import { TargetCandidate } from "@/types";
import { MLIcon } from "@/components/icons";

interface TargetCandidatesCardProps {
  candidates: TargetCandidate[];
}

export function TargetCandidatesCard({ candidates }: TargetCandidatesCardProps) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        padding: "1.25rem 1.5rem",
        backgroundColor: "rgba(99, 102, 241, 0.04)",
        border: "1px solid rgba(99, 102, 241, 0.25)",
        borderRadius: "var(--radius-lg)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.85rem" }}>
        <div
          style={{
            width: "28px",
            height: "28px",
            borderRadius: "6px",
            backgroundColor: "rgba(99, 102, 241, 0.15)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--accent-indigo)",
          }}
        >
          <MLIcon size={16} />
        </div>
        <div>
          <h4 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Machine Learning Target Variable Recommendations
          </h4>
          <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Automatically detected candidate outcomes suitable for supervised model training
          </p>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        {candidates.map((cand, idx) => {
          const isBinary = cand.task_type === "binary_classification";
          const isReg = cand.task_type === "regression";
          const badgeClass = isBinary ? "badge-emerald" : isReg ? "badge-indigo" : "badge-amber";

          return (
            <div
              key={idx}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.65rem 0.9rem",
                backgroundColor: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                flexWrap: "wrap",
                gap: "0.5rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <span style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.875rem" }}>
                  {cand.column_name}
                </span>
                <span className={`badge ${badgeClass}`} style={{ fontSize: "0.6875rem" }}>
                  {cand.task_type.replace("_", " ")}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {Math.round(cand.confidence * 100)}% confidence
                </span>
              </div>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                {cand.reason}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
