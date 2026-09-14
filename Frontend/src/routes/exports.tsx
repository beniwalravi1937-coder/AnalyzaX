import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState } from "react";
import { useDataset } from "../context/DatasetContext";
import { ExportQuickPanel } from "../components/exports/ExportQuickPanel";
import { ReportBuilderPanel } from "../components/exports/ReportBuilderPanel";
import { ExportHistoryTable } from "../components/exports/ExportHistoryTable";
import { ChartImageExport } from "../components/exports/ChartImageExport";
import { cleanupExpired } from "../services/exportApi";
import { ExportsIcon, UploadIcon } from "../components/icons";
import { AnalyticalWorkspaceHeader } from "@/components/layout/AnalyticalWorkspaceHeader";
import { SecondaryInfoPanel } from "@/components/layout/SecondaryInfoPanel";
import { Button } from "@/components/ui/button";
import { Download, Trash2, FileText, Image as ImageIcon, Zap, History as HistoryIcon } from "lucide-react";

export const Route = createFileRoute("/exports")({
  head: () => ({
    meta: [
      { title: "Data & Report Exports — AnalyzaX" },
      {
        name: "description",
        content:
          "Multi-format publishing engine for reproducible data artifacts, executive reports, and visualization assets.",
      },
      { property: "og:title", content: "Data & Report Exports — AnalyzaX" },
    ],
  }),
  component: ExportsPage,
});

type TabType = "quick" | "reports" | "chart_images" | "history";

function ExportsPage() {
  const { activeDataset } = useDataset();
  const [activeTab, setActiveTab] = useState<TabType>("quick");
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isCleaning, setIsCleaning] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<string | null>(null);
  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");

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

  const workflowSteps = [
    { id: "scope", label: "Dataset Scope", status: activeDataset ? ("completed" as const) : ("current" as const) },
    { id: "format", label: "Format Selection", status: "completed" as const },
    { id: "execution", label: "Artifact Rendering", status: activeTab === "history" ? ("completed" as const) : ("current" as const) },
    { id: "archive", label: "Download & Archive", status: "completed" as const },
  ];

  return (
    <div className="flex flex-col min-h-[calc(100vh-100px)] space-y-4">
      <AnalyticalWorkspaceHeader
        title="Exports"
        description="Multi-format publishing engine for reproducible data artifacts, executive reports, and visualization assets."
        badgeText="Multi-Format Engine"
        steps={workflowSteps}
        currentStepId={activeTab === "history" ? "archive" : "format"}
        status="idle"
        mode={mode}
        onModeChange={setMode}
        primaryAction={
          <Button
            size="sm"
            onClick={() => setActiveTab("quick")}
            className="h-9 px-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>New Export</span>
          </Button>
        }
        secondaryActions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleCleanup}
            disabled={isCleaning}
            className="h-9 px-2.5 text-xs border-white/10 bg-slate-900/60 hover:bg-slate-850 hover:border-white/20 text-slate-300 gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5 text-slate-400" />
            <span>{isCleaning ? "Cleaning..." : "Purge Expired"}</span>
          </Button>
        }
      />

      {/* Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => setActiveTab("quick")}
            className={`btn btn-sm text-xs ${activeTab === "quick" ? "btn-primary" : "btn-secondary"}`}
          >
            ⚡ Quick Export
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("reports")}
            className={`btn btn-sm text-xs ${activeTab === "reports" ? "btn-primary" : "btn-secondary"}`}
          >
            📑 Report Builder
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("chart_images")}
            className={`btn btn-sm text-xs ${activeTab === "chart_images" ? "btn-primary" : "btn-secondary"}`}
          >
            🖼️ Chart Images
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("history")}
            className={`btn btn-sm text-xs ${activeTab === "history" ? "btn-primary" : "btn-secondary"}`}
          >
            📜 Artifact History
          </button>
        </div>

        {cleanupResult && (
          <span className="text-xs text-slate-400">
            {cleanupResult}
          </span>
        )}
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
          <Link to="/data" className="btn btn-primary btn-sm" style={{ fontSize: "0.75rem" }}>
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
              <Link to="/data" className="btn btn-primary btn-sm" style={{ marginTop: "1rem" }}>
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
            <Link to="/visualizations" style={{ color: "var(--brand-primary)", textDecoration: "underline" }}>
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

      {/* Secondary Information */}
      <SecondaryInfoPanel
        metadata={{
          datasetName: activeDataset?.name || "No dataset selected",
          versionName: activeDataset?.active_version_id || "v1",
          engine: "Multi-Format Export & Archival Engine",
          customFields: {
            "Active Tab": activeTab,
            "Artifact TTL": "7 days retention",
            "Supported Formats": "CSV, Excel, Parquet, PDF, PNG",
          },
        }}
        recommendations={[
          {
            id: "eda-verify",
            title: "Verify Data Summary in EDA",
            description: "Check statistical moments and distributions before distributing export packages.",
            actionLabel: "Open EDA",
            onAction: () => { window.location.href = "/eda"; },
            impact: "medium" as const,
          },
          {
            id: "cleaning-verify",
            title: "Check Imputation Lineage",
            description: "Review transformation log before generating client-facing executive reports.",
            actionLabel: "Cleaning Studio",
            onAction: () => { window.location.href = "/cleaning"; },
            impact: "low" as const,
          },
        ]}
        detailsContent={
          <div className="space-y-3 text-xs text-slate-300">
            <p>
              Generated analytical packages and reports are rendered server-side with sha256 checksums and automated schema preservation.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/5">
                <span className="text-slate-400 block text-[10px] uppercase">Storage Mode</span>
                <span className="font-semibold text-slate-200">Ephemeral Sandboxed FS</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/5">
                <span className="text-slate-400 block text-[10px] uppercase">Retention Policy</span>
                <span className="font-semibold text-slate-200">7-Day Automatic Purge</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/5">
                <span className="text-slate-400 block text-[10px] uppercase">Report Renderer</span>
                <span className="font-semibold text-slate-200">Executive HTML/PDF Engine</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-white/5">
                <span className="text-slate-400 block text-[10px] uppercase">Integrity Verification</span>
                <span className="font-semibold text-slate-200">SHA-256 Checksum</span>
              </div>
            </div>
          </div>
        }
      />
    </div>
  );
}

