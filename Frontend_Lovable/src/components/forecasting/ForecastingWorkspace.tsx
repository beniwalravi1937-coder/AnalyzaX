"use client";

import React, { useEffect, useState, useRef } from "react";
import { api } from "@/services/api";
import { DatasetResponse, DatasetVersion } from "@/types";
import {
  ForecastExperiment,
  ForecastExperimentRequest,
  ForecastFrequency,
  ForecastModelDefinition,
  ForecastResult,
  TemporalAnalysisSummary,
  TemporalValidationReport,
} from "@/types/forecasting";
import { forecastingApi } from "@/services/forecastingApi";
import { TimeSeriesConfigPanel } from "./TimeSeriesConfigPanel";
import { TemporalQualityPanel } from "./TemporalQualityPanel";
import { TemporalAnalysisView } from "./TemporalAnalysisView";
import { HorizonValidationConfigView } from "./HorizonValidationConfigView";
import { ForecastModelSelector } from "./ForecastModelSelector";
import { ForecastLeaderboard } from "./ForecastLeaderboard";
import { ForecastVisualizer } from "./ForecastVisualizer";
import { ForecastDiagnosticsView } from "./ForecastDiagnosticsView";
import { ForecastFutureInference } from "./ForecastFutureInference";
import { ForecastingHistory } from "./ForecastingHistory";
import {
  LineChart,
  History,
  Sparkles,
  Sliders,
  Play,
  CheckCircle2,
  AlertCircle,
  RotateCw,
  Layers,
  Database,
  Calendar,
} from "./icons";

