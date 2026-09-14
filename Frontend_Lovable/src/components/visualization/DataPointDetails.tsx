"use client";

import React from "react";

interface DataPointDetailsProps {
  dataPoint: {
    name?: string;
    value?: any;
    seriesName?: string;
    dataIndex?: number;
    raw?: any;
  } | null;
  onClose: () => void;
  onFilterByValue?: (field: string, value: any) => void;
  xField?: string | null;
}

export function DataPointDetails({
  dataPoint,
  onClose,
  onFilterByValue,
  xField,
}: DataPointDetailsProps) {
  if (!dataPoint) return null;

  const displayVal = typeof dataPoint.value === "object" && dataPoint.value !== null
    ? JSON.stringify(dataPoint.value)
    : String(dataPoint.value ?? "N/A");

  return (
    <div
      style={{
        padding: "0.75rem 1rem",
        backgroundColor: "rgba(30, 41, 59, 0.95)",
        borderTop: "1px solid var(--border-subtle)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        fontSize: "0.8rem",
        gap: "1rem",
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "1.25rem", flexWrap: "wrap" }}>
        <div>
          <span style={{ color: "var(--text-muted)", marginRight: "0.35rem" }}>Selected:</span>
          <strong style={{ color: "var(--text-primary)" }}>{dataPoint.name || "Data Point"}</strong>
        </div>

        <div>
          <span style={{ color: "var(--text-muted)", marginRight: "0.35rem" }}>Value:</span>
          <strong style={{ color: "var(--brand-primary, #6366f1)" }}>{displayVal}</strong>
        </div>

        {dataPoint.seriesName && (
          <div>
            <span style={{ color: "var(--text-muted)", marginRight: "0.35rem" }}>Series:</span>
            <span style={{ color: "var(--text-secondary)" }}>{dataPoint.seriesName}</span>
          </div>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        {onFilterByValue && xField && dataPoint.name && (
          <button
            onClick={() => onFilterByValue(xField, dataPoint.name)}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.725rem", padding: "0.2rem 0.5rem" }}
          >
            Filter to &quot;{dataPoint.name}&quot;
          </button>
        )}
        <button
          onClick={onClose}
          className="btn btn-secondary btn-sm"
          style={{ fontSize: "0.725rem", padding: "0.2rem 0.5rem" }}
        >
          ✕
        </button>
      </div>
    </div>
  );
}
