"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/services/api";
import { DatasetResponse, DatasetVersion } from "@/types";
import {
  CrossValidationConfig,
  HyperparameterSearchConfig,
  MLExperiment,
  MLExperimentRequest,
  MLModelDefinition,
  MLResult,
  MLTaskType,
  PreprocessingConfig,
  SplitConfig,
  SuitabilityReport,
} from "@/types/ml";
import { useDataset } from "@/context/DatasetContext";
import {
  getLocalProfile,
  getLocalSampleRows,
  STUDENT_EXAM_PERFORMANCE_COLUMNS,
} from "@/services/localDatasetEngine";
import { sqlApi } from "@/services/sqlApi";
import { DEFAULT_ML_MODELS, mlApi } from "@/services/mlApi";
import { MLSuitabilityPanel } from "./MLSuitabilityPanel";
import { TaskTargetSelector } from "./TaskTargetSelector";
import { FeatureSelector } from "./FeatureSelector";
import { PreprocessingConfigView } from "./PreprocessingConfigView";
import { SplitValidationConfigView } from "./SplitValidationConfigView";
import { ModelSelector } from "./ModelSelector";
import { ModelComparisonLeaderboard } from "./ModelComparisonLeaderboard";
import { ModelDiagnosticsView } from "./ModelDiagnosticsView";
import { FeatureImportanceView } from "./FeatureImportanceView";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import { PredictionRunner } from "./PredictionRunner";
import { MLExperimentHistory } from "./MLExperimentHistory";

