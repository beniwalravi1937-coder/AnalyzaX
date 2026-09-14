"use client";

import React from "react";
import Link from "next/link";
import { ComponentDataResponse } from "@/types/dashboard";

interface AiInsightWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function AiInsightWidget({ dataResp, configuration }: AiInsightWidgetProps) {
  const insight = dataResp?.data || configuration.insight || {};
  const summary = insight.summary || insight.response_text || "No AI insight recorded.";
  const sessionId = insight.session_id;
  const evidenceRefs: string[] = insight.evidence_references || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between" }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              background: "linear-gradient(135deg, rgba(99,102,241,0.3) 0%, rgba(168,85,247,0.3) 100%)",
              color: "#c084fc",
              padding: "0.2rem 0.5rem",
              borderRadius: "4px",
              border: "1px solid rgba(168,85,247,0.4)",
            }}
          >
            AI Analyst Grounded Synthesis
          </span>
        </div>

        <p style={{ margin: 0, fontSize: "0.875rem", color: "#e2e8f0", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
          {summary}
        </p>
      </div>

      <div style={{ borderTop: "1px solid rgba(51, 65, 85, 0.4)", paddingTop: "0.5rem", marginTop: "0.5rem" }}>
        {evidenceRefs.length > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap", marginBottom: "0.25rem" }}>
            <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Evidence:</span>
            {evidenceRefs.map((ref) => (
              <span
                key={ref}
                style={{
                  fontSize: "0.65rem",
                  fontFamily: "monospace",
                  background: "rgba(30, 41, 59, 0.8)",
                  color: "#38bdf8",
                  padding: "0.1rem 0.35rem",
                  borderRadius: "3px",
                  border: "1px solid rgba(56, 189, 248, 0.3)",
                }}
              >
                {ref}
              </span>
            ))}
          </div>
        )}

        {sessionId && (
          <Link
            href="/ai-analyst"
            style={{ fontSize: "0.75rem", color: "#818cf8", textDecoration: "none" }}
          >
            Open in AI Analyst Studio →
          </Link>
        )}
      </div>
    </div>
  );
}
