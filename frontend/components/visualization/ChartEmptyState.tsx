"use client";

import React from "react";
import { BarChartIcon } from "@/components/icons";

interface ChartEmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  height?: string | number;
}

export function ChartEmptyState({
  title = "No visualization data",
  description = "Select fields in the builder or choose a recommendation to render a chart.",
  actionLabel,
  onAction,
  height = 360,
}: ChartEmptyStateProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: typeof height === "number" ? `${height}px` : height,
        padding: "2rem",
        backgroundColor: "rgba(15, 23, 42, 0.2)",
        borderRadius: "0.5rem",
        border: "1px dashed var(--border-subtle)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "12px",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "1rem",
          color: "var(--brand-primary, #6366f1)",
        }}
      >
        <BarChartIcon size={24} />
      </div>
      <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
        {title}
      </div>
      <div
        style={{
          fontSize: "0.825rem",
          color: "var(--text-secondary)",
          marginTop: "0.25rem",
          maxWidth: "380px",
        }}
      >
        {description}
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="btn btn-primary btn-sm"
          style={{ marginTop: "1rem" }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
