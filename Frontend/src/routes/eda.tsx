import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import { apiClient } from "@/services/api";
import { DatasetResponse, EDAReport } from "@/types";
import { AnalyticalWorkspaceHeader } from "@/components/layout/AnalyticalWorkspaceHeader";
import { SecondaryInfoPanel } from "@/components/layout/SecondaryInfoPanel";
import { DatasetSelector } from "@/components/ui/DatasetSelector";
import { VersionSelector } from "@/components/ui/VersionSelector";
import { Button } from "@/components/ui/button";
import { RefreshCw, Sparkles, AlertTriangle, Database, Info, Layers } from "lucide-react";
import { OverviewTab } from "@/components/eda/OverviewTab";
import { UnivariateTab } from "@/components/eda/UnivariateTab";
import { CorrelationsTab } from "@/components/eda/CorrelationsTab";
import { RelationshipTab } from "@/components/eda/RelationshipTab";
import { FindingsTab } from "@/components/eda/FindingsTab";

export const Route = createFileRoute("/eda")({
  head: () => ({
    meta: [
      { title: "Data Exploration & Relationships — AnalyzaX" },
      {
        name: "description",
        content:
          "Explore distributions, discover what factors drive your metrics, and uncover hidden relationships between variables with automated visual summaries.",
      },
      { property: "og:title", content: "Data Exploration & Relationships — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Explore distributions and uncover what factors drive your business metrics with automated visual summaries.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-eda.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-eda.png" },
    ],
  }),
  component: EDAPage,
});

