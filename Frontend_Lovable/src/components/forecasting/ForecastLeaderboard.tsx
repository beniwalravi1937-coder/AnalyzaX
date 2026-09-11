"use client";

import React from "react";
import {
  ForecastModelRun,
  ForecastMetrics,
} from "@/types/forecasting";
import {
  Trophy,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ChevronRight,
  TrendingUp,
} from "./icons";

interface ForecastLeaderboardProps {
  models: ForecastModelRun[];
  bestModelId: string;
  selectedModelId: string;
  primaryMetric: string;
  onSelectModel: (modelId: string) => void;
}

export const ForecastLeaderboard: React.FC<ForecastLeaderboardProps> = ({
  models,
  bestModelId,
  selectedModelId,
  primaryMetric,
  onSelectModel,
}) => {
  if (!models || models.length === 0) {
    return null;
  }

  // Find baseline model (naive or seasonal_naive)
  const baselineModel = models.find(
    (m) => m.model_id === "naive" || m.model_id === "seasonal_naive"
  );
  const baselineScore = baselineModel
    ? (baselineModel.backtest_result.mean_metrics as any)[primaryMetric.toLowerCase()]
    : null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-100">
              Model Leaderboard
            </h3>
            <p className="text-xs text-slate-400">
              Ranked by primary backtest metric:{" "}
              <span className="font-semibold text-indigo-400 uppercase">
                {primaryMetric}
              </span>{" "}
              (lower is better)
            </p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-3 px-4">Rank & Model</th>
              <th className="py-3 px-3 text-right">
                {primaryMetric.toUpperCase()} (Mean)
              </th>
              <th className="py-3 px-3 text-right">MAE</th>
              <th className="py-3 px-3 text-right">RMSE</th>
              <th className="py-3 px-3 text-right">sMAPE (%)</th>
              <th className="py-3 px-3 text-right">WAPE (%)</th>
              <th className="py-3 px-3 text-right">MASE</th>
              <th className="py-3 px-3 text-right">vs Baseline</th>
              <th className="py-3 px-3 text-right">Duration</th>
              <th className="py-3 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
            {models.map((run, idx) => {
              const isBest = run.model_id === bestModelId;
              const isSelected = run.model_id === selectedModelId;
              const metrics = run.backtest_result.mean_metrics;
              const score = (metrics as any)[primaryMetric.toLowerCase()] ?? 0;

              let baselineDelta: number | null = null;
              if (
                baselineScore !== null &&
                baselineScore !== undefined &&
                baselineScore > 0 &&
                score !== undefined
              ) {
                baselineDelta = ((score - baselineScore) / baselineScore) * 100;
              }

              return (
                <tr
                  key={run.run_id}
                  onClick={() => onSelectModel(run.model_id)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-indigo-950/40 border-l-2 border-l-indigo-500"
                      : "hover:bg-slate-800/40"
                  }`}
                >
                  <td className="py-3.5 px-4 font-sans flex items-center space-x-3">
                    <span className="text-slate-500 w-4 font-bold">{idx + 1}</span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-slate-200">
                          {run.model_name}
                        </span>
                        {isBest && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            <Sparkles className="w-2.5 h-2.5 mr-1" />
                            BEST
                          </span>
                        )}
                        {isSelected && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-indigo-500/20 text-indigo-300">
                            Active
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-500">
                        {run.model_id}
                      </span>
                    </div>
                  </td>

                  <td className="py-3.5 px-3 text-right font-bold text-slate-100">
                    {score.toFixed(3)}
                  </td>

                  <td className="py-3.5 px-3 text-right text-slate-300">
                    {metrics.mae?.toFixed(3) ?? "-"}
                  </td>

                  <td className="py-3.5 px-3 text-right text-slate-300">
                    {metrics.rmse?.toFixed(3) ?? "-"}
                  </td>

                  <td className="py-3.5 px-3 text-right text-slate-300">
                    {metrics.smape !== undefined ? `${metrics.smape.toFixed(2)}%` : "-"}
                  </td>

                  <td className="py-3.5 px-3 text-right text-slate-300">
                    {metrics.wape !== undefined ? `${metrics.wape.toFixed(2)}%` : "-"}
                  </td>

                  <td className="py-3.5 px-3 text-right text-slate-300">
                    {metrics.mase !== undefined && metrics.mase !== null
                      ? metrics.mase.toFixed(3)
                      : "-"}
                  </td>

                  <td className="py-3.5 px-3 text-right">
                    {baselineDelta !== null ? (
                      <span
                        className={`inline-flex items-center ${
                          baselineDelta < 0
                            ? "text-emerald-400"
                            : baselineDelta > 0
                            ? "text-rose-400"
                            : "text-slate-400"
                        }`}
                      >
                        {baselineDelta < 0 ? "▼" : baselineDelta > 0 ? "▲" : ""}
                        {Math.abs(baselineDelta).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-slate-600">Baseline</span>
                    )}
                  </td>

                  <td className="py-3.5 px-3 text-right text-slate-400 font-sans">
                    <span className="inline-flex items-center text-[11px]">
                      <Clock className="w-3 h-3 mr-1 text-slate-500" />
                      {(run.training_duration_ms / 1000).toFixed(2)}s
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectModel(run.model_id);
                      }}
                      className={`p-1.5 rounded-lg text-xs transition-colors ${
                        isSelected
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-800 text-slate-400 hover:text-slate-200"
                      }`}
                      title="Inspect Model"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
