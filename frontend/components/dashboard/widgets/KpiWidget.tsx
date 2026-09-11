"use client";

import React from "react";
import { ComponentDataResponse } from "@/types/dashboard";

interface KpiWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function KpiWidget({ dataResp, configuration }: KpiWidgetProps) {
  const data = dataResp?.data || {};
  const rawValue = data.value !== undefined ? data.value : configuration.value;
  const metric = data.metric || configuration.metric || "Metric";
  const column = data.column || configuration.column;
  const formatting = data.formatting || configuration.formatting || "compact";
  const comparison = data.comparison || configuration.comparison;

  const formattedValue = React.useMemo(() => {
    if (rawValue === null || rawValue === undefined) return "—";
    const num = Number(rawValue);
    if (isNaN(num)) return String(rawValue);

    if (formatting === "currency") {
      return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(num);
    }
    if (formatting === "percentage") {
      return `${(num * 100).toFixed(1)}%`;
    }
    if (formatting === "compact") {
      return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(num);
    }
    if (formatting === "integer") {
      return Math.round(num).toLocaleString();
    }
    return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }, [rawValue, formatting]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "center" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: "0.75rem", marginBottom: "0.25rem" }}>
        <span style={{ fontSize: "2rem", fontWeight: 700, color: "#ffffff", letterSpacing: "-0.03em" }}>
          {formattedValue}
        </span>
        {comparison && (
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "0.15rem 0.45rem",
              borderRadius: "4px",
              background: comparison.startsWith("+") ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
              color: comparison.startsWith("+") ? "#34d399" : "#f87171",
            }}
          >
            {comparison}
          </span>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem", color: "#94a3b8" }}>
        <span style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
          {metric}
        </span>
        {column && (
          <>
            <span>•</span>
            <code style={{ fontSize: "0.75rem", color: "#cbd5e1" }}>{column}</code>
          </>
        )}
      </div>
    </div>
  );
}