function EDAPage() {
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<
    "overview" | "distributions" | "relationships" | "missingness" | "findings"
  >("overview");

  // Pairwise relationship selection across tabs
  const [pairX, setPairX] = useState<string>("");
  const [pairY, setPairY] = useState<string>("");

  // Report state
  const [report, setReport] = useState<EDAReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Correlation method
  const [corrMethod, setCorrMethod] = useState<"pearson" | "spearman" | "kendall">("pearson");

  // 1. Fetch datasets list on mount
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
        } else {
          setIsLoading(false);
        }
      } catch (err: any) {
        setErrorMessage("Failed to load datasets: " + (err.message || String(err)));
        setIsLoading(false);
      }
    }
    loadDatasets();
  }, []);

  // 2. Fetch EDA Report when dataset or version or correlation method changes
  const fetchReport = useCallback(
    async (datasetId: string, versionId?: string, method = corrMethod, refresh = false) => {
      if (!datasetId) return;
      if (refresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setErrorMessage(null);

      try {
        let data: EDAReport;
        if (refresh) {
          data = await apiClient.refreshEdaReport(datasetId, versionId, method);
        } else {
          data = await apiClient.getEdaReport(datasetId, versionId, method);
        }
        setReport(data);
        if (data.overview.version_id) {
          setSelectedVersionId(data.overview.version_id);
        }
      } catch (err: any) {
        setErrorMessage(
          err.message || "Failed to load exploratory data analysis report."
        );
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [corrMethod]
  );

  useEffect(() => {
    if (selectedDatasetId) {
      fetchReport(selectedDatasetId, selectedVersionId || undefined, corrMethod, false);
    }
  }, [selectedDatasetId, selectedVersionId, corrMethod, fetchReport]);

  const handleDatasetChange = (newDatasetId: string) => {
    setSelectedDatasetId(newDatasetId);
    const ds = datasets.find((d) => d.id === newDatasetId);
    if (ds) {
      setSelectedVersionId(ds.active_version_id || ds.current_version_id || "v1");
    }
  };

  const handleRefresh = () => {
    if (selectedDatasetId) {
      fetchReport(selectedDatasetId, selectedVersionId || undefined, corrMethod, true);
    }
  };

  const handleInspectPair = (colX: string, colY: string) => {
    setPairX(colX);
    setPairY(colY);
    setActiveTab("relationships");
  };

  const currentDataset = datasets.find((d) => d.id === selectedDatasetId);

  const missingColumns = report?.univariate
    ? Object.entries(report.univariate)
        .map(([name, stats]: [string, any]) => ({
          name,
          missingCount: stats.missing_count ?? 0,
          missingPct: stats.missing_percentage ?? 0,
          type: stats.data_type || "numeric",
        }))
        .filter((c) => c.missingCount > 0)
        .sort((a, b) => b.missingPct - a.missingPct)
    : [];

  const edaRecommendations = (report?.findings || []).slice(0, 4).map((f, i) => ({
    id: `finding-${i}`,
    title: f.title,
    description: f.description,
    impact: f.severity === "high" ? ("high" as const) : f.severity === "medium" ? ("medium" as const) : ("low" as const),
    actionLabel: "Explore In Depth",
    onAction: () => setActiveTab("findings"),
  }));

  return (
    <div className="flex flex-col min-h-[calc(100vh-100px)]">
      <AnalyticalWorkspaceHeader
        title="EDA"
        description="Explore distributions, relationships, and patterns."
        badgeText="Vectorized SciPy"
        status={isLoading ? "loading" : isRefreshing ? "running" : report ? "success" : "idle"}
        durationMs={report?.execution_time_ms}
        rowCount={report?.overview?.total_rows}
        primaryAction={
          <Button
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing || isLoading}
            className="h-9 px-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>{isRefreshing ? "Refreshing..." : "Refresh"}</span>
          </Button>
        }
        customDatasetSelector={
          <div className="flex items-center gap-1.5 bg-slate-900/60 p-1 rounded-lg border border-white/10">
            <span className="text-[11px] font-medium text-slate-400 pl-2 pr-0.5 uppercase tracking-wider hidden sm:inline">
              Dataset:
            </span>
            <DatasetSelector
              datasets={datasets.map((d) => ({
                id: d.id,
                name: d.name || (d as any).filename || d.id,
                rowCount: (d as any).row_count,
                versionName: (d as any).current_version_name || "V1",
              }))}
              activeDatasetId={selectedDatasetId}
              onSelectDataset={handleDatasetChange}
              size="sm"
            />
            {selectedVersionId && (
              <VersionSelector
                versions={[{ id: selectedVersionId, version_number: 1, is_current: true }]}
                activeVersionId={selectedVersionId}
                onSelectVersion={(v) => setSelectedVersionId(v)}
                size="sm"
              />
            )}
          </div>
        }
      />

      {/* Empty State if no datasets */}
      {datasets.length === 0 && !isLoading && (
        <div className="mb-6">
          <GuidedOnboarding
            title="Explore Data & Uncover Relationships"
            description="Understand what drives your metrics. Explore numerical distributions, calculate correlation matrices, identify skewness, and discover patterns automatically."
            badgeText="Exploratory Analysis"
            features={[
              "Instant univariate distributions, quantiles, and outliers",
              "Interactive Pearson & Spearman correlation matrices",
              "Automated key driver and bivariate relationship discovery",
            ]}
          />
        </div>
      )}

      {/* Error state */}
      {errorMessage && (
        <div className="p-4 mb-5 rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-300 text-sm">
          {errorMessage}
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="p-12 text-center rounded-xl border border-white/10 bg-slate-900/40 text-slate-400">
          <RefreshCw className="w-7 h-7 mx-auto mb-3 animate-spin text-indigo-400" />
          <h3 className="text-base font-medium text-white">
            Computing Automated EDA Intelligence...
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Extracting parametric moments, IQR fences, correlation matrices, and rule-based findings.
          </p>
        </div>
      )}

      {/* Main EDA Dashboard when Report Loaded */}
      {!isLoading && report && (
        <div className="flex-1">
          {/* 5 Common Tabs */}
          <div className="flex items-center gap-2 border-b border-white/[0.08] mb-6 overflow-x-auto pb-1">
            {[
              { id: "overview", label: "Overview", icon: "📋" },
              { id: "distributions", label: "Distributions", icon: "📊" },
              { id: "relationships", label: "Relationships", icon: "⚡" },
              { id: "missingness", label: `Missingness (${report.overview?.missing_cells_pct?.toFixed(1) || 0}%)`, icon: "🔍" },
              {
                id: "findings",
                label: `Findings (${report.findings.length})`,
                icon: "💡",
              },
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-semibold"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent"
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Panes */}
          {activeTab === "overview" && (
            <OverviewTab
              report={report}
              onSelectTab={(t) => {
                if (t === "univariate") setActiveTab("distributions");
                else if (t === "correlations") setActiveTab("relationships");
                else setActiveTab(t as any);
              }}
            />
          )}

          {activeTab === "distributions" && <UnivariateTab report={report} />}

          {activeTab === "relationships" && (
            <div className="space-y-6">
              <RelationshipTab
                report={report}
                initialColX={pairX}
                initialColY={pairY}
              />
              <div className="pt-4 border-t border-white/5">
                <CorrelationsTab
                  report={report}
                  onChangeMethod={(m) => setCorrMethod(m)}
                  onInspectPair={handleInspectPair}
                  isRefreshing={isRefreshing}
                />
              </div>
            </div>
          )}

          {activeTab === "missingness" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-white/10 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider">Missing Cells</span>
                  <div className="text-xl font-bold font-mono text-rose-400">
                    {report.overview?.missing_cells?.toLocaleString() || 0}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-white/10 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider">Missing Rate</span>
                  <div className="text-xl font-bold font-mono text-amber-400">
                    {(report.overview?.missing_cells_pct ?? 0).toFixed(2)}%
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-white/10 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider">Affected Columns</span>
                  <div className="text-xl font-bold font-mono text-indigo-300">
                    {missingColumns.length} / {report.overview?.total_columns || 0}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-white/10 space-y-1">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider">Duplicate Rows</span>
                  <div className="text-xl font-bold font-mono text-slate-200">
                    {report.overview?.duplicate_rows?.toLocaleString() || 0}
                  </div>
                </div>
              </div>

              <div className="p-5 rounded-xl border border-white/10 bg-slate-900/60 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-white">Missing Values by Column</h4>
                    <p className="text-xs text-slate-400">Null frequencies requiring imputation or cleaning</p>
                  </div>
                  <Link
                    to="/cleaning"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Clean with AI</span>
                  </Link>
                </div>

                {missingColumns.length === 0 ? (
                  <div className="py-8 text-center text-xs text-emerald-400 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                    No missing values detected in this dataset! Complete data integrity confirmed.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {missingColumns.map((col) => (
                      <div
                        key={col.name}
                        className="p-3 rounded-lg bg-slate-950/60 border border-white/5 flex items-center justify-between gap-4"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between mb-1 text-xs">
                            <span className="font-mono font-medium text-slate-200">{col.name}</span>
                            <span className="font-mono text-slate-400">
                              {col.missingCount.toLocaleString()} missing ({col.missingPct.toFixed(1)}%)
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-rose-500 rounded-full"
                              style={{ width: `${Math.min(col.missingPct, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "findings" && <FindingsTab findings={report.findings} />}
        </div>
      )}

      {/* Secondary Information: History, Details, Metadata, Recommendations */}
      <SecondaryInfoPanel
        metadata={{
          datasetName: currentDataset?.name || "Active Dataset",
          versionName: selectedVersionId || "V1",
          rowCount: report?.overview?.total_rows,
          columnCount: report?.overview?.total_columns,
          engine: "SciPy + DuckDB Vectorized",
          executionTimeMs: report?.execution_time_ms,
          customFields: {
            "Correlation Metric": corrMethod.toUpperCase(),
            "Missing Cells": `${report?.overview?.missing_cells ?? 0} (${(report?.overview?.missing_cells_pct ?? 0).toFixed(1)}%)`,
            "Duplicate Rows": report?.overview?.duplicate_rows ?? 0,
          },
        }}
        recommendations={edaRecommendations}
      />
    </div>
  );
}
