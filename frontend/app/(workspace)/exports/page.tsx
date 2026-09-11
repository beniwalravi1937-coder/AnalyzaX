"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useDataset } from "@/context/DatasetContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { ExportQuickPanel } from "@/components/exports/ExportQuickPanel";
import { ReportBuilderPanel } from "@/components/exports/ReportBuilderPanel";
import { ExportHistoryTable } from "@/components/exports/ExportHistoryTable";
import { ChartImageExport } from "@/components/exports/ChartImageExport";
import { cleanupExpired } from "@/services/exportApi";
import { ExportsIcon, UploadIcon } from "@/components/icons";

type TabType = "quick" | "reports" | "chart_images" | "history";

export default function ExportsPage() {
  const { activeDataset } = useDataset();
  const [activeTab, setActiveTab] = useState<TabType>("quick");
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isCleaning, setIsCleaning] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<string | null>(null);

  const handleCleanup = async () => {
    setIsCleaning(true);
    setCleanupResult(null);
    try {
      const res = await cleanupExpired();
      setCleanupResult(`Cleaned up ${res.removed} expired artifacts.`);
      setRefreshTrigger((prev) => prev + 1);
    } catch (err: unknown) {
      setCleanupResult(err instanceof Error ? err.message : "Cleanup failed");
    } finally {
      setIsCleaning(false);
    }
  };

  const handleExportCreated = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", paddingBottom: "3rem" }}>
      <PageHeader
        title="Export & Artifact Studio"
        description="Multi-format publishing engine for reproducible data artifacts, executive reports, SQL outputs, and standalone visualizations."
        badge={{ text: "Phase 15 — Active", variant: "emerald" }}
      />

      {/* Top Bar / Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.5rem",
          borderBottom: "1px solid var(--border-subtle)",
          paddingBottom: "1rem",
        }}
      >
        {/* Navigation Tabs */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => setActiveTab("quick")}
            className={`btn btn-sm ${activeTab === "quick" ? "btn-primary" : "btn-secondary"}`}
          >
            ⚡ Quick Export
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("reports")}
            className={`btn btn-sm ${activeTab === "reports" ? "btn-primary" : "btn-secondary"}`}
          >
            📑 Report Builder
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("chart_images")}
            className={`btn btn-sm ${activeTab === "chart_images" ? "btn-primary" : "btn-secondary"}`}
          >
            🖼️ Chart Images
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("history")}
            className={`btn btn-sm ${activeTab === "history" ? "btn-primary" : "btn-secondary"}`}
          >
            📜 Artifact History
          </button>
        </div>

        {/* Global Cleanup Button */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {cleanupResult && (
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              {cleanupResult}
            </span>
          )}
          <button
            onClick={handleCleanup}
            disabled={isCleaning}
            className="btn btn-ghost btn-sm"
            style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}
            title="Purge artifacts older than TTL (7 days)"
          >
            {isCleaning ? "Cleaning..." : "🧹 Purge Expired"}
          </button>
        </div>
      </div>

      {/* Dataset Context Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1rem",
          marginBottom: "1.5rem",
          background: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "0.5rem",
          fontSize: "0.8125rem",
        }}
      >
        <div>
          <span style={{ color: "var(--text-secondary)", marginRight: "0.5rem" }}>
            Active Dataset Scope:
          </span>
          {activeDataset ? (
            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
              📊 {activeDataset.name}{" "}
              <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>
                ({activeDataset.active_version_id || "v1"})
              </span>
            </span>
          ) : (
            <span style={{ color: "#f59e0b", fontWeight: 500 }}>
              ⚠️ No dataset selected. Connect or upload a dataset to export data.
            </span>
          )}
        </div>

        {!activeDataset && (
          <Link href="/upload" className="btn btn-primary btn-sm" style={{ fontSize: "0.75rem" }}>
            Upload Dataset
          </Link>
        )}
      </div>

      {/* Main Tab Content */}
      {activeTab === "quick" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {activeDataset ? (
            <ExportQuickPanel
              datasetId={activeDataset.id}
              versionId={activeDataset.active_version_id || "v1"}
            />
          ) : (
            <div
              style={{
                textAlign: "center",
                padding: "3rem 1rem",
                border: "1px dashed var(--border-subtle)",
                borderRadius: "0.5rem",
                background: "var(--bg-card)",
              }}
            >
              <ExportsIcon size={32} />
              <h3 style={{ marginTop: "1rem", color: "var(--text-primary)" }}>
                No active dataset selected
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                Select or upload a dataset to export tabular data or analytical artifacts.
              </p>
              <Link href="/upload" className="btn btn-primary btn-sm" style={{ marginTop: "1rem" }}>
                <UploadIcon size={14} style={{ marginRight: "0.4rem" }} /> Go to Ingestion
              </Link>
            </div>
          )}

          {/* Inline recent history */}
          <ExportHistoryTable
            datasetId={activeDataset?.id}
            refreshTrigger={refreshTrigger}
            onJobDeleted={handleExportCreated}
          />
        </div>
      )}

      {activeTab === "reports" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {activeDataset ? (
            <ReportBuilderPanel
              datasetId={activeDataset.id}
              versionId={activeDataset.active_version_id || "v1"}
            />
          ) : (
            <div
              style={{
                textAlign: "center",
                padding: "3rem 1rem",
                border: "1px dashed var(--border-subtle)",
                borderRadius: "0.5rem",
                background: "var(--bg-card)",
              }}
            >
              <ExportsIcon size={32} />
              <h3 style={{ marginTop: "1rem", color: "var(--text-primary)" }}>
                No active dataset selected
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                Select a dataset first to compose executive summaries and analytical reports.
              </p>
            </div>
          )}

          <ExportHistoryTable
            datasetId={activeDataset?.id}
            refreshTrigger={refreshTrigger}
            onJobDeleted={handleExportCreated}
          />
        </div>
      )}

      {activeTab === "chart_images" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <ChartImageExport chartTitle={activeDataset ? `${activeDataset.name}_chart` : "chart_export"} />
          <div
            style={{
              padding: "1rem",
              borderRadius: "0.5rem",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-surface)",
              fontSize: "0.8125rem",
              color: "var(--text-secondary)",
            }}
          >
            💡 <strong>Pro-tip:</strong> You can also export charts directly within the{" "}
            <Link href="/visualization" style={{ color: "var(--brand-primary)", textDecoration: "underline" }}>
              Visualization Studio
            </Link>{" "}
            using the chart toolbar dropdown menu.
          </div>
        </div>
      )}

      {activeTab === "history" && (
        <ExportHistoryTable
          datasetId={activeDataset?.id}
          refreshTrigger={refreshTrigger}
          onJobDeleted={handleExportCreated}
        />
      )}
    </div>
  );
}
