"use client";

import React, { useState } from "react";
import { ToolResult } from "@/types/ai_analyst";
import { CheckIcon, AlertCircleIcon } from "@/components/icons";

interface ToolExecutionIndicatorProps {
  toolResults: ToolResult[];
}

export function ToolExecutionIndicator({ toolResults }: ToolExecutionIndicatorProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!toolResults || toolResults.length === 0) return null;

  return (
    <div
      style={{
        margin: "0.75rem 0",
        background: "rgba(0, 0, 0, 0.2)",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
        borderRadius: "0.5rem",
        overflow: "hidden",
      }}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: "100%",
          padding: "0.5rem 0.75rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "transparent",
          border: "none",
          color: "var(--text-secondary)",
          fontSize: "0.8rem",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>⚙️</span>
          <strong>How I analyzed this:</strong> {toolResults.length} analytical engine {toolResults.length === 1 ? "call" : "calls"}
        </span>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          {isExpanded ? "▲ Hide" : "▼ Show details"}
        </span>
      </button>

      {isExpanded && (
        <div style={{ padding: "0.5rem 0.75rem", borderTop: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))" }}>
          {toolResults.map((tr, i) => {
            const isSuccess = tr.status === "completed";
            return (
              <div
                key={tr.call_id || i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.35rem 0",
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ color: "var(--accent-primary, #6366f1)" }}>{tr.tool_id}</span>
                  {tr.provenance?.sql && (
                    <span style={{ color: "var(--text-muted)", maxWidth: "240px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      `{tr.provenance.sql}`
                    </span>
                  )}
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  {isSuccess ? (
                    <span style={{ color: "var(--emerald-500, #10b981)", display: "flex", alignItems: "center", gap: "0.2rem" }}>
                      <CheckIcon size={12} />
                      {tr.execution_time_ms ? `${Math.round(tr.execution_time_ms)}ms` : "Done"}
                    </span>
                  ) : (
                    <span style={{ color: "var(--red-500, #ef4444)", display: "flex", alignItems: "center", gap: "0.2rem" }}>
                      <AlertCircleIcon size={12} />
                      Failed
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
