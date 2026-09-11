"use client";

import React from "react";
import { ComponentDataResponse } from "@/types/dashboard";

interface ForecastWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function ForecastWidget({ dataResp, configuration }: ForecastWidgetProps) {
  const result = dataResp?.data || configuration.result || {};
  const horizon = result.horizon || 30;
  const model = result.model || "ARIMA / Exponential Smoothing";
  const metrics = result.metrics || {};
  const mape = metrics.mape !== undefined ? metrics.mape : result.mape;
  const predictedTotal = result.predicted_total;
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
          <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#ffffff" }}>{model}</span>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 600,
              background: "rgba(14, 165, 233, 0.2)",
              color: "#38bdf8",
              padding: "0.15rem 0.45rem",
              borderRadius: "4px",
            }}
          >
            {horizon}-Day Horizon
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.5rem" }}>
          <div style={{ background: "rgba(15, 23, 42, 0.5)", padding: "0.5rem", borderRadius: "6px" }}>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", textTransform: "uppercase" }}>Backtest MAPE</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#34d399" }}>
              {mape !== undefined ? `${Number(mape).toFixed(1)}%` : "—"}
            </div>
          </div>
          <div style={{ background: "rgba(15, 23, 42, 0.5)", padding: "0.5rem", borderRadius: "6px" }}>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", textTransform: "uppercase" }}>Projected Volume</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#ffffff" }}>
              {predictedTotal !== undefined ? Number(predictedTotal).toLocaleString() : "—"}
            </div>
          </div>
        </div>
      </div>

      <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
        Forecast derived from Phase 12 temporal models.
      </div>
    </div>
  );
}
