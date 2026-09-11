"use client";

import React, { useState } from "react";
import { DatasetVersion } from "@/types";
import { HistoryIcon, CheckIcon, ChevronDownIcon } from "@/components/icons";

interface DatasetVersionSelectorProps {
  versions: DatasetVersion[];
  activeVersionId: string;
  onSelectVersion: (versionId: string) => void;
  isLoading?: boolean;
}

export function DatasetVersionSelector({
  versions,
  activeVersionId,
  onSelectVersion,
  isLoading = false,
}: DatasetVersionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const activeVersion =
    versions.find((v) => v.version_id === activeVersionId) || versions[0];

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.4rem 0.75rem",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "6px",
          color: "var(--text-primary)",
          fontSize: "0.78rem",
          fontWeight: 600,
          cursor: isLoading ? "not-allowed" : "pointer",
        }}
      >
        <HistoryIcon size={14} style={{ color: "var(--accent-primary)" }} />
        <span>
          Version: <span style={{ color: "var(--accent-primary)" }}>{activeVersion?.version_id}</span>{" "}
          <span style={{ fontWeight: 400, color: "var(--text-tertiary)" }}>
            ({activeVersion?.row_count.toLocaleString()} rows)
          </span>
        </span>
        <ChevronDownIcon size={12} style={{ color: "var(--text-tertiary)" }} />
      </button>

      {isOpen && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            right: 0,
            width: "320px",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "8px",
            boxShadow: "0 10px 25px rgba(0,0,0,0.3)",
            zIndex: 100,
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              padding: "0.6rem 0.8rem",
              backgroundColor: "var(--bg-canvas)",
              borderBottom: "1px solid var(--border-subtle)",
              fontSize: "0.72rem",
              fontWeight: 600,
              color: "var(--text-secondary)",
            }}
          >
            Dataset Lineage Versions ({versions.length})
          </div>

          <div style={{ maxHeight: "250px", overflowY: "auto" }}>
            {versions.map((ver) => {
              const isActive = ver.version_id === activeVersionId;

              return (
                <button
                  key={ver.version_id}
                  onClick={() => {
                    onSelectVersion(ver.version_id);
                    setIsOpen(false);
                  }}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.65rem 0.8rem",
                    border: "none",
                    borderBottom: "1px solid var(--border-subtle)",
                    backgroundColor: isActive ? "rgba(99, 102, 241, 0.08)" : "transparent",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "background-color 0.15s ease",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <span
                        style={{
                          fontSize: "0.78rem",
                          fontWeight: 700,
                          color: isActive ? "var(--accent-primary)" : "var(--text-primary)",
                        }}
                      >
                        {ver.version_id}
                      </span>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          color: "var(--text-secondary)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          maxWidth: "180px",
                        }}
                      >
                        {ver.version_label}
                      </span>
                    </div>

                    <div
                      style={{
                        fontSize: "0.68rem",
                        color: "var(--text-tertiary)",
                        marginTop: "2px",
                      }}
                    >
                      {ver.row_count.toLocaleString()} rows • {ver.column_count} cols • {ver.created_at.slice(0, 10)}
                    </div>
                  </div>

                  {isActive && (
                    <div
                      style={{
                        color: "#10b981",
                        display: "flex",
                        alignItems: "center",
                      }}
                    >
                      <CheckIcon size={14} />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
