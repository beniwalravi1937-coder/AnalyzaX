"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/services/api";
import { DatasetResponse, DatasetVersion } from "@/types";
import { MethodCatalogItem, StatisticalResult } from "@/types/statistics";
import { statisticsApi } from "@/services/statisticsApi";
import { StatisticsMethodSelector } from "./StatisticsMethodSelector";
import { TestConfiguration } from "./TestConfiguration";
import { StatisticsResultView } from "./StatisticsResult";
import { StatisticsHistory } from "./StatisticsHistory";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";

export const StatisticsWorkspace: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("v1");
  const [columns, setColumns] = useState<string[]>([]);
  const [methods, setMethods] = useState<MethodCatalogItem[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>("t_test_welch");

  // Configuration state
  const [targetColumns, setTargetColumns] = useState<string[]>([]);
  const [groupColumns, setGroupColumns] = useState<string[]>([]);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95);
  const [alternative, setAlternative] = useState<string>("two-sided");
  const [multipleTesting, setMultipleTesting] = useState<string>("none");

  // Execution & history state
  const [currentResult, setCurrentResult] = useState<StatisticalResult | null>(null);
  const [history, setHistory] = useState<StatisticalResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"workspace" | "history">("workspace");

  // 1. Initial load of datasets and method catalog
  useEffect(() => {
    const init = async () => {
      try {
        const [dsRes, mList] = await Promise.all([
          api.listDatasets(),
          statisticsApi.getMethods(),
        ]);
        const dsList = dsRes.datasets || [];
        setDatasets(dsList);
        setMethods(mList);
        if (dsList.length > 0) {
          setSelectedDatasetId(dsList[0].id);
        }
      } catch (err: any) {
        console.error("Error initializing statistics workspace:", err);
      }
    };
    init();
  }, []);

  // 2. Load versions and columns when dataset changes
  useEffect(() => {
    if (!selectedDatasetId) return;

    const loadDatasetMeta = async () => {
      try {
        const vList = await api.listVersions(selectedDatasetId);
        setVersions(vList);
        const activeV = vList.find((v) => v.status === "READY") || vList[0];
        const vId = activeV ? activeV.version_id : "v1";
        setSelectedVersionId(vId);

        // Fetch schema/columns from profile
        const prof = await api.getDatasetProfile(selectedDatasetId).catch(() => null);
        if (prof?.columns) {
          const colNames = prof.columns.map((c: any) => c.name);
          setColumns(colNames);
          if (colNames.length > 0) {
            setTargetColumns([colNames[0]]);
            if (colNames.length > 1) {
              setGroupColumns([colNames[1]]);
            }
          }
        }
      } catch (err) {
        console.error("Failed to load version/profile:", err);
      }
    };
    loadDatasetMeta();
  }, [selectedDatasetId]);

  // 3. Load history when dataset or version changes
  useEffect(() => {
    if (!selectedDatasetId) return;
    const loadHistory = async () => {
      try {
        const hist = await statisticsApi.getHistory(selectedDatasetId, selectedVersionId);
        setHistory(hist);
      } catch (e) {
        console.error("Failed to load history:", e);
      }
    };
    loadHistory();
  }, [selectedDatasetId, selectedVersionId]);

  // Handle run analysis
  const handleExecute = async () => {
    if (!selectedDatasetId || targetColumns.length === 0) return;
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await statisticsApi.runAnalysis({
        dataset_id: selectedDatasetId,
        dataset_version_id: selectedVersionId,
        analysis_type: methods.find((m) => m.method === selectedMethod)?.category.toLowerCase() || "inference",
        method: selectedMethod,
        target_columns: targetColumns,
        group_columns: groupColumns,
        parameters: {
          alpha,
          confidence_level: confidenceLevel,
          alternative,
          multiple_testing: multipleTesting,
        },
      });

      setCurrentResult(res);
      // Refresh history
      const updatedHist = await statisticsApi.getHistory(selectedDatasetId, selectedVersionId);
      setHistory(updatedHist);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute statistical analysis");
    } finally {
      setIsLoading(false);
    }
  };

  // Recommender action
  const handleAutoRecommend = async () => {
    if (!selectedDatasetId || targetColumns.length === 0) return;
    try {
      const rec = await statisticsApi.recommendMethod({
        dataset_id: selectedDatasetId,
        dataset_version_id: selectedVersionId,
        target_columns: targetColumns,
        group_columns: groupColumns,
      });
      setSelectedMethod(rec.recommended_method);
    } catch (err) {
      console.error("Auto recommendation failed:", err);
    }
  };

  const currentMethodItem = methods.find((m) => m.method === selectedMethod) || methods[0];

  if (datasets.length === 0) {
    return (
      <GuidedOnboarding
        title="Hypothesis Testing & Statistical Analysis"
        description="Verify business assumptions with mathematical confidence. Compare group averages, evaluate treatment effects, and validate significance with automated plain-language explanations."
        badgeText="Statistical Testing"
        features={[
          "Parametric & non-parametric tests (t-test, ANOVA, Mann-Whitney, Chi-square)",
          "Automated assumption diagnostics & effect size metrics",
          "Executive plain-language summaries explaining what the p-value means",
        ]}
        onUploadSuccess={async () => {
          const dsRes = await api.listDatasets();
          const dsList = dsRes.datasets || [];
          setDatasets(dsList);
          if (dsList.length > 0) {
            setSelectedDatasetId(dsList[0].id);
          }
        }}
      />
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Top Bar: Dataset & Version Picker */}
      <div
        style={{
          padding: "1rem 1.25rem",
          borderRadius: "var(--radius-md, 8px)",
          background: "var(--bg-surface, rgba(255, 255, 255, 0.02))",
          border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.2rem" }}>
              Active Dataset
            </label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="input input-sm"
              style={{ minWidth: "180px" }}
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.2rem" }}>
              Dataset Version
            </label>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(e.target.value)}
              className="input input-sm"
              style={{ minWidth: "120px" }}
            >
              {versions.map((v) => (
                <option key={v.version_id} value={v.version_id}>
                  {v.version_id} ({v.version_label || "Version"})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* View Toggle */}
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={() => setActiveTab("workspace")}
            className={`btn btn-sm ${activeTab === "workspace" ? "btn-primary" : "btn-secondary"}`}
          >
            Analysis Workspace
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("history")}
            className={`btn btn-sm ${activeTab === "history" ? "btn-primary" : "btn-secondary"}`}
          >
            History ({history.length})
          </button>
        </div>
      </div>

      {errorMsg && (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderRadius: "6px",
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "#ef4444",
            fontSize: "0.875rem",
          }}
        >
          {errorMsg}
        </div>
      )}

      {activeTab === "history" ? (
        <StatisticsHistory
          history={history}
          activeId={currentResult?.result_id}
          onSelect={async (id) => {
            const res = await statisticsApi.getAnalysis(id);
            setCurrentResult(res);
            setActiveTab("workspace");
          }}
          onDelete={async (id) => {
            await statisticsApi.deleteAnalysis(id);
            const updated = await statisticsApi.getHistory(selectedDatasetId, selectedVersionId);
            setHistory(updated);
            if (currentResult?.result_id === id) {
              setCurrentResult(null);
            }
          }}
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Method Selection */}
          <StatisticsMethodSelector
            methods={methods}
            selectedMethod={selectedMethod}
            onSelectMethod={(m) => setSelectedMethod(m)}
          />

          {/* Test Configuration Form */}
          {currentMethodItem && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  onClick={handleAutoRecommend}
                  className="btn btn-xs btn-ghost"
                  style={{ color: "var(--primary)" }}
                >
                  ⚡ Auto-Recommend Method for Selected Columns
                </button>
              </div>

              <TestConfiguration
                methodItem={currentMethodItem}
                columns={columns}
                targetColumns={targetColumns}
                groupColumns={groupColumns}
                alpha={alpha}
                confidenceLevel={confidenceLevel}
                alternative={alternative}
                multipleTesting={multipleTesting}
                onTargetChange={setTargetColumns}
                onGroupChange={setGroupColumns}
                onAlphaChange={setAlpha}
                onConfidenceChange={setConfidenceLevel}
                onAlternativeChange={setAlternative}
                onMultipleTestingChange={setMultipleTesting}
                onRun={handleExecute}
                isLoading={isLoading}
              />
            </div>
          )}

          {/* Results Display */}
          {currentResult && (
            <StatisticsResultView result={currentResult} />
          )}
        </div>
      )}
    </div>
  );
};
