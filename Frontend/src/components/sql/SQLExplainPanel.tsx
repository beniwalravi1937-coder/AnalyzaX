"use client";

import React from "react";
import { SQLExplainResult } from "@/types";
import { EyeIcon, CopyIcon, CheckIcon } from "@/components/icons";

interface SQLExplainPanelProps {
  plan: SQLExplainResult | null;
  loading?: boolean;
}

export function SQLExplainPanel({ plan, loading = false }: SQLExplainPanelProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    if (plan?.plan_text) {
      navigator.clipboard.writeText(plan.plan_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <div className="spinner-border spinner-border-sm" style={{ marginBottom: "0.5rem" }} />
        <div style={{ fontSize: "0.8125rem" }}>Generating physical execution plan...</div>
      </div>
    );
  }

  if (!plan) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <EyeIcon size={28} style={{ marginBottom: "0.5rem", opacity: 0.5 }} />
        <div style={{ fontWeight: 500, fontSize: "0.875rem" }}>No execution plan generated</div>
        <div style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
          Click "Explain" in the editor toolbar to inspect DuckDB's scan, projection, and join operators.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.6rem 0.75rem",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span className="badge badge-indigo" style={{ fontSize: "0.6875rem" }}>
            DuckDB Physical Plan
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Analysis time: {plan.execution_time_ms} ms
          </span>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="btn btn-secondary btn-sm"
          style={{ fontSize: "0.6875rem", padding: "0.2rem 0.5rem" }}
        >
          {copied ? <CheckIcon size={12} color="var(--color-success)" /> : <CopyIcon size={12} />}
          {copied ? "Copied" : "Copy Plan"}
        </button>
      </div>

      {/* Plan Body */}
      <div style={{ flex: 1, overflow: "auto", padding: "1rem" }}>
        <pre
          style={{
            fontFamily: "var(--font-mono, monospace)",
            fontSize: "0.75rem",
            lineHeight: 1.5,
            color: "var(--text-primary)",
            backgroundColor: "var(--bg-input)",
            padding: "1rem",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border-subtle)",
            whiteSpace: "pre",
            margin: 0,
          }}
        >
          {plan.plan_text}
        </pre>
      </div>
    </div>
  );
}
