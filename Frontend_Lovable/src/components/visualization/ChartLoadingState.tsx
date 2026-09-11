"use client";

import React from "react";

interface ChartLoadingStateProps {
  message?: string;
  subtext?: string;
  height?: string | number;
}

export function ChartLoadingState({
  message = "Rendering visualization...",
  subtext = "Computing deterministic aggregations & rendering marks",
  height = 360,
}: ChartLoadingStateProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: typeof height === "number" ? `${height}px` : height,
        padding: "2rem",
        backgroundColor: "rgba(15, 23, 42, 0.3)",
        borderRadius: "0.5rem",
        border: "1px dashed var(--border-subtle)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "50%",
          border: "3px solid rgba(99, 102, 241, 0.2)",
          borderTopColor: "var(--brand-primary, #6366f1)",
          animation: "spin 1s linear infinite",
          marginBottom: "1rem",
        }}
      />
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>
        {message}
      </div>
      {subtext && (
        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
          {subtext}
        </div>
      )}
    </div>
  );
}
