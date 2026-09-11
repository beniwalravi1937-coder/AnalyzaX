"use client";

import React from "react";
import { AlertTriangleIcon } from "@/components/icons";

interface ChartErrorStateProps {
  title?: string;
  error: string;
  warnings?: string[];
  onRetry?: () => void;
  height?: string | number;
}

export function ChartErrorState({
  title = "Visualization Error",
  error,
  warnings,
  onRetry,
  height = 360,
}: ChartErrorStateProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: typeof height === "number" ? `${height}px` : height,
        padding: "2rem",
        backgroundColor: "rgba(239, 68, 68, 0.05)",
        borderRadius: "0.5rem",
        border: "1px solid rgba(239, 68, 68, 0.25)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "12px",
          backgroundColor: "rgba(239, 68, 68, 0.15)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "1rem",
          color: "var(--status-danger, #ef4444)",
        }}
      >
        <AlertTriangleIcon size={24} />
      </div>
      <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--status-danger, #ef4444)" }}>
        {title}
      </div>
      <div
        style={{
          fontSize: "0.825rem",
          color: "var(--text-secondary)",
          marginTop: "0.5rem",
          maxWidth: "480px",
          wordBreak: "break-word",
          fontFamily: "monospace",
          backgroundColor: "rgba(0, 0, 0, 0.2)",
          padding: "0.5rem 0.75rem",
          borderRadius: "0.375rem",
        }}
      >
        {error}
      </div>

      {warnings && warnings.length > 0 && (
        <div style={{ marginTop: "0.75rem", textAlign: "left", maxWidth: "480px" }}>
          {warnings.map((w, idx) => (
            <div
              key={idx}
              style={{
                fontSize: "0.75rem",
                color: "var(--status-warning, #f59e0b)",
                marginBottom: "0.25rem",
              }}
            >
              ⚠ {w}
            </div>
          ))}
        </div>
      )}

      {onRetry && (
        <button
          onClick={onRetry}
          className="btn btn-secondary btn-sm"
          style={{ marginTop: "1rem" }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
