import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  BarChartIcon,
  UploadIcon,
  RefreshIcon,
  DatabaseIcon,
  SaveIcon,
  SlidersIcon,
  SparklesIcon,
} from "@/components/icons";
import { apiClient } from "@/services/api";
import { sqlApi } from "@/services/sqlApi";
import { visualizationApi } from "@/services/visualizationApi";
import {
  DatasetResponse,
  DatasetVersion,
  ChartSpec,
  VisualizationRecommendation,
  SavedVisualization,
  VisualizationValidationResult,
} from "@/types";
import { ChartContainer } from "@/components/visualization/ChartContainer";
import { ChartBuilder } from "@/components/visualization/ChartBuilder";
import { VisualizationGrid } from "@/components/visualization/VisualizationGrid";

export const Route = createFileRoute("/visualizations")({
  head: () => ({
    meta: [
      { title: "Interactive Charts & Visuals — AnalyzaX" },
      {
        name: "description",
        content:
          "Build interactive bar, line, and scatter charts with drag-and-drop ease. Turn complex spreadsheet rows into clear, presentation-ready graphics.",
      },
      { property: "og:title", content: "Interactive Charts & Visuals — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Build interactive charts with drag-and-drop ease. Turn complex data into presentation-ready visuals.",
      },
    ],
  }),
  component: VisualizationsPage,
});