export const ForecastingWorkspace: React.FC = () => {
  // Datasets & Versions
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("v1");
  const [columns, setColumns] = useState<Array<{ name: string; type: string }>>([]);

  // Workspace Mode & Active Tab
  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");
  const [activeTab, setActiveTab] = useState<"studio" | "history">("studio");

  // Configuration State
  const [timeColumn, setTimeColumn] = useState<string>("");
  const [targetColumn, setTargetColumn] = useState<string>("");
  const [frequency, setFrequency] = useState<ForecastFrequency>("DAILY");
  const [horizon, setHorizon] = useState<number>(14);
  const [validationFolds, setValidationFolds] = useState<number>(3);
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95);
  const [primaryMetric, setPrimaryMetric] = useState<string>("mae");
  const [availableModels, setAvailableModels] = useState<
    ForecastModelDefinition[]
  >([]);
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([
    "naive",
    "holt_winters",
    "arima",
  ]);
  const [modelParameters, setModelParameters] = useState<
    Record<string, Record<string, any>>
  >({});

  // Analysis & Validation Results
  const [validationReport, setValidationReport] =
    useState<TemporalValidationReport | null>(null);
  const [temporalAnalysis, setTemporalAnalysis] =
    useState<TemporalAnalysisSummary | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  // Execution & Job Status
  const [isLaunching, setIsLaunching] = useState<boolean>(false);
  const [activeExperiment, setActiveExperiment] =
    useState<ForecastExperiment | null>(null);
  const [activeResult, setActiveResult] = useState<ForecastResult | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Polling ref
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Initial Load: Datasets & Registered Forecasting Models
  useEffect(() => {
    const init = async () => {
      try {
        const [dsRes, modelsList] = await Promise.all([
          api.listDatasets(),
          forecastingApi.listModels(),
        ]);
        const dsList = dsRes.datasets || [];
        setDatasets(dsList);
        setAvailableModels(modelsList);
        if (dsList.length > 0) {
          setSelectedDatasetId(dsList[0].id);
        }
      } catch (err) {
        console.error("Failed to initialize Forecasting Workspace:", err);
      }
    };
    init();

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  // 2. Load Versions & Columns when selectedDatasetId changes
  useEffect(() => {
    if (!selectedDatasetId) return;

    const loadDatasetMetadata = async () => {
      try {
        const vList = await api.listVersions(selectedDatasetId);
        setVersions(vList);
        const activeV = vList.find((v) => v.status === "READY") || vList[0];
        const vId = activeV ? activeV.version_id : "v1";
        setSelectedVersionId(vId);

        // Fetch columns from profile
        const prof = await api
          .getDatasetProfile(selectedDatasetId)
          .catch(() => null);
        if (prof?.columns) {
          const cols = prof.columns.map((c: any) => ({
            name: c.name,
            type: c.data_type || c.type || "numeric",
          }));
          setColumns(cols);

          // Trigger initial suitability
          triggerSuitability(selectedDatasetId, vId, cols);
        }
      } catch (err) {
        console.error("Failed to load dataset details:", err);
      }
    };
    loadDatasetMetadata();
  }, [selectedDatasetId]);

  // Run automated suitability to recommend time column and target
  const triggerSuitability = async (
    dsId: string,
    vId: string,
    cols?: Array<{ name: string; type: string }>
  ) => {
    try {
      const candidates = await forecastingApi.getTimeCandidates(dsId, vId);
      if (candidates && candidates.length > 0) {
        setTimeColumn(candidates[0].column_name);
      }
      if (cols && cols.length > 0) {
        const timeColName = candidates?.[0]?.column_name;
        const numericCol = cols.find(
          (c) =>
            c.name !== timeColName &&
            ["numeric", "float", "integer", "int", "decimal", "number"].some((t) =>
              c.type.toLowerCase().includes(t)
            )
        );
        if (numericCol) {
          setTargetColumn(numericCol.name);
        }
      }
    } catch (err) {
      console.warn("Automated suitability scan note:", err);
    }
  };

  // 3. Validation & Temporal Analysis triggers
  const handleValidate = async () => {
    if (!selectedDatasetId || !timeColumn || !targetColumn) return;
    setIsValidating(true);
    setErrorMessage(null);
    try {
      const report = await forecastingApi.validateTimeSeries(
        selectedDatasetId,
        selectedVersionId,
        timeColumn,
        targetColumn,
        frequency
      );
      setValidationReport(report);
      if (report.inferred_frequency) {
        setFrequency(report.inferred_frequency);
      }

      // Automatically run temporal analysis if series is valid
      if (report.is_valid) {
        setIsAnalyzing(true);
        const analysis = await forecastingApi.analyzeTimeSeries(
          selectedDatasetId,
          selectedVersionId,
          timeColumn,
          targetColumn,
          report.inferred_frequency
        );
        setTemporalAnalysis(analysis);
        setIsAnalyzing(false);

        // In beginner mode: automatically suggest models based on seasonality
        if (mode === "beginner") {
          if (analysis.seasonality.detected) {
            setSelectedModelIds(["seasonal_naive", "holt_winters", "sarimax"]);
          } else {
            setSelectedModelIds(["naive", "drift", "holt", "arima"]);
          }
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to validate time series");
    } finally {
      setIsValidating(false);
      setIsAnalyzing(false);
    }
  };

  // 4. Launch Experiment
  const handleLaunchExperiment = async () => {
    if (!selectedDatasetId || !timeColumn || !targetColumn) {
      setErrorMessage("Please select time and target columns first.");
      return;
    }
    if (selectedModelIds.length === 0) {
      setErrorMessage("Please select at least one forecasting model.");
      return;
    }

    setIsLaunching(true);
    setErrorMessage(null);
    setActiveResult(null);

    const payload: ForecastExperimentRequest = {
      dataset_id: selectedDatasetId,
      dataset_version_id: selectedVersionId,
      time_column: timeColumn,
      target_column: targetColumn,
      frequency,
      forecast_horizon: horizon,
      validation_folds: validationFolds,
      models: selectedModelIds,
      primary_metric: primaryMetric,
      confidence_level: confidenceLevel,
      model_parameters: modelParameters,
    };

    try {
      const exp = await forecastingApi.createExperiment(payload);
      setActiveExperiment(exp);
      startPolling(exp.experiment_id);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start forecasting experiment");
      setIsLaunching(false);
    }
  };

  // Polling for experiment completion
  const startPolling = (expId: string) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    pollTimerRef.current = setInterval(async () => {
      try {
        const exp = await forecastingApi.getExperiment(expId);
        setActiveExperiment(exp);

        if (exp.status === "COMPLETED") {
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          setIsLaunching(false);
          // Fetch final results
          const res = await forecastingApi.getResults(expId);
          setActiveResult(res);
          setSelectedModelId(res.best_model_id);
        } else if (exp.status === "FAILED" || exp.status === "CANCELLED") {
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          setIsLaunching(false);
          setErrorMessage(
            exp.error_message || `Experiment ended with status ${exp.status}`
          );
        }
      } catch (err) {
        console.error("Error polling experiment:", err);
      }
    }, 1500);
  };

  // Load a historical experiment
  const handleSelectHistoryExperiment = async (expId: string) => {
    try {
      const [exp, res] = await Promise.all([
        forecastingApi.getExperiment(expId),
        forecastingApi.getResults(expId),
      ]);
      setActiveExperiment(exp);
      setActiveResult(res);
      setSelectedModelId(res.best_model_id);
      setTimeColumn(res.time_column);
      setTargetColumn(res.target_column);
      setFrequency(res.frequency);
      setHorizon(res.forecast_horizon);
      setValidationReport(res.validation_report);
      setTemporalAnalysis(res.temporal_analysis);
      setActiveTab("studio");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load past experiment");
    }
  };

  const selectedModelRun = activeResult?.models.find(
    (m) => m.model_id === selectedModelId
  );

  return (
    <div className="space-y-8 pb-16">
      {/* Top Bar: Dataset Version, Mode Toggle, History Switch */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Dataset & Version Pickers */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2 bg-slate-950 px-3 py-2 rounded-lg border border-slate-800">
            <Database className="w-4 h-4 text-indigo-400" />
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-200 focus:outline-none cursor-pointer"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900">
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2 bg-slate-950 px-3 py-2 rounded-lg border border-slate-800">
            <span className="text-[11px] text-slate-400 font-medium">Version:</span>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(e.target.value)}
              className="bg-transparent text-xs font-mono font-semibold text-indigo-300 focus:outline-none cursor-pointer"
            >
              {versions.map((v) => (
                <option
                  key={v.version_id}
                  value={v.version_id}
                  className="bg-slate-900 font-mono"
                >
                  {v.version_id} ({v.row_count.toLocaleString()} rows)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Beginner vs Advanced Mode + Tabs */}
        <div className="flex items-center gap-3 self-end md:self-auto">
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setMode("beginner")}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md font-medium transition-colors ${
                mode === "beginner"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Beginner</span>
            </button>
            <button
              onClick={() => setMode("advanced")}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md font-medium transition-colors ${
                mode === "advanced"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Advanced</span>
            </button>
          </div>

          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab("studio")}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "studio"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <LineChart className="w-3.5 h-3.5" />
              <span>Studio</span>
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "history"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>History</span>
            </button>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-300 flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Tab Content */}
      {activeTab === "studio" ? (
        <div className="space-y-8">
          {/* STEP 1: Temporal Column & Frequency Configuration */}
          <TimeSeriesConfigPanel
            datasetId={selectedDatasetId}
            versionId={selectedVersionId}
            columns={columns}
            timeColumn={timeColumn}
            setTimeColumn={setTimeColumn}
            targetColumn={targetColumn}
            setTargetColumn={setTargetColumn}
            frequency={frequency}
            setFrequency={setFrequency}
            validationReport={validationReport}
            onValidate={handleValidate}
            isValidating={isValidating}
          />

          {/* STEP 2: Temporal Quality & Diagnostics (shown after validation) */}
          {validationReport && (
            <TemporalQualityPanel report={validationReport} />
          )}

          {/* STEP 3: Trend & Seasonality Diagnostics */}
          {temporalAnalysis && (
            <TemporalAnalysisView
              summary={temporalAnalysis}
              decompositionSpec={activeResult?.visualizations?.find((v) => v.title.toLowerCase().includes("decomposition"))}
              acfSpec={activeResult?.visualizations?.find((v) => v.title.toLowerCase().includes("autocorrelation") || v.title.toLowerCase().includes("acf"))}
            />
          )}

          {/* STEP 4: Horizon, Validation & Evaluation Settings */}
          <HorizonValidationConfigView
            horizon={horizon}
            setHorizon={setHorizon}
            windowType="expanding"
            setWindowType={() => {}}
            validationFolds={validationFolds}
            setValidationFolds={setValidationFolds}
            primaryMetric={primaryMetric}
            setPrimaryMetric={setPrimaryMetric}
            confidenceLevel={confidenceLevel}
            setConfidenceLevel={setConfidenceLevel}
            frequencyLabel={frequency}
          />

          {/* STEP 5: Forecasting Model Selection */}
          <ForecastModelSelector
            models={availableModels}
            selectedModels={selectedModelIds}
            setSelectedModels={setSelectedModelIds}
            modelParameters={modelParameters}
            setModelParameters={setModelParameters}
            isAdvanced={mode === "advanced"}
          />

          {/* STEP 6: Launch Experiment Button & Job Monitor */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h4 className="text-base font-semibold text-slate-100">
                  Ready to Train & Forecast
                </h4>
                <p className="text-xs text-slate-400">
                  Evaluating {selectedModelIds.length} estimators via{" "}
                  {validationFolds}-fold walk-forward backtesting with zero temporal leakage.
                </p>
              </div>

              <button
                onClick={handleLaunchExperiment}
                disabled={isLaunching || selectedModelIds.length === 0}
                className="flex items-center space-x-2 px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-950/50 transition-colors disabled:opacity-50"
              >
                {isLaunching ? (
                  <RotateCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                <span>
                  {isLaunching
                    ? "Running Backtest & Forecasts..."
                    : "Launch Forecasting Experiment"}
                </span>
              </button>
            </div>

            {/* Active Job Progress Bar */}
            {isLaunching && activeExperiment && (
              <div className="space-y-2 pt-3 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-indigo-400 flex items-center space-x-1.5">
                    <RotateCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Stage: {activeExperiment.progress_stage || "INITIALIZING"}</span>
                  </span>
                  <span className="font-mono text-slate-400 font-bold">
                    {activeExperiment.progress_percent}%
                  </span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.max(5, activeExperiment.progress_percent)}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* STEP 7: Results Section (Leaderboard, Visualizer, Diagnostics, Inference) */}
          {activeResult && (
            <div className="space-y-8 pt-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-100">
                    Forecasting Results & Evaluation
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    Experiment ID: {activeResult.experiment_id} • Recommended Model:{" "}
                    <span className="text-indigo-400 font-bold">
                      {activeResult.best_model_id}
                    </span>
                  </p>
                </div>
              </div>

              {/* Leaderboard */}
              <ForecastLeaderboard
                models={activeResult.models}
                bestModelId={activeResult.best_model_id}
                selectedModelId={selectedModelId}
                primaryMetric={activeResult.primary_metric}
                onSelectModel={setSelectedModelId}
              />

              {/* Main Visualizer */}
              <ForecastVisualizer
                result={activeResult}
                selectedModelRun={selectedModelRun}
              />

              {/* Diagnostics & Audit */}
              <ForecastDiagnosticsView
                result={activeResult}
                selectedModelRun={selectedModelRun}
              />

              {/* Live Future Inference */}
              <ForecastFutureInference
                result={activeResult}
                selectedModelRun={selectedModelRun}
              />
            </div>
          )}
        </div>
      ) : (
        /* History Tab */
        <ForecastingHistory
          datasetId={selectedDatasetId}
          onSelectExperiment={handleSelectHistoryExperiment}
          activeExperimentId={activeExperiment?.experiment_id}
        />
      )}
    </div>
  );
};
