"use client";

import React, { useState } from "react";
import {
  ForecastFinding,
  ForecastModelRun,
  ForecastResult,
} from "@/types/forecasting";
import { ChartSpec } from "@/types";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  GitCommit,
  BarChart3,
  Search,
  Layers,
} from "./icons";

interface ForecastDiagnosticsViewProps {
  result: ForecastResult;
  selectedModelRun?: ForecastModelRun;
}

export const ForecastDiagnosticsView: React.FC<ForecastDiagnosticsViewProps> = ({
  result,
  selectedModelRun,
}) => {
  const [activeTab, setActiveTab] = useState<
    "residuals" | "backtest" | "comparison" | "findings"
  >("residuals");

  const activeModel = selectedModelRun || result.models[0];
  const residuals = activeModel?.residual_diagnostics;
  const backtest = activeModel?.backtest_result;

  // Visualizations from backend
  const residualChartSpec = result.visualizations?.find(
    (v) => v.title.toLowerCase().includes("residual")
  ) as ChartSpec | undefined;

  const backtestChartSpec = result.visualizations?.find(
    (v) => v.title.toLowerCase().includes("backtest")
  ) as ChartSpec | undefined;

  const comparisonChartSpec = result.visualizations?.find(
    (v) => v.title.toLowerCase().includes("comparison")
  ) as ChartSpec | undefined;

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
      case "HIGH":
        return "bg-rose-500/20 text-rose-300 border-rose-500/30";
      case "MEDIUM":
        return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "LOW":
        return "bg-indigo-500/20 text-indigo-300 border-indigo-500/30";
      default:
        return "bg-slate-700/30 text-slate-300 border-slate-700/50";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-5">
      {/* Header with Diagnostic Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center space-x-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            <span>Diagnostics & Model Audit</span>
          </h3>
          <p className="text-xs text-slate-400">
            Statistical residual health, backtest fold consistency, and deterministic findings
          </p>
        </div>

        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab("residuals")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === "residuals"
                ? "bg-indigo-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Residual Analysis
          </button>
          <button
            onClick={() => setActiveTab("backtest")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === "backtest"
                ? "bg-indigo-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Backtest Folds ({backtest?.folds?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab("comparison")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === "comparison"
                ? "bg-indigo-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Model Comparison
          </button>
          <button
            onClick={() => setActiveTab("findings")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === "findings"
                ? "bg-indigo-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Findings ({result.findings.length})
          </button>
        </div>
      </div>

      {/* Tab: Residual Analysis */}
      {activeTab === "residuals" && (
        <div className="space-y-4">
          {residuals ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">
                    Residual Mean
                  </div>
                  <div className="text-xl font-bold font-mono text-slate-100 mt-1">
                    {residuals.mean.toFixed(4)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Target: ~0 (Unbiased)
                  </div>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">
                    Residual Std Dev
                  </div>
                  <div className="text-xl font-bold font-mono text-slate-100 mt-1">
                    {residuals.std.toFixed(4)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Noise scale
                  </div>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">
                    Autocorrelation (Ljung-Box)
                  </div>
                  <div
                    className={`text-sm font-bold font-mono mt-1 ${
                      residuals.autocorrelation_detected
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {residuals.autocorrelation_detected
                      ? "Detected (p < 0.05)"
                      : "Clean White Noise"}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    p = {residuals.ljung_box_pvalue?.toFixed(4) ?? "N/A"}
                  </div>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">
                    Normality Test (D'Agostino)
                  </div>
                  <div className="text-sm font-bold font-mono text-slate-100 mt-1">
                    {residuals.normality_pvalue !== undefined &&
                    residuals.normality_pvalue < 0.05
                      ? "Non-Normal"
                      : "Consistent w/ Normal"}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    p = {residuals.normality_pvalue?.toFixed(4) ?? "N/A"}
                  </div>
                </div>
              </div>

              {residualChartSpec && (
                <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800/80 min-h-[320px]">
                  <ChartRenderer spec={residualChartSpec} height={300} />
                </div>
              )}
            </>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm">
              No residual diagnostics available for this model run.
            </div>
          )}
        </div>
      )}

      {/* Tab: Backtest Folds */}
      {activeTab === "backtest" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>
              Rolling-Origin Walk-Forward Backtesting (
              <span className="font-semibold text-slate-200">
                {backtest?.folds?.length || 0} folds
              </span>
              )
            </span>
            <span className="font-mono text-slate-300">
              Mean MAE: {backtest?.mean_metrics?.mae?.toFixed(3)} • Mean RMSE:{" "}
              {backtest?.mean_metrics?.rmse?.toFixed(3)}
            </span>
          </div>

          {backtestChartSpec && (
            <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800/80 min-h-[320px]">
              <ChartRenderer spec={backtestChartSpec} height={300} />
            </div>
          )}

          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/40">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 uppercase tracking-wider">
                  <th className="py-2.5 px-4">Fold #</th>
                  <th className="py-2.5 px-4">Train Cutoff</th>
                  <th className="py-2.5 px-4">Test Horizon Window</th>
                  <th className="py-2.5 px-3 text-right">Fold MAE</th>
                  <th className="py-2.5 px-3 text-right">Fold RMSE</th>
                  <th className="py-2.5 px-3 text-right">Fold sMAPE</th>
                  <th className="py-2.5 px-3 text-right">Fold WAPE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {backtest?.folds?.map((fold) => (
                  <tr key={fold.fold_index} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 font-bold text-slate-300">
                      Fold {fold.fold_index + 1}
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">
                      {fold.train_end}
                    </td>
                    <td className="py-2.5 px-4 text-slate-300 font-sans">
                      {fold.test_start} → {fold.test_end}
                    </td>
                    <td className="py-2.5 px-3 text-right text-indigo-400 font-bold">
                      {fold.metrics.mae?.toFixed(3)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {fold.metrics.rmse?.toFixed(3)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {fold.metrics.smape?.toFixed(2)}%
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {fold.metrics.wape?.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Model Comparison Chart */}
      {activeTab === "comparison" && (
        <div className="space-y-4">
          {comparisonChartSpec ? (
            <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800/80 min-h-[350px]">
              <ChartRenderer spec={comparisonChartSpec} height={340} />
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm">
              No comparison visualization available.
            </div>
          )}
        </div>
      )}

      {/* Tab: Findings */}
      {activeTab === "findings" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.findings.map((f) => (
            <div
              key={f.finding_id}
              className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {f.category}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(
                    f.severity
                  )}`}
                >
                  {f.severity}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-slate-200">{f.title}</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                {f.description}
              </p>
              {f.methodology && (
                <div className="text-[11px] text-slate-500 border-t border-slate-800/60 pt-2 mt-2">
                  <span className="font-semibold text-slate-400">Method:</span>{" "}
                  {f.methodology}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
