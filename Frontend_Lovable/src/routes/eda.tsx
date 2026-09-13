import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import { EDAIcon, UploadIcon, RefreshIcon } from "@/components/icons";
import { apiClient } from "@/services/api";
import { DatasetResponse, EDAReport } from "@/types";
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
    "overview" | "univariate" | "correlations" | "relationships" | "findings"
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

  return (
    <div className="ax-stack">
      {/* Page Header */}
      <PageHeader
        title="Exploratory Data Analysis (EDA)"
        description="Vectorized statistical distributions, pairwise correlations, time-series trends, and automated rule-based findings."
        badge={{ text: "Phase 7 — Complete", variant: "emerald" }}
      />

      {/* Dataset & Version Bar */}
      {datasets.length > 0 && (
        <div
          className="card"
          style={{
            padding: "0.875rem 1.25rem",
            marginBottom: "1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontWeight: 500 }}>
                Dataset:
              </span>
              <select
                value={selectedDatasetId}
                onChange={(e) => handleDatasetChange(e.target.value)}
                className="input"
                style={{ fontSize: "0.8125rem", minWidth: "180px" }}
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name || d.original_filename || d.filename || d.id}
                  </option>
                ))}
              </select>
            </div>

            {selectedVersionId && (
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Version:</span>
                <span className="badge badge-indigo" style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                  {selectedVersionId}
                </span>
              </div>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing || isLoading}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.8125rem" }}
              title="Recompute and refresh deterministic EDA metrics"
            >
              <RefreshIcon size={14} className={isRefreshing ? "spin" : ""} />
              <span>{isRefreshing ? "Recomputing..." : "Refresh Analysis"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Empty State if no datasets */}
      {datasets.length === 0 && !isLoading && (
        <div style={{ marginBottom: "2rem" }}>
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
        <div
          className="card"
          style={{
            padding: "1.25rem",
            marginBottom: "1.5rem",
            backgroundColor: "rgba(244, 63, 94, 0.08)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            color: "#f43f5e",
            fontSize: "0.875rem",
          }}
        >
          {errorMessage}
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="card" style={{ padding: "4rem", textAlign: "center", color: "var(--text-muted)" }}>
          <div className="spin" style={{ display: "inline-block", marginBottom: "1rem" }}>
            <RefreshIcon size={28} />
          </div>
          <h3 style={{ fontSize: "1.125rem", color: "var(--text-primary)" }}>
            Computing Automated EDA Intelligence...
          </h3>
          <p style={{ fontSize: "0.8125rem", marginTop: "0.35rem" }}>
            Extracting parametric moments, IQR fences, correlation matrices, and rule-based findings.
          </p>
        </div>
      )}

      {/* Main EDA Dashboard when Report Loaded */}
      {!isLoading && report && (
        <div>
          {/* Navigation Tabs */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              borderBottom: "1px solid var(--border-subtle)",
              marginBottom: "1.5rem",
              overflowX: "auto",
            }}
          >
            {[
              { id: "overview", label: "Overview", icon: "📋" },
              { id: "univariate", label: "Univariate Explorer", icon: "📊" },
              { id: "correlations", label: "Correlations", icon: "🔥" },
              { id: "relationships", label: "Relationship Studio", icon: "⚡" },
              {
                id: "findings",
                label: `Automated Findings (${report.findings.length})`,
                icon: "💡",
              },
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    padding: "0.75rem 1rem",
                    fontSize: "0.875rem",
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? "#818cf8" : "var(--text-secondary)",
                    borderBottom: isActive ? "2px solid #6366f1" : "2px solid transparent",
                    background: "none",
                    borderTop: "none",
                    borderLeft: "none",
                    borderRight: "none",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    transition: "all 0.15s ease",
                  }}
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
              onSelectTab={(t) => setActiveTab(t as any)}
            />
          )}

          {activeTab === "univariate" && <UnivariateTab report={report} />}

          {activeTab === "correlations" && (
            <CorrelationsTab
              report={report}
              onChangeMethod={(m) => setCorrMethod(m)}
              onInspectPair={handleInspectPair}
              isRefreshing={isRefreshing}
            />
          )}

          {activeTab === "relationships" && (
            <RelationshipTab
              report={report}
              initialColX={pairX}
              initialColY={pairY}
            />
          )}

          {activeTab === "findings" && <FindingsTab findings={report.findings} />}
        </div>
      )}
    </div>
  );
}
