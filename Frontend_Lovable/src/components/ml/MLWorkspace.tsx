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
import { mlApi } from "@/services/mlApi";
import { MLSuitabilityPanel } from "./MLSuitabilityPanel";
import { TaskTargetSelector } from "./TaskTargetSelector";
import { FeatureSelector } from "./FeatureSelector";
import { PreprocessingConfigView } from "./PreprocessingConfigView";
import { SplitValidationConfigView } from "./SplitValidationConfigView";
import { ModelSelector } from "./ModelSelector";
import { ModelComparisonLeaderboard } from "./ModelComparisonLeaderboard";
import { ModelDiagnosticsView } from "./ModelDiagnosticsView";
import { FeatureImportanceView } from "./FeatureImportanceView";
import { PredictionRunner } from "./PredictionRunner";
import { MLExperimentHistory } from "./MLExperimentHistory";

export const MLWorkspace: React.FC = () => {
  // Datasets & Versions
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("v1");
  const [columns, setColumns] = useState<string[]>([]);

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

  // 1. Initial Load: Datasets & Registered Models
  useEffect(() => {
    const init = async () => {
      try {
        const [dsRes, modelsList] = await Promise.all([
          api.listDatasets(),
          mlApi.getModels(),
        ]);
        const dsList = dsRes.datasets || [];
        setDatasets(dsList);
        setAvailableModels(modelsList);
        if (dsList.length > 0) {
          setSelectedDatasetId(dsList[0].id);
        }
      } catch (err) {
        console.error("Failed to initialize ML workspace:", err);
      }
    };
    init();
  }, []);

  // 2. Load Versions, Schema & Trigger Suitability Scan
  useEffect(() => {
    if (!selectedDatasetId) return;

    const loadDatasetDetails = async () => {
      try {
        const vList = await api.listVersions(selectedDatasetId);
        setVersions(vList);
        const activeV = vList.find((v) => v.status === "READY") || vList[0];
        const vId = activeV ? activeV.version_id : "v1";
        setSelectedVersionId(vId);

        // Fetch columns from profile
        const prof = await api.getDatasetProfile(selectedDatasetId).catch(() => null);
        if (prof?.columns) {
          const colNames = prof.columns.map((c: any) => c.name);
          setColumns(colNames);

          // Run automated suitability
          runSuitabilityCheck(selectedDatasetId, vId, undefined, undefined, colNames);
        }

        // Load experiment history
        loadHistory(selectedDatasetId, vId);
      } catch (err) {
        console.error("Failed to load dataset metadata:", err);
      }
    };
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
      if (selectedFeatures.length === 0 && rep.recommended_features) {
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

  // 6. Execute Experiment
  const handleRunExperiment = async () => {
    setErrorMsg(null);

    if (taskType !== "clustering" && !targetColumn) {
      setErrorMsg("Please select a target column to predict.");
      return;
    }
    if (selectedFeatures.length === 0) {
      setErrorMsg("Please select at least one feature column.");
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
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Dataset</span>
            <select
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
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Dataset Version</span>
            <select
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
                runSuitabilityCheck(undefined, undefined, undefined, t);
              }}
              targetColumn={targetColumn}
              onTargetColumnChange={(tgt) => {
                setTargetColumn(tgt);
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Selected: <strong>{selectedModelIds.length} model(s)</strong> on <strong>{selectedFeatures.length} features</strong>
              </div>

              <button
                type="button"
                onClick={handleRunExperiment}
                disabled={isTraining || selectedModelIds.length === 0}
                className="btn btn-primary"
                style={{ padding: "0.6rem 1.5rem", fontSize: "0.875rem" }}
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
