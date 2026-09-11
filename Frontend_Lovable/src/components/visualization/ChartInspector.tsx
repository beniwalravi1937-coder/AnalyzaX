"use client";

import React, { useState } from "react";
import { ChartSpec } from "@/types";
import { CopyIcon, CheckIcon } from "@/components/icons";

interface ChartInspectorProps {
  spec: ChartSpec;
  isOpen: boolean;
  onClose: () => void;
}

export function ChartInspector({ spec, isOpen, onClose }: ChartInspectorProps) {
  const [copied, setCopied] = useState(false);
  const [showJson, setShowJson] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(spec, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const sampling = spec.sampling;
  const provenance = spec.provenance;

  return (
    <div
      style={{
        borderTop: "1px solid var(--border-subtle)",
        backgroundColor: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(8px)",
        padding: "1rem",
        fontSize: "0.8rem",
        color: "var(--text-secondary)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <span style={{ fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          ChartSpec Inspector & Provenance
        </span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            onClick={() => setShowJson(!showJson)}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem" }}
          >
            {showJson ? "Structured View" : "Raw JSON"}
          </button>
          <button
            onClick={handleCopy}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem" }}
          >
            {copied ? <CheckIcon size={12} /> : <CopyIcon size={12} />}
            {copied ? "Copied" : "Copy Spec"}
          </button>
          <button
            onClick={onClose}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem" }}
          >
            ✕
          </button>
        </div>
      </div>

      {showJson ? (
        <pre
          style={{
            maxHeight: "220px",
            overflowY: "auto",
            backgroundColor: "#020617",
            padding: "0.75rem",
            borderRadius: "0.375rem",
            fontSize: "0.725rem",
            color: "#38bdf8",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          {JSON.stringify(spec, null, 2)}
        </pre>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
          {/* Column 1: Core Configuration */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>Configuration</span>
            <div><span style={{ color: "var(--text-muted)" }}>Type:</span> {spec.chart_type}</div>
            <div><span style={{ color: "var(--text-muted)" }}>X-Axis:</span> {spec.x || "(None)"}</div>
            <div><span style={{ color: "var(--text-muted)" }}>Y-Axis:</span> {spec.y || "(None)"}</div>
            <div><span style={{ color: "var(--text-muted)" }}>Series:</span> {spec.series || "(None)"}</div>
            <div><span style={{ color: "var(--text-muted)" }}>Aggregation:</span> {spec.aggregation?.toUpperCase() || "None"}</div>
          </div>

          {/* Column 2: Sampling & Limits */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>Data & Limits</span>
            <div><span style={{ color: "var(--text-muted)" }}>Displayed Points:</span> {spec.data?.length || 0}</div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Source Rows:</span>{" "}
              {sampling?.original_row_count ? sampling.original_row_count.toLocaleString() : "Unknown"}
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Sampling Method:</span>{" "}
              {sampling?.sampling_method || "exact"}
            </div>
            {spec.top_n && (
              <div>
                <span style={{ color: "var(--text-muted)" }}>Top-N:</span> Top {spec.top_n.n}{" "}
                {spec.top_n.include_other ? `(+ ${spec.top_n.other_label})` : ""}
              </div>
            )}
          </div>

          {/* Column 3: Provenance */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>Provenance</span>
            <div><span style={{ color: "var(--text-muted)" }}>Dataset ID:</span> {spec.dataset_id}</div>
            <div><span style={{ color: "var(--text-muted)" }}>Version Bound:</span> {spec.dataset_version_id || spec.version_id}</div>
            <div><span style={{ color: "var(--text-muted)" }}>Source Type:</span> {provenance?.source_type || spec.source_type || "dataset"}</div>
            <div><span style={{ color: "var(--text-muted)" }}>Created:</span> {provenance?.created_at ? new Date(provenance.created_at).toLocaleTimeString() : "Session"}</div>
          </div>
        </div>
      )}
    </div>
  );
}
