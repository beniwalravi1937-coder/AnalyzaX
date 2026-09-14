import React from "react";
import { ChartSpec } from "@/types";
import { EDAIcon } from "@/components/icons";

interface ChartContainerProps {
  spec: ChartSpec;
  height?: string;
  hasData?: boolean;
  emptyMessage?: string;
  children?: React.ReactNode;
}

export function ChartContainer({
  spec,
  height = "320px",
  hasData = false,
  emptyMessage = "No chart data available. Connect a dataset to visualize.",
  children,
}: ChartContainerProps) {
  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: height,
      }}
    >
      {/* Chart Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1rem",
          paddingBottom: "0.6rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h3
            style={{
              fontSize: "0.9375rem",
              fontWeight: 600,
              color: "var(--text-primary)",
            }}
          >
            {spec.title}
          </h3>
          <span className="badge badge-indigo" style={{ fontSize: "0.625rem" }}>
            {(spec.chart_type || spec.type || "CHART").toUpperCase()}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span
            style={{
              fontSize: "0.6875rem",
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {spec.x_field || spec.x ? `x: ${spec.x_field || spec.x}` : ""}
            {(spec.y_field || spec.y) ? ` | y: ${spec.y_field || spec.y}` : ""}
          </span>
        </div>
      </div>

      {/* Chart Body or Empty State */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "rgba(255, 255, 255, 0.015)",
          borderRadius: "var(--radius-sm)",
          border: "1px dashed var(--border-subtle)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {hasData && children ? (
          children
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              padding: "1.5rem",
              color: "var(--text-muted)",
              gap: "0.5rem",
            }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                backgroundColor: "rgba(99, 102, 241, 0.08)",
                color: "#818cf8",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <EDAIcon size={18} />
            </div>
            <p style={{ fontSize: "0.8125rem", maxWidth: "280px", lineHeight: 1.4 }}>
              {emptyMessage}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
