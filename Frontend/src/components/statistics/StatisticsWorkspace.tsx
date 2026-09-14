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
import { AnalyticalWorkspaceHeader } from "@/components/layout/AnalyticalWorkspaceHeader";
import { SecondaryInfoPanel } from "@/components/layout/SecondaryInfoPanel";
import { DatasetSelector } from "@/components/ui/DatasetSelector";
import { VersionSelector } from "@/components/ui/VersionSelector";
import { Button } from "@/components/ui/button";
import { Play, Sparkles, SlidersHorizontal, ArrowRight } from "lucide-react";

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

  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");

  const currentDataset = datasets.find((d) => d.id === selectedDatasetId);

  const workflowSteps = [
    { id: "builder", label: "Analysis Builder", status: "completed" as const },
    { id: "results", label: "Results", status: (currentResult ? "completed" : "current") as const },
    { id: "assumptions", label: "Assumptions", status: (currentResult?.assumptions && currentResult.assumptions.length > 0 ? "completed" : "pending") as const },
    { id: "diagnostics", label: "Diagnostics", status: (currentResult?.effect_sizes && currentResult.effect_sizes.length > 0 ? "completed" : "pending") as const },
    { id: "interpretation", label: "Interpretation", status: (currentResult?.findings && currentResult.findings.length > 0 ? "completed" : "pending") as const },
  ];

  return (
    <div className="flex flex-col min-h-[calc(100vh-100px)]">
      <AnalyticalWorkspaceHeader
        title="Statistics"
        description="Run statistical analysis with transparent methodology."
        badgeText="SciPy + statsmodels"
        steps={workflowSteps}
        currentStepId={currentResult ? "results" : "builder"}
        mode={mode}
        onToggleMode={setMode}
        status={isLoading ? "running" : currentResult ? "success" : "idle"}
        durationMs={currentResult?.execution_time_ms}
        primaryAction={
          <Button
            size="sm"
            onClick={handleExecute}
            disabled={isLoading || targetColumns.length === 0}
            className="h-9 px-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs gap-1.5 shadow-sm"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isLoading ? "Running..." : "Run Analysis"}</span>
          </Button>
        }
        secondaryActions={
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handleAutoRecommend}
              className="h-9 px-2.5 text-xs border-white/10 bg-slate-900/60 hover:bg-slate-850 hover:border-white/20 text-indigo-300 gap-1"
            >
              <Sparkles className="w-3 h-3" />
              <span>Auto-Recommend</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab(activeTab === "workspace" ? "history" : "workspace")}
              className={`h-9 px-2.5 text-xs border-white/10 ${activeTab === "history" ? "bg-indigo-600/20 text-white border-indigo-500/40" : "bg-slate-900/60 text-slate-300"}`}
            >
              <span>History ({history.length})</span>
            </Button>
          </div>
        }
        customDatasetSelector={
          <div className="flex items-center gap-1.5 bg-slate-900/60 p-1 rounded-lg border border-white/10">
            <span className="text-[11px] font-medium text-slate-400 pl-2 pr-0.5 uppercase tracking-wider hidden sm:inline">
              Dataset:
            </span>
            <DatasetSelector
              datasets={datasets.map((d) => ({
                id: d.id,
                name: d.name,
                rowCount: (d as any).row_count,
                versionName: (d as any).current_version_name || "V1",
              }))}
              activeDatasetId={selectedDatasetId}
              onSelectDataset={(id) => setSelectedDatasetId(id)}
              size="sm"
            />
            {versions.length > 0 && (
              <VersionSelector
                versions={versions.map((v) => ({
                  id: v.version_id,
                  version_number: parseInt(v.version_id.replace(/\D/g, "") || "1"),
                  row_count: v.row_count,
                  is_current: v.version_id === selectedVersionId,
                }))}
                activeVersionId={selectedVersionId || versions[0]?.version_id}
                onSelectVersion={(vid) => setSelectedVersionId(vid)}
                size="sm"
              />
            )}
          </div>
        }
      />

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

      {/* Secondary Information: History, Details, Metadata, Recommendations */}
      <SecondaryInfoPanel
        metadata={{
          datasetName: currentDataset?.name || "Active Dataset",
          versionName: selectedVersionId || "V1",
          engine: "SciPy + statsmodels (Deterministic)",
          executionTimeMs: currentResult?.execution_time_ms,
          customFields: {
            "Selected Method": currentMethodItem?.name || selectedMethod,
            "Target Column(s)": targetColumns.join(", ") || "None",
            "Group Column(s)": groupColumns.join(", ") || "None",
            "Significance Alpha": alpha,
            "Confidence Level": `${Math.round(confidenceLevel * 100)}%`,
          },
        }}
        historyEntries={history.map((h) => ({
          id: h.result_id,
          title: `${h.method_name} on ${(h.parameters as any)?.target_columns?.join(", ") || "columns"}`,
          timestamp: h.executed_at,
          status: "success" as const,
          durationMs: h.execution_time_ms,
          summary: h.executive_summary?.slice(0, 100) + "...",
        }))}
        onSelectHistoryEntry={async (entry) => {
          const res = await statisticsApi.getAnalysis(entry.id);
          setCurrentResult(res);
          setActiveTab("workspace");
        }}
        recommendations={[
          {
            id: "rec-stat-normality",
            title: "Automated Normality & Variance Check",
            description: "Assess skewness and variance homogeneity to ensure parametric assumptions hold before decision-making.",
            impact: "medium" as const,
            actionLabel: "Verify Assumptions",
            onAction: handleAutoRecommend,
          },
        ]}
      />
    </div>
  );
};