function VisualizationsPage() {
  // Datasets & Versions
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");

  // Schema Columns
  const [availableColumns, setAvailableColumns] = useState<
    Array<{ name: string; type?: string; is_numeric?: boolean; is_temporal?: boolean }>
  >([]);

  // Navigation Tabs: "recommendations" | "studio" | "saved"
  const [activeTab, setActiveTab] = useState<"recommendations" | "studio" | "saved">("recommendations");

  // Recommendations State
  const [recommendations, setRecommendations] = useState<VisualizationRecommendation[]>([]);
  const [isRecsLoading, setIsRecsLoading] = useState(false);
  const [recsError, setRecsError] = useState<string | null>(null);

  // Active Chart & Hydration State
  const [activeSpec, setActiveSpec] = useState<ChartSpec | null>(null);
  const [activeData, setActiveData] = useState<Record<string, any>[]>([]);
  const [isHydrating, setIsHydrating] = useState(false);
  const [hydrationError, setHydrationError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<VisualizationValidationResult | null>(null);

  // Saved Charts State
  const [savedCharts, setSavedCharts] = useState<SavedVisualization[]>([]);
  const [savedLoading, setSavedLoading] = useState(false);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saveDescription, setSaveDescription] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // 1. Initial load: Datasets
  useEffect(() => {
    async function loadDatasets() {
      try {
        const res = await apiClient.listDatasets();
        const list = res.datasets || [];
        setDatasets(list);
        if (list.length > 0) {
          const first = list[0];
          setSelectedDatasetId(first.id);
          setSelectedVersionId(first.active_version_id || first.current_version_id || "v1");
        }
      } catch (err) {
        console.error("Failed to load datasets:", err);
      }
    }
    loadDatasets();
  }, []);

  // 2. Load versions when dataset changes
  useEffect(() => {
    if (!selectedDatasetId) return;
    async function loadVersions() {
      try {
        const vList = await apiClient.getDatasetVersions(selectedDatasetId);
        setVersions(vList);
        if (vList.length > 0 && !selectedVersionId) {
          setSelectedVersionId(vList[0].version_id);
        }
      } catch (err) {
        console.error("Failed to load versions:", err);
      }
    }
    loadVersions();
  }, [selectedDatasetId, selectedVersionId]);

  // 3. Introspect Schema / Columns
  useEffect(() => {
    if (!selectedDatasetId) return;
    async function loadColumns() {
      try {
        const sInfo = await sqlApi.getSchema(selectedDatasetId, selectedVersionId || null);
        if (sInfo && sInfo.columns) {
          setAvailableColumns(
            sInfo.columns.map((col) => {
              const dt = (col.physical_type || "").toUpperCase();
              const isNum =
                dt.includes("INT") ||
                dt.includes("FLOAT") ||
                dt.includes("DOUBLE") ||
                dt.includes("DECIMAL") ||
                dt.includes("NUMERIC");
              const isTemp =
                dt.includes("DATE") ||
                dt.includes("TIME") ||
                dt.includes("TIMESTAMP");
              return {
                name: col.name,
                type: col.physical_type,
                is_numeric: isNum,
                is_temporal: isTemp,
              };
            })
          );
        }
      } catch (err) {
        console.error("Failed to load columns:", err);
      }
    }
    loadColumns();
  }, [selectedDatasetId, selectedVersionId]);

  // 4. Load Recommendations
  const loadRecommendations = useCallback(async () => {
    if (!selectedDatasetId) return;
    setIsRecsLoading(true);
    setRecsError(null);
    try {
      const recs = await visualizationApi.getRecommendations(
        selectedDatasetId,
        selectedVersionId || null
      );
      setRecommendations(recs);
      if (recs.length > 0 && !activeSpec) {
        const topRec = recs[0];
        setActiveSpec(topRec.spec);
        hydrateChart(topRec.spec);
      }
    } catch (err: any) {
      setRecsError(err.message || "Failed to load visualization recommendations.");
    } finally {
      setIsRecsLoading(false);
    }
  }, [selectedDatasetId, selectedVersionId, activeSpec]);

  // 5. Load Saved Visualizations
  const loadSavedCharts = useCallback(async () => {
    if (!selectedDatasetId) return;
    setSavedLoading(true);
    try {
      const list = await visualizationApi.listSavedVisualizations(selectedDatasetId);
      setSavedCharts(list);
    } catch (err) {
      console.error("Failed to load saved visualizations:", err);
    } finally {
      setSavedLoading(false);
    }
  }, [selectedDatasetId]);

  useEffect(() => {
    if (selectedDatasetId) {
      loadRecommendations();
      loadSavedCharts();
    }
  }, [selectedDatasetId, selectedVersionId, loadRecommendations, loadSavedCharts]);

  // Hydrate a ChartSpec (previews with server-side aggregated data)
  const hydrateChart = async (specToHydrate: ChartSpec) => {
    setIsHydrating(true);
    setHydrationError(null);
    try {
      const valRes = await visualizationApi.validateSpec(specToHydrate);
      setValidationResult(valRes);

      if (!valRes.is_valid) {
        setHydrationError(valRes.errors.join("; "));
        setIsHydrating(false);
        return;
      }

      const hydrated = await visualizationApi.previewChart(specToHydrate);
      setActiveSpec(hydrated);
      setActiveData(hydrated.data || []);
    } catch (err: any) {
      setHydrationError(err.message || "Failed to hydrate visualization data.");
    } finally {
      setIsHydrating(false);
    }
  };

  const handleSelectSpec = (spec: ChartSpec) => {
    const specWithContext: ChartSpec = {
      ...spec,
      dataset_id: selectedDatasetId,
      dataset_version_id: selectedVersionId || spec.dataset_version_id,
    };
    setActiveSpec(specWithContext);
    hydrateChart(specWithContext);
  };

  const handleSaveVisualization = async () => {
    if (!activeSpec) return;
    setIsSaving(true);
    try {
      const name = saveName.trim() || activeSpec.title || "Custom Visualization";
      await visualizationApi.saveVisualization(name, activeSpec, saveDescription);
      setSaveModalOpen(false);
      setSaveName("");
      setSaveDescription("");
      setSaveSuccessMsg("Visualization saved successfully!");
      setTimeout(() => setSaveSuccessMsg(null), 3000);
      loadSavedCharts();
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteSavedChart = async (id: string) => {
    if (!confirm("Are you sure you want to delete this saved visualization?")) return;
    try {
      await visualizationApi.deleteSavedVisualization(id);
      loadSavedCharts();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleFilterByValue = (field: string, value: any) => {
    if (!activeSpec) return;
    const existingFilters = activeSpec.filters || [];
    const newFilter = { column: field, operator: "eq" as const, value };
    const updatedSpec: ChartSpec = {
      ...activeSpec,
      filters: [...existingFilters, newFilter],
    };
    setActiveSpec(updatedSpec);
    hydrateChart(updatedSpec);
  };

  return (
    <div className="ax-stack">
      {/* Page Header */}
      <PageHeader
        title="Visualization Intelligence & Studio"
        description="Deterministic, semantic, version-aware visualizations and automated chart intelligence."
      />

      {/* Dataset & Version Bar */}
      <div
        className="card"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1.25rem",
          marginBottom: "1.25rem",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1.25rem", flexWrap: "wrap" }}>
          {/* Dataset Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <DatabaseIcon size={16} className="text-brand" />
            <span style={{ fontSize: "0.825rem", fontWeight: 600, color: "var(--text-secondary)" }}>
              Dataset:
            </span>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="input input-sm"
              style={{ minWidth: "180px", fontSize: "0.825rem" }}
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* Version Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "0.825rem", fontWeight: 600, color: "var(--text-secondary)" }}>
              Version:
            </span>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(e.target.value)}
              className="input input-sm"
              style={{ minWidth: "100px", fontSize: "0.825rem" }}
            >
              {versions.map((v) => (
                <option key={v.version_id} value={v.version_id}>
                  {v.version_id} ({v.version_label || "Base"})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Right side status / reload */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {saveSuccessMsg && (
            <span style={{ fontSize: "0.8rem", color: "var(--status-success, #10b981)", fontWeight: 600 }}>
              ✓ {saveSuccessMsg}
            </span>
          )}
          <button
            onClick={() => {
              loadRecommendations();
              loadSavedCharts();
            }}
            className="btn btn-secondary btn-sm"
            style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}
          >
            <RefreshIcon size={14} className={isRecsLoading ? "spin" : ""} />
            Refresh Intelligence
          </button>
        </div>
      </div>

      {datasets.length === 0 ? (
        <EmptyState
          title="No Datasets Available"
          description="Upload a dataset to start exploring automated visualization intelligence and interactive charts."
          action={
            <Link to="/data" className="btn btn-primary btn-sm">
              <UploadIcon size={14} /> Upload Dataset
            </Link>
          }
        />
      ) : (
        <>
          {/* Main Navigation Tabs */}
          <div
            style={{
              display: "flex",
              borderBottom: "1px solid var(--border-subtle)",
              marginBottom: "1.25rem",
              gap: "1.5rem",
            }}
          >
            <button
              onClick={() => setActiveTab("recommendations")}
              style={{
                background: "none",
                border: "none",
                borderBottom: activeTab === "recommendations" ? "2px solid #6366f1" : "2px solid transparent",
                padding: "0.6rem 0.5rem",
                color: activeTab === "recommendations" ? "#818cf8" : "var(--text-secondary)",
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <SparklesIcon size={16} />
              Intelligence & Recommendations
              {recommendations.length > 0 && (
                <span
                  style={{
                    fontSize: "0.7rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "1rem",
                    backgroundColor: "rgba(99, 102, 241, 0.2)",
                    color: "#a5b4fc",
                  }}
                >
                  {recommendations.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("studio")}
              style={{
                background: "none",
                border: "none",
                borderBottom: activeTab === "studio" ? "2px solid #6366f1" : "2px solid transparent",
                padding: "0.6rem 0.5rem",
                color: activeTab === "studio" ? "#818cf8" : "var(--text-secondary)",
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <SlidersIcon size={16} />
              Visual Studio & Preview
            </button>

            <button
              onClick={() => setActiveTab("saved")}
              style={{
                background: "none",
                border: "none",
                borderBottom: activeTab === "saved" ? "2px solid #6366f1" : "2px solid transparent",
                padding: "0.6rem 0.5rem",
                color: activeTab === "saved" ? "#818cf8" : "var(--text-secondary)",
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <SaveIcon size={16} />
              Saved Visualizations
              {savedCharts.length > 0 && (
                <span
                  style={{
                    fontSize: "0.7rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "1rem",
                    backgroundColor: "rgba(16, 185, 129, 0.2)",
                    color: "#34d399",
                  }}
                >
                  {savedCharts.length}
                </span>
              )}
            </button>
          </div>

          {/* TAB 1: Recommendations & Intelligence */}
          {activeTab === "recommendations" && (
            <div>
              {/* Top Section: Active Preview Hero Card */}
              {activeSpec && (
                <div style={{ marginBottom: "2rem" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                    <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      Active Visualization Preview
                    </div>
                    <button
                      onClick={() => setActiveTab("studio")}
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: "0.75rem" }}
                    >
                      Open in Studio & Edit ↗
                    </button>
                  </div>
                  <ChartContainer
                    spec={activeSpec}
                    data={activeData}
                    isLoading={isHydrating}
                    error={hydrationError}
                    warnings={validationResult?.warnings?.map((w) =>
                      typeof w === "string" ? w : w.message
                    )}
                    onSave={() => setSaveModalOpen(true)}
                    onFilterByValue={handleFilterByValue}
                    height={380}
                  />
                </div>
              )}

              {/* Recommendations Grid */}
              <div>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem" }}>
                  Automated Visualizations for this Dataset ({recommendations.length})
                </h3>
                {isRecsLoading ? (
                  <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
                    Evaluating statistical distribution rules & scoring chart suitability...
                  </div>
                ) : recsError ? (
                  <div style={{ padding: "1rem", color: "var(--accent-rose)", backgroundColor: "rgba(244, 63, 94, 0.1)", borderRadius: "0.5rem" }}>
                    {recsError}
                  </div>
                ) : (
                  <VisualizationGrid
                    recommendations={recommendations}
                    onSelect={(spec) => {
                      handleSelectSpec(spec);
                      window.scrollTo({ top: 120, behavior: "smooth" });
                    }}
                    selectedSpec={activeSpec}
                  />
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Visual Studio / Builder */}
          {activeTab === "studio" && (
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.8fr", gap: "1.5rem" }}>
              {/* Left Column: Builder Controls */}
              <div>
                {activeSpec ? (
                  <ChartBuilder
                    spec={activeSpec}
                    onChange={(updated) => setActiveSpec(updated)}
                    availableColumns={availableColumns}
                    onPreview={() => activeSpec && hydrateChart(activeSpec)}
                    isLoading={isHydrating}
                  />
                ) : (
                  <div
                    style={{
                      padding: "2rem",
                      textAlign: "center",
                      backgroundColor: "var(--bg-surface)",
                      borderRadius: "0.5rem",
                      border: "1px dashed var(--border-subtle)",
                    }}
                  >
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                      No active chart selected.
                    </p>
                    <button
                      onClick={() => {
                        if (availableColumns.length > 0) {
                          const newSpec: ChartSpec = {
                            chart_type: "bar",
                            dataset_id: selectedDatasetId,
                            dataset_version_id: selectedVersionId,
                            title: "Custom Chart",
                            x_axis: { field: availableColumns[0].name, type: "category" },
                            y_axis: {
                              field: availableColumns[1]?.name || availableColumns[0].name,
                              aggregation: "COUNT",
                            },
                          };
                          setActiveSpec(newSpec);
                          hydrateChart(newSpec);
                        }
                      }}
                      className="btn btn-primary btn-sm"
                      style={{ marginTop: "0.5rem" }}
                    >
                      Create Blank Chart
                    </button>
                  </div>
                )}
              </div>

              {/* Right Column: Live Hydrated Chart */}
              <div>
                {activeSpec ? (
                  <ChartContainer
                    spec={activeSpec}
                    data={activeData}
                    isLoading={isHydrating}
                    error={hydrationError}
                    warnings={validationResult?.warnings?.map((w) =>
                      typeof w === "string" ? w : w.message
                    )}
                    onSave={() => setSaveModalOpen(true)}
                    onFilterByValue={handleFilterByValue}
                    height={500}
                  />
                ) : (
                  <div
                    style={{
                      height: "500px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: "var(--bg-surface)",
                      borderRadius: "0.5rem",
                      border: "1px dashed var(--border-subtle)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    Select or configure a chart to view the live rendering.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Saved Visualizations */}
          {activeTab === "saved" && (
            <div>
              {savedLoading ? (
                <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
                  Loading saved visualizations...
                </div>
              ) : savedCharts.length === 0 ? (
                <div
                  style={{
                    padding: "3rem",
                    textAlign: "center",
                    backgroundColor: "var(--bg-surface)",
                    borderRadius: "0.5rem",
                    border: "1px dashed var(--border-subtle)",
                  }}
                >
                  <BarChartIcon size={32} style={{ margin: "0 auto 1rem auto", color: "var(--text-muted)" }} />
                  <h4 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    No Saved Visualizations
                  </h4>
                  <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                    Configure a chart in the Studio or pick a recommendation, then click &quot;Save Chart&quot;.
                  </p>
                </div>
              ) : (
                <VisualizationGrid
                  savedCharts={savedCharts}
                  onSelect={(spec) => {
                    handleSelectSpec(spec);
                    setActiveTab("studio");
                  }}
                  onDelete={handleDeleteSavedChart}
                  selectedSpec={activeSpec}
                />
              )}
            </div>
          )}
        </>
      )}

      {/* Save Modal */}
      {saveModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(4px)",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
          }}
        >
          <div
            className="card"
            style={{
              width: "100%",
              maxWidth: "480px",
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0.5rem",
              padding: "1.5rem",
            }}
          >
            <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "1rem" }}>
              Save Visualization
            </h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.775rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
                  Visualization Name
                </label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder={activeSpec?.title || "e.g., Q3 Revenue Breakdown"}
                  className="input"
                  style={{ width: "100%", fontSize: "0.825rem" }}
                  autoFocus
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.775rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>
                  Description / Notes (Optional)
                </label>
                <textarea
                  value={saveDescription}
                  onChange={(e) => setSaveDescription(e.target.value)}
                  placeholder="Additional context or analytical explanation..."
                  className="input"
                  rows={3}
                  style={{ width: "100%", fontSize: "0.825rem", resize: "vertical" }}
                />
              </div>

              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", backgroundColor: "rgba(255,255,255,0.03)", padding: "0.5rem", borderRadius: "0.25rem" }}>
                🔒 This visualization will be tied to dataset <strong>{selectedDatasetId}</strong> version <strong>{selectedVersionId}</strong> with immutable lineage provenance.
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
                <button
                  onClick={() => setSaveModalOpen(false)}
                  className="btn btn-secondary btn-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveVisualization}
                  disabled={isSaving}
                  className="btn btn-primary btn-sm"
                >
                  {isSaving ? "Saving..." : "Confirm Save"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
