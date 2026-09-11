"use client";

import React from "react";
import { ComponentDataResponse } from "@/types/dashboard";

interface EdaFindingWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function EdaFindingWidget({ dataResp, configuration }: EdaFindingWidgetProps) {
  const finding = dataResp?.data || configuration.finding || {};
  const title = finding.title || "Data Discovery";
  const severity = (finding.severity || "INFO").toUpperCase();
  const description = finding.description || "No description provided.";
  const evidence = finding.evidence;

  const severityColor =
    severity === "CRITICAL"
      ? "#ef4444"
      : severity === "HIGH"
      ? "#f97316"
      : severity === "MEDIUM"
      ? "#eab308"
      : "#38bdf8";

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between" }}>
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
          <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "#ffffff" }}>{title}</h4>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              padding: "0.15rem 0.5rem",
              borderRadius: "4px",
              background: `${severityColor}22`,
              color: severityColor,
              border: `1px solid ${severityColor}55`,
            }}
          >
            {severity}
          </span>
        </div>

        <p style={{ margin: 0, fontSize: "0.85rem", color: "#cbd5e1", lineHeight: 1.5 }}>
          {description}
        </p>
      </div>

      {evidence && (
        <div style={{ fontSize: "0.75rem", color: "#94a3b8", background: "rgba(15, 23, 42, 0.4)", padding: "0.4rem 0.6rem", borderRadius: "4px", marginTop: "0.5rem" }}>
          <strong>Evidence:</strong> {typeof evidence === "object" ? JSON.stringify(evidence) : String(evidence)}
        </div>
      )}
    </div>
  );
}
