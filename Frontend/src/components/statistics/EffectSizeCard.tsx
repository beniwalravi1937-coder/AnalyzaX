"use client";

import React from "react";
import { EffectSize } from "@/types/statistics";

interface EffectSizeCardProps {
  effect: EffectSize;
}

export const EffectSizeCard: React.FC<EffectSizeCardProps> = ({ effect }) => {
  const getBadgeColor = (interp: string) => {
    switch (interp.toLowerCase()) {
      case "large":
        return { bg: "rgba(16, 185, 129, 0.15)", text: "#10b981", border: "rgba(16, 185, 129, 0.3)" };
      case "medium":
        return { bg: "rgba(59, 130, 246, 0.15)", text: "#3b82f6", border: "rgba(59, 130, 246, 0.3)" };
      case "small":
        return { bg: "rgba(245, 158, 11, 0.15)", text: "#f59e0b", border: "rgba(245, 158, 11, 0.3)" };
      default:
        return { bg: "rgba(156, 163, 175, 0.15)", text: "#9ca3af", border: "rgba(156, 163, 175, 0.3)" };
    }
  };

  const badge = getBadgeColor(effect.interpretation);

  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: "var(--radius-md, 8px)",
        background: "var(--bg-subtle, rgba(255, 255, 255, 0.03))",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
          {effect.metric_name.replace(/_/g, " ")}
        </span>
        <span
          style={{
            fontSize: "0.7rem",
            padding: "0.15rem 0.45rem",
            borderRadius: "4px",
            background: badge.bg,
            color: badge.text,
            border: `1px solid ${badge.border}`,
            fontWeight: 600,
            textTransform: "capitalize",
          }}
        >
          {effect.interpretation} Effect
        </span>
      </div>

      <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "monospace" }}>
        {effect.value.toFixed(4)}
      </div>

      <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
        Standardized practical magnitude indication based on academic benchmark guidelines.
      </div>
    </div>
  );
};
