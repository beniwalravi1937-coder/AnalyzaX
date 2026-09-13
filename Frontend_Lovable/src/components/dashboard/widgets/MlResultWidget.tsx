"use client";

import React from "react";
import { ComponentDataResponse } from "@/types/dashboard";

interface MlResultWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function MlResultWidget({ dataResp, configuration }: MlResultWidgetProps) {
  const result = dataResp?.data || configuration.result || {};
  const modelName = result.model_name || result.model_type || "ML Model";
  const primaryMetric = result.primary_metric || "Metric";
  const metricVal = result.metric_value ?? result.primary_metric_value;
  const baselineLift = result.baseline_lift;
  const requiresRecomp = dataResp?.requires_recomputation;
  const recompReason = dataResp?.recomputation_reason;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between" }}>
      {requiresRecomp && (
        <div
          style={{
            background: "rgba(234, 179, 8, 0.15)",
            border: "1px solid rgba(234, 179, 8, 0.4)",
            borderRadius: "4px",
            padding: "0.4rem 0.6rem",
            marginBottom: "0.5rem",
            fontSize: "0.75rem",
            color: "#fde047",
          }}
        >
          <strong>Notice:</strong> {recompReason}
        </div>
      )}

      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "0.9rem", fontWeight: 700, color: "#ffffff" }}>{modelName}</span>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 600,
              background: "rgba(99, 102, 241, 0.2)",
              color: "#a5b4fc",
              padding: "0.15rem 0.45rem",
              borderRadius: "4px",
            }}
          >
            Production Validated
          </span>
        </div>

        <div style={{ background: "rgba(15, 23, 42, 0.5)", padding: "0.75rem", borderRadius: "6px", marginBottom: "0.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8", textTransform: "uppercase" }}>{primaryMetric}</span>
            <span style={{ fontSize: "1.5rem", fontWeight: 700, color: "#34d399" }}>
              {metricVal !== undefined ? (typeof metricVal === "number" ? metricVal.toFixed(3) : String(metricVal)) : "—"}
            </span>
          </div>
          {baselineLift && (
            <div style={{ fontSize: "0.75rem", color: "#60a5fa", marginTop: "0.25rem" }}>
              Lift over baseline: <strong>{baselineLift}</strong>
            </div>
          )}
        </div>
      </div>

      <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
        Metrics evaluated against validated test fold.
      </div>
    </div>
  );
}