export const MLWorkspace: React.FC = () => {
  const { activeDataset, datasets: contextDatasets } = useDataset();

  // Datasets & Versions
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("v1");
  const [columns, setColumns] = useState<string[]>([]);
  const [isColumnsLoading, setIsColumnsLoading] = useState<boolean>(false);

  // Workflow Mode & Tabs
  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");
  const [activeTab, setActiveTab] = useState<"studio" | "history">("studio");

  // Suitability state
  const [suitability, setSuitability] = useState<SuitabilityReport | null>(null);
  const [isSuitabilityLoading, setIsSuitabilityLoading] = useState<boolean>(false);

  // Task & Features Configuration
  const [taskType, setTaskType] = useState<MLTaskType>("regression");
  const [targetColumn, setTargetColumn] = useState<string>("");
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);

  // Preprocessing, Splitting & CV
  const [preprocessingConfig, setPreprocessingConfig] = useState<PreprocessingConfig>({
    numeric_impute: "median",
    numeric_scale: "standard",
    categorical_impute: "most_frequent",
    categorical_encode: "one_hot",
    extract_date_features: false,
    date_features: ["year", "month", "day", "day_of_week"],
  });

  const [splitConfig, setSplitConfig] = useState<SplitConfig>({
    train_size: 0.70,
    val_size: 0.15,
    test_size: 0.15,
    random_seed: 42,
    stratify: true,
  });

  const [cvConfig, setCVConfig] = useState<CrossValidationConfig>({
    enabled: true,
    n_splits: 5,
    shuffle: true,
    random_seed: 42,
    stratified: true,
  });

  // Models & Search
  const [availableModels, setAvailableModels] = useState<MLModelDefinition[]>([]);
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);
  const [modelParameters, setModelParameters] = useState<Record<string, Record<string, any>>>({});
  const [searchConfig, setSearchConfig] = useState<HyperparameterSearchConfig>({
    enabled: false,
    search_method: "random",
    param_grid: {},
    n_iter: 10,
  });
  const [primaryMetric, setPrimaryMetric] = useState<string>("");

  // Execution & Results
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [currentExperimentId, setCurrentExperimentId] = useState<string | null>(null);
  const [result, setResult] = useState<MLResult | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [history, setHistory] = useState<MLExperiment[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync with global DatasetContext
  useEffect(() => {
    if (contextDatasets && contextDatasets.length > 0) {
      setDatasets(contextDatasets);
    }
    if (activeDataset && (!selectedDatasetId || !datasets.some((d) => d.id === selectedDatasetId))) {
      setSelectedDatasetId(activeDataset.id);
    }
  }, [activeDataset, contextDatasets]);

  // 1. Initial Load: Datasets & Registered Models
  useEffect(() => {
    const init = async () => {
      try {
        const [dsRes, modelsList] = await Promise.all([
          api.listDatasets().catch(() => ({ datasets: [] })),
          mlApi.getModels().catch(() => DEFAULT_ML_MODELS),
        ]);
        const dsList = dsRes.datasets || [];
        if (dsList.length > 0) {
          setDatasets((prev) => (prev.length > 0 ? prev : dsList));
          setSelectedDatasetId((prev) => prev || activeDataset?.id || dsList[0].id);
        }
        setAvailableModels(modelsList.length > 0 ? modelsList : DEFAULT_ML_MODELS);
      } catch (err) {
        console.error("Failed to initialize ML workspace:", err);
        setAvailableModels(DEFAULT_ML_MODELS);
      }
    };
    init();
  }, []);

  // 2. Load Versions, Schema & Trigger Suitability Scan
  const loadDatasetDetails = async () => {
    if (!selectedDatasetId) return;
    setIsColumnsLoading(true);
    setErrorMsg(null);

    try {
      // Step A: Load versions with safe fallback
      const vList = await api.listVersions(selectedDatasetId).catch(() => [
        { version_id: "v1", version_label: "Base", status: "READY", dataset_id: selectedDatasetId } as DatasetVersion,
      ]);
      setVersions(vList);
      const activeV = vList.find((v) => v.status === "READY") || vList[0];
      const vId = activeV ? activeV.version_id : "v1";
      setSelectedVersionId(vId);

      // Step B: Robust multi-tier column resolution
      let colNames: string[] = [];

      // 1. Dataset Profile API
      try {
        const prof = await api.getDatasetProfile(selectedDatasetId);
        if (prof?.columns && prof.columns.length > 0) {
          colNames = prof.columns.map((c: any) => (typeof c === "string" ? c : c.name));
        }
      } catch {
        // Fallback
      }

      // 2. Local Dataset Engine Profile
      if (colNames.length === 0) {
        const localProf = getLocalProfile(selectedDatasetId);
        if (localProf?.columns && localProf.columns.length > 0) {
          colNames = localProf.columns.map((c: any) => (typeof c === "string" ? c : c.name));
        }
      }

      // 3. SQL Schema Introspection
      if (colNames.length === 0) {
        try {
          const sInfo = await sqlApi.getSchema(selectedDatasetId, vId);
          if (sInfo?.columns && sInfo.columns.length > 0) {
            colNames = sInfo.columns.map((c) => c.name);
          }
        } catch {
          // Fallback
        }
      }

      // 4. Sample Rows introspection
      if (colNames.length === 0) {
        const rows = getLocalSampleRows(selectedDatasetId);
        if (rows && rows.length > 0) {
          colNames = Object.keys(rows[0]);
        }
      }

      // 5. Preloaded fallback for student_exam_performance
      if (colNames.length === 0) {
        const dsObj = datasets.find((d) => d.id === selectedDatasetId) || activeDataset;
        const dsName = (dsObj?.name || dsObj?.original_filename || selectedDatasetId).toLowerCase();
        if (dsName.includes("student") || dsName.includes("exam") || dsName.includes("performance")) {
          colNames = [...STUDENT_EXAM_PERFORMANCE_COLUMNS];
        }
      }

      if (colNames.length > 0) {
        setColumns(colNames);

        // Auto-select candidate target column if not set or invalid
        let newTarget = targetColumn;
        if (!newTarget || !colNames.includes(newTarget)) {
          if (taskType === "regression") {
            newTarget = colNames.find((c) => c === "exam_score" || c.includes("score") || c.includes("sales") || c.includes("price")) || colNames[colNames.length - 1];
          } else if (taskType === "binary_classification") {
            newTarget = colNames.find((c) => c === "pass_status" || c.includes("status") || c.includes("churn")) || colNames[colNames.length - 1];
          } else if (taskType === "multiclass_classification") {
            newTarget = colNames.find((c) => c === "performance_grade" || c.includes("grade") || c.includes("level")) || colNames[colNames.length - 1];
          }
          setTargetColumn(newTarget);
        }

        // Auto-select clean recommended predictors if empty
        if (selectedFeatures.length === 0) {
          const defaultPreds = colNames.filter(
            (c) => c !== newTarget && !/id$|^id$|^uuid$|identifier|student_id|order_id|customer_id/i.test(c)
          );
          setSelectedFeatures(defaultPreds);
        }

        // Run automated suitability
        runSuitabilityCheck(selectedDatasetId, vId, newTarget, taskType, colNames);
      } else {
        setColumns([]);
      }

      // Load experiment history
      loadHistory(selectedDatasetId, vId);
    } catch (err) {
      console.error("Failed to load dataset details:", err);
    } finally {
      setIsColumnsLoading(false);
    }
  };

  useEffect(() => {
    loadDatasetDetails();
  }, [selectedDatasetId]);

  // 3. Automated Suitability Scanner
  const runSuitabilityCheck = async (
    dsId = selectedDatasetId,
    vId = selectedVersionId,
    target = targetColumn,
    task = taskType,
    feats = selectedFeatures
  ) => {
    if (!dsId) return;
    setIsSuitabilityLoading(true);
    try {
      const rep = await mlApi.checkSuitability({
        dataset_id: dsId,
        dataset_version_id: vId,
        target_column: target || undefined,
        task_type: task,
        candidate_features: feats.length > 0 ? feats : undefined,
      });
      setSuitability(rep);

      // Auto-set recommended target if not set
      if (!target && rep.recommended_target) {
        setTargetColumn(rep.recommended_target);
      }
      if (rep.recommended_task) {
        setTaskType(rep.recommended_task);
      }
      if (selectedFeatures.length === 0 && rep.recommended_features && rep.recommended_features.length > 0) {
        setSelectedFeatures(rep.recommended_features);
      }
    } catch (err) {
      console.error("Suitability check error:", err);
    } finally {
      setIsSuitabilityLoading(false);
    }
  };

  // 4. Load History
  const loadHistory = async (dsId = selectedDatasetId, vId = selectedVersionId) => {
    setIsHistoryLoading(true);
    try {
      const list = await mlApi.listExperiments(dsId, vId);
      setHistory(list);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  // 5. Update Default Models when Task changes
  useEffect(() => {
    const matching = availableModels.filter(
      (m) => m.task_types.includes(taskType) && !m.model_id.startsWith("dummy")
    );
    if (matching.length > 0) {
      // Pick top 2 recommended models by default
      const defaultPicks = matching.slice(0, 2).map((m) => m.model_id);
      setSelectedModelIds(defaultPicks);
    }

    // Set default primary metric
    if (taskType === "regression") setPrimaryMetric("rmse");
    else if (taskType === "clustering") setPrimaryMetric("inertia");
    else setPrimaryMetric("f1_macro");
  }, [taskType, availableModels]);

  // Validation state computation
  const isTargetRequired = taskType !== "clustering";
  const hasValidTarget = !isTargetRequired || Boolean(targetColumn && columns.includes(targetColumn));
  const hasPredictors = selectedFeatures.length > 0;
  const hasModels = selectedModelIds.length > 0;
  const isConfigValid = Boolean(selectedDatasetId) && hasValidTarget && hasPredictors && hasModels && !isTraining;

  // 6. Execute Experiment
  const handleRunExperiment = async () => {
    setErrorMsg(null);

    if (taskType !== "clustering" && !targetColumn) {
      setErrorMsg("Please select a target column to predict.");
      return;
    }
    if (selectedFeatures.length === 0) {
      setErrorMsg("Please select at least one predictor variable.");
      return;
    }
    if (selectedModelIds.length === 0) {
      setErrorMsg("Please select at least one algorithm to train.");
      return;
    }

    setIsTraining(true);
    setResult(null);

    const req: MLExperimentRequest = {
      dataset_id: selectedDatasetId,
      dataset_version_id: selectedVersionId,
      task_type: taskType,
      target_column: taskType !== "clustering" ? targetColumn : undefined,
      feature_columns: selectedFeatures,
      preprocessing: preprocessingConfig,
      split: splitConfig,
      cross_validation: cvConfig,
      models: selectedModelIds,
      model_parameters: modelParameters,
      hyperparameter_search: searchConfig,
      primary_metric: primaryMetric,
      random_seed: splitConfig.random_seed,
      mode: mode,
    };

    try {
      const res = await mlApi.runExperiment(req);
      setResult(res);
      setCurrentExperimentId(res.experiment_id);
      if (res.best_model_run_id) {
        setSelectedRunId(res.best_model_run_id);
      } else if (res.model_runs.length > 0) {
        setSelectedRunId(res.model_runs[0].model_run_id);
      }
      loadHistory();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to train models");
    } finally {
      setIsTraining(false);
    }
  };

  const handleLoadHistoricResult = async (expId: string) => {
    setIsTraining(true);
    setErrorMsg(null);
    try {
      const res = await mlApi.getExperimentResult(expId);
      setResult(res);
      setCurrentExperimentId(res.experiment_id);
      if (res.best_model_run_id) {
        setSelectedRunId(res.best_model_run_id);
      } else if (res.model_runs.length > 0) {
        setSelectedRunId(res.model_runs[0].model_run_id);
      }
      setActiveTab("studio");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load experiment result");
    } finally {
      setIsTraining(false);
    }
  };

  const selectedModelRun = result?.model_runs.find((r) => r.model_run_id === selectedRunId);

  if (datasets.length === 0) {
    return (
      <GuidedOnboarding
        title="Train Predictive Machine Learning Models"
        description="Build machine learning models to predict customer churn, classify outcomes, and forecast values with zero data science coding required. Complete with automated feature encoding and model benchmarks."
        badgeText="Machine Learning Studio"
        features={[
          "Classification & regression with automated algorithm benchmarking",
          "Leakage-free preprocessing, train/test splitting, and cross-validation",
          "Interactive live what-if scenarios & model prediction explorer",
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
      {/* Top Header Bar with Mode Toggle & History Tab */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          padding: "0.875rem 1.25rem",
          borderRadius: "8px",
          background: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
        }}
      >
        {/* Dataset & Version Selectors */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <label htmlFor="ml-dataset-select" style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Dataset</label>
            <select
              id="ml-dataset-select"
              aria-label="Select Dataset"
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="input"
              style={{ fontSize: "0.8125rem", padding: "0.3rem 0.6rem" }}
            >
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="ml-version-select" style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Dataset Version</label>
            <select
              id="ml-version-select"
              aria-label="Select Dataset Version"
              value={selectedVersionId}
              onChange={(e) => {
                setSelectedVersionId(e.target.value);
                runSuitabilityCheck(selectedDatasetId, e.target.value);
                loadHistory(selectedDatasetId, e.target.value);
              }}
              className="input"
              style={{ fontSize: "0.8125rem", padding: "0.3rem 0.6rem" }}
            >
              {versions.map((v) => (
                <option key={v.version_id} value={v.version_id}>
                  {v.version_id} ({v.version_label || "Base"})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Mode Toggle & Workspace Navigation */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {/* Beginner vs Advanced Mode Toggle */}
          <div
            style={{
              display: "flex",
              borderRadius: "6px",
              background: "var(--bg-subtle)",
              padding: "2px",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <button
              type="button"
              onClick={() => setMode("beginner")}
              className={`btn btn-sm ${mode === "beginner" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            >
              Standard Mode
            </button>
            <button
              type="button"
              onClick={() => setMode("advanced")}
              className={`btn btn-sm ${mode === "advanced" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            >
              Advanced Mode
            </button>
          </div>

          {/* Navigation Tabs */}
          <div style={{ display: "flex", gap: "0.375rem" }}>
            <button
              type="button"
              onClick={() => setActiveTab("studio")}
              className={`btn btn-sm ${activeTab === "studio" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.75rem" }}
            >
              ML Studio
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("history")}
              className={`btn btn-sm ${activeTab === "history" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.75rem" }}
            >
              History ({history.length})
            </button>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div
          style={{
            padding: "0.875rem 1rem",
            borderRadius: "8px",
            background: "var(--error-bg, #ef444415)",
            border: "1px solid var(--error-border, #ef444455)",
            color: "var(--color-error, #ef4444)",
            fontSize: "0.8125rem",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* TAB 1: STUDIO */}
      {activeTab === "studio" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Suitability Panel */}
          <MLSuitabilityPanel
            report={suitability}
            isLoading={isSuitabilityLoading}
            onRefresh={() => runSuitabilityCheck()}
          />

          {/* Configuration Form Card */}
          <div
            style={{
              padding: "1.25rem",
              borderRadius: "8px",
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              display: "flex",
              flexDirection: "column",
              gap: "1.5rem",
            }}
          >
            {/* Task and Target */}
            <TaskTargetSelector
              taskType={taskType}
              onTaskTypeChange={(t) => {
                setTaskType(t);
                if (t === "regression" && targetColumn === "pass_status") {
                  setTargetColumn("exam_score");
                  setSelectedFeatures((prev) => prev.filter((f) => f !== "exam_score"));
                } else if ((t === "binary_classification" || t === "multiclass_classification") && targetColumn === "exam_score") {
                  const newT = t === "binary_classification" ? "pass_status" : "performance_grade";
                  setTargetColumn(newT);
                  setSelectedFeatures((prev) => prev.filter((f) => f !== newT));
                }
                runSuitabilityCheck(undefined, undefined, undefined, t);
              }}
              targetColumn={targetColumn}
              onTargetColumnChange={(tgt) => {
                setTargetColumn(tgt);
                setSelectedFeatures((prev) => prev.filter((f) => f !== tgt));
                runSuitabilityCheck(undefined, undefined, tgt);
              }}
              columns={columns}
              recommendedTask={suitability?.recommended_task}
              recommendedTarget={suitability?.recommended_target}
              classDistribution={suitability?.class_distribution}
            />

            {/* Feature Selection */}
            <FeatureSelector
              columns={columns}
              targetColumn={targetColumn}
              selectedFeatures={selectedFeatures}
              onSelectedFeaturesChange={setSelectedFeatures}
              recommendedFeatures={suitability?.recommended_features || []}
              excludedFeatures={suitability?.excluded_features || {}}
              isLoading={isColumnsLoading}
              onReloadColumns={loadDatasetDetails}
            />

            {/* Advanced Section: Preprocessing & Splitting */}
            {mode === "advanced" && (
              <>
                <div>
                  <label style={{ fontSize: "0.875rem", fontWeight: 600, display: "block", marginBottom: "0.5rem" }}>
                    5. Preprocessing Pipeline Configuration
                  </label>
                  <PreprocessingConfigView
                    config={preprocessingConfig}
                    onChange={setPreprocessingConfig}
                  />
                </div>

                <div>
                  <label style={{ fontSize: "0.875rem", fontWeight: 600, display: "block", marginBottom: "0.5rem" }}>
                    6. Data Splitting & Validation Strategy
                  </label>
                  <SplitValidationConfigView
                    taskType={taskType}
                    splitConfig={splitConfig}
                    onSplitChange={setSplitConfig}
                    cvConfig={cvConfig}
                    onCVChange={setCVConfig}
                  />
                </div>
              </>
            )}

            {/* Model Selection */}
            <ModelSelector
              taskType={taskType}
              availableModels={availableModels}
              selectedModelIds={selectedModelIds}
              onSelectedModelIdsChange={setSelectedModelIds}
              modelParameters={modelParameters}
              onModelParametersChange={setModelParameters}
              searchConfig={searchConfig}
              onSearchConfigChange={setSearchConfig}
              isAdvanced={mode === "advanced"}
            />

            {/* Train Action Button */}
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
              {!isConfigValid && !isTraining && (
                <div
                  style={{
                    padding: "0.625rem 0.875rem",
                    borderRadius: "6px",
                    background: "rgba(245, 158, 11, 0.1)",
                    border: "1px solid rgba(245, 158, 11, 0.3)",
                    color: "#f59e0b",
                    fontSize: "0.75rem",
                    display: "flex",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "0.5rem",
                  }}
                >
                  <span style={{ fontWeight: 600 }}>Required to enable Run Experiment:</span>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                    {!hasValidTarget && (
                      <span className="badge badge-warning" style={{ fontSize: "0.6875rem" }}>
                        Select Target Column (Step 2)
                      </span>
                    )}
                    {!hasPredictors && (
                      <span className="badge badge-warning" style={{ fontSize: "0.6875rem" }}>
                        Select at least 1 predictor (Step 3)
                      </span>
                    )}
                    {!hasModels && (
                      <span className="badge badge-warning" style={{ fontSize: "0.6875rem" }}>
                        Select at least 1 algorithm (Step 4)
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  Selected: <strong style={{ color: "var(--text-primary)" }}>{selectedModelIds.length} model(s)</strong> on <strong style={{ color: "var(--text-primary)" }}>{selectedFeatures.length} features</strong>
                </div>

                <button
                  type="button"
                  onClick={handleRunExperiment}
                  disabled={!isConfigValid || isTraining}
                  title={!isConfigValid ? "Complete required selections above to run experiment" : "Start model training"}
                  className="btn btn-primary"
                  style={{
                    padding: "0.6rem 1.5rem",
                    fontSize: "0.875rem",
                    opacity: !isConfigValid || isTraining ? 0.6 : 1,
                    cursor: !isConfigValid || isTraining ? "not-allowed" : "pointer",
                  }}
                >
                  {isTraining ? (
                    <>
                      <span className="spinner" style={{ marginRight: "0.5rem" }} />
                      Fitting & Evaluating Models...
                    </>
                  ) : (
                    "Run Experiment"
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Results Section */}
          {result && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {/* Findings Section */}
              {result.findings && result.findings.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <h4 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>
                    Analytical Insights & Findings ({result.findings.length})
                  </h4>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
                    {result.findings.map((finding) => (
                      <div
                        key={finding.finding_id}
                        style={{
                          padding: "1rem",
                          borderRadius: "8px",
                          background: "var(--bg-surface)",
                          border: "1px solid var(--border-subtle)",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.375rem",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <strong style={{ fontSize: "0.875rem" }}>{finding.title}</strong>
                          <span className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>
                            {finding.category}
                          </span>
                        </div>
                        <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.35 }}>
                          {finding.description}
                        </p>
                        {finding.evidence && (
                          <span style={{ fontSize: "0.75rem", color: "var(--color-primary, #6366f1)", fontWeight: 500 }}>
                            {finding.evidence}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Leaderboard Table */}
              <ModelComparisonLeaderboard
                modelRuns={result.model_runs}
                bestModelRunId={result.best_model_run_id}
                primaryMetric={result.primary_metric}
                selectedRunId={selectedRunId}
                onSelectRunId={setSelectedRunId}
              />

              {/* Deep Diagnostics View */}
              {selectedModelRun && (
                <ModelDiagnosticsView
                  modelRun={selectedModelRun}
                  result={result}
                />
              )}

              {/* Feature Importance View */}
              {selectedModelRun && selectedModelRun.feature_importance.length > 0 && (
                <FeatureImportanceView
                  items={selectedModelRun.feature_importance}
                  modelName={selectedModelRun.model_name}
                />
              )}

              {/* Interactive Prediction Runner */}
              {selectedModelRun && (
                <PredictionRunner
                  result={result}
                  selectedModelRun={selectedModelRun}
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXPERIMENT HISTORY */}
      {activeTab === "history" && (
        <MLExperimentHistory
          experiments={history}
          onSelectExperiment={handleLoadHistoricResult}
          isLoading={isHistoryLoading}
        />
      )}
    </div>
  );
};
