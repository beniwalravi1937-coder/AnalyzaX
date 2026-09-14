"use client";

import React from "react";
import { DashboardComponent, ComponentDataResponse } from "@/types/dashboard";

interface ProvenanceModalProps {
  component: DashboardComponent | null;
  dataResp?: ComponentDataResponse;
  onClose: () => void;
}

export function ProvenanceModal({ component, dataResp, onClose }: ProvenanceModalProps) {
  if (!component) return null;

  const prov = dataResp?.provenance || component.provenance;
  const isStale = dataResp?.is_stale || prov?.is_stale;
  const staleReason = dataResp?.stale_reason || prov?.stale_reason;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#1e293b",
          border: "1px solid rgba(99, 102, 241, 0.3)",
          borderRadius: "12px",
          padding: "1.5rem",
          maxWidth: "540px",
          width: "90%",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
            Source & Provenance
          </h3>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "1.2rem",
            }}
          >
            ✕
          </button>
        </div>

        {/* Stale warning if applicable */}
        {isStale && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.4)",
              borderRadius: "6px",
              padding: "0.6rem 0.8rem",
              marginBottom: "1rem",
              fontSize: "0.8rem",
              color: "#fca5a5",
            }}
          >
            <strong>Version Stale:</strong> {staleReason || "Referenced dataset version has been superseded."}
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", fontSize: "0.85rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(51,65,85,0.4)", paddingBottom: "0.4rem" }}>
            <span style={{ color: "#94a3b8" }}>Component:</span>
            <span style={{ color: "#ffffff", fontWeight: 600 }}>{component.title}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(51,65,85,0.4)", paddingBottom: "0.4rem" }}>
            <span style={{ color: "#94a3b8" }}>Component Type:</span>
            <span style={{ color: "#818cf8", fontWeight: 600 }}>{component.type}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(51,65,85,0.4)", paddingBottom: "0.4rem" }}>
            <span style={{ color: "#94a3b8" }}>Dataset ID:</span>
            <code style={{ color: "#cbd5e1" }}>{component.dataset_id}</code>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(51,65,85,0.4)", paddingBottom: "0.4rem" }}>
            <span style={{ color: "#94a3b8" }}>Dataset Version:</span>
            <span style={{ color: "#34d399", fontWeight: 600 }}>{component.dataset_version_id}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(51,65,85,0.4)", paddingBottom: "0.4rem" }}>
            <span style={{ color: "#94a3b8" }}>Source Engine:</span>
            <span style={{ color: "#e2e8f0" }}>{component.source?.engine || "core"}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(51,65,85,0.4)", paddingBottom: "0.4rem" }}>
            <span style={{ color: "#94a3b8" }}>Source Type:</span>
            <span style={{ color: "#e2e8f0" }}>{component.source?.source_type}</span>
          </div>

          {component.source?.result_id && (
            <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(51,65,85,0.4)", paddingBottom: "0.4rem" }}>
              <span style={{ color: "#94a3b8" }}>Result ID:</span>
              <code style={{ color: "#cbd5e1" }}>{component.source.result_id}</code>
            </div>
          )}

          {dataResp?.refreshed_at && (
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Last Refreshed:</span>
              <span style={{ color: "#cbd5e1" }}>{new Date(dataResp.refreshed_at).toLocaleString()}</span>
            </div>
          )}
        </div>

        <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
          <button
            onClick={onClose}
            className="btn btn-secondary btn-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
