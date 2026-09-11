"use client";

import React, { useEffect, useState } from "react";
import { DashboardVersion } from "@/types/dashboard";
import { listVersions, restoreVersion } from "@/services/dashboardApi";

interface DashboardHistoryDrawerProps {
  dashboardId: string;
  isOpen: boolean;
  onClose: () => void;
  onVersionRestored: () => void;
}

export function DashboardHistoryDrawer({
  dashboardId,
  isOpen,
  onClose,
  onVersionRestored,
}: DashboardHistoryDrawerProps) {
  const [versions, setVersions] = useState<DashboardVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [restoringVersion, setRestoringVersion] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen && dashboardId) {
      loadVersions();
    }
  }, [isOpen, dashboardId]);

  const loadVersions = async () => {
    setIsLoading(true);
    try {
      const vers = await listVersions(dashboardId);
      setVersions(vers);
    } catch (err) {
      console.error("Failed to load versions:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestore = async (verNum: number) => {
    if (!confirm(`Restore Version ${verNum}? This creates a new version snapshot while preserving history.`)) {
      return;
    }
    setRestoringVersion(verNum);
    try {
      await restoreVersion(dashboardId, verNum);
      onVersionRestored();
      onClose();
    } catch (err: any) {
      alert(`Failed to restore version: ${err.message}`);
    } finally {
      setRestoringVersion(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.6)",
        backdropFilter: "blur(2px)",
        zIndex: 1050,
        display: "flex",
        justifyContent: "flex-end",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "440px",
          background: "#1e293b",
          borderLeft: "1px solid rgba(51, 65, 85, 0.8)",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          boxShadow: "-10px 0 30px rgba(0, 0, 0, 0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid rgba(51, 65, 85, 0.6)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
              Version History
            </h3>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
              Audit snapshots and rollback capabilities
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              fontSize: "1.25rem",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ padding: "1.5rem", flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "1rem" }}>
          {isLoading ? (
            <div style={{ textAlign: "center", color: "#94a3b8", padding: "2rem" }}>Loading history...</div>
          ) : versions.length === 0 ? (
            <div style={{ textAlign: "center", color: "#94a3b8", padding: "2rem" }}>No version records found</div>
          ) : (
            versions.map((v, idx) => (
              <div
                key={v.version_id}
                style={{
                  background: idx === 0 ? "rgba(99, 102, 241, 0.1)" : "rgba(15, 23, 42, 0.5)",
                  border: idx === 0 ? "1px solid rgba(99, 102, 241, 0.4)" : "1px solid rgba(51, 65, 85, 0.5)",
                  borderRadius: "8px",
                  padding: "1rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                  <span style={{ fontWeight: 700, color: "#ffffff", fontSize: "0.95rem" }}>
                    Version {v.version_number}
                    {idx === 0 && (
                      <span
                        style={{
                          marginLeft: "0.5rem",
                          fontSize: "0.65rem",
                          background: "#3b82f6",
                          color: "#ffffff",
                          padding: "0.1rem 0.4rem",
                          borderRadius: "4px",
                          fontWeight: 600,
                        }}
                      >
                        CURRENT
                      </span>
                    )}
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                    {new Date(v.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div style={{ fontSize: "0.8rem", color: "#cbd5e1", marginBottom: "0.75rem" }}>
                  {v.comment || "Automated state snapshot"}
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.7rem", color: "#64748b" }}>
                    {v.snapshot.components?.length || 0} components • {v.snapshot.filters?.length || 0} filters
                  </span>

                  {idx !== 0 && (
                    <button
                      onClick={() => handleRestore(v.version_number)}
                      disabled={restoringVersion === v.version_number}
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
                    >
                      {restoringVersion === v.version_number ? "Restoring..." : "Restore"}
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
