"use client";

import React from "react";
import { ComponentDataResponse } from "@/types/dashboard";

interface StatisticsWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function StatisticsWidget({ dataResp, configuration }: StatisticsWidgetProps) {
  const result = dataResp?.data || configuration.result || {};
  const method = result.method || "Hypothesis Test";
  const statistic = result.statistic;
  const pValue = result.p_value ?? result.pValue;
  const decision = result.decision;
  const interpretation = result.interpretation || result.conclusion;
  const requiresRecomp = dataResp?.requires_recomputation;
  const recompReason = dataResp?.recomputation_reason;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between" }}>
      {/* Warning banner if filtered */}
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
        <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#818cf8", marginBottom: "0.5rem" }}>
          {method}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "0.5rem" }}>
          <div style={{ background: "rgba(15, 23, 42, 0.5)", padding: "0.5rem", borderRadius: "6px" }}>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", textTransform: "uppercase" }}>Test Statistic</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
              {statistic !== undefined ? Number(statistic).toFixed(3) : "—"}
            </div>
          </div>
          <div style={{ background: "rgba(15, 23, 42, 0.5)", padding: "0.5rem", borderRadius: "6px" }}>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", textTransform: "uppercase" }}>p-value</div>
            <div
              style={{
                fontSize: "1.1rem",
                fontWeight: 700,
                color: pValue !== undefined && pValue < 0.05 ? "#34d399" : "#f87171",
              }}
            >
              {pValue !== undefined ? Number(pValue).toFixed(4) : "—"}
            </div>
          </div>
        </div>

        {decision && (
          <div style={{ fontSize: "0.8rem", color: "#e2e8f0", marginBottom: "0.25rem" }}>
            <strong>Decision:</strong> {decision}
          </div>
        )}
      </div>

      {interpretation && (
        <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontStyle: "italic", borderTop: "1px solid rgba(51, 65, 85, 0.4)", paddingTop: "0.4rem" }}>
          {interpretation}
        </div>
      )}
    </div>
  );
}
