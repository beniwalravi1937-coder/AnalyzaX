"use client";

import React, { useState } from "react";
import {
  ForecastModelRun,
  ForecastResult,
  FuturePredictResult,
} from "@/types/forecasting";
import { forecastingApi } from "@/services/forecastingApi";
import {
  Sparkles,
  Play,
  Calendar,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Download,
  Loader2,
} from "./icons";

interface ForecastFutureInferenceProps {
  result: ForecastResult;
  selectedModelRun?: ForecastModelRun;
}

export const ForecastFutureInference: React.FC<ForecastFutureInferenceProps> = ({
  result,
  selectedModelRun,
}) => {
  const [periods, setPeriods] = useState<number>(result.forecast_horizon || 14);
  const [confidenceLevel, setConfidenceLevel] = useState<number>(
    result.confidence_level || 0.95
  );
  const [selectedRunId, setSelectedRunId] = useState<string>(
    selectedModelRun?.run_id || result.models[0]?.run_id || ""
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [predictionResult, setPredictionResult] =
    useState<FuturePredictResult | null>(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await forecastingApi.predictFuture(result.experiment_id, {
        run_id: selectedRunId || undefined,
        periods,
        confidence_level: confidenceLevel,
      });
      setPredictionResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to generate future forecast");
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = () => {
    if (!predictionResult || !predictionResult.forecast_points.length) return;
    const headers = [
      "horizon_step",
      "timestamp",
      "point_forecast",
      "lower_bound",
      "upper_bound",
    ];
    const rows = predictionResult.forecast_points.map((p) => [
      p.horizon_step,
      p.timestamp,
      p.value,
      p.lower_bound ?? "",
      p.upper_bound ?? "",
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `future_forecast_${predictionResult.model_id}_${periods}p.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-100">
              Future Horizon Inference
            </h3>
            <p className="text-xs text-slate-400">
              Generate out-of-sample forward projections using the refitted model artifact
            </p>
          </div>
        </div>
      </div>

      {/* Control Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-950/60 p-4 rounded-lg border border-slate-800">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Model Engine
          </label>
          <select
            value={selectedRunId}
            onChange={(e) => setSelectedRunId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
          >
            {result.models.map((m) => (
              <option key={m.run_id} value={m.run_id}>
                {m.model_name}{" "}
                {m.model_id === result.best_model_id ? "(Best)" : ""}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Projection Periods
          </label>
          <input
            type="number"
            min={1}
            max={365}
            value={periods}
            onChange={(e) => setPeriods(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Prediction Interval
          </label>
          <select
            value={confidenceLevel}
            onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value={0.9}>90% Confidence</option>
            <option value={0.95}>95% Confidence (Standard)</option>
            <option value={0.99}>99% Confidence</option>
          </select>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-400 flex items-center space-x-1.5">
          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
          <span>
            Frequency: <span className="text-slate-200 font-mono">{result.frequency}</span>
          </span>
        </div>

        <button
          onClick={handlePredict}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 transition-colors disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          <span>{loading ? "Generating..." : "Generate Future Forecast"}</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-300 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Prediction Output */}
      {predictionResult && (
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-sm font-semibold text-slate-200">
                Inference Complete: {predictionResult.forecast_points.length} Steps
                Projected
              </span>
            </div>

            <button
              onClick={downloadCSV}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/40 max-h-[320px]">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 text-slate-400 uppercase">
                <tr>
                  <th className="py-2.5 px-4">Step</th>
                  <th className="py-2.5 px-4">Calendar Timestamp</th>
                  <th className="py-2.5 px-4 text-right">Future Forecast</th>
                  <th className="py-2.5 px-4 text-right">
                    Lower ({Math.round(predictionResult.confidence_level * 100)}%)
                  </th>
                  <th className="py-2.5 px-4 text-right">
                    Upper ({Math.round(predictionResult.confidence_level * 100)}%)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {predictionResult.forecast_points.map((pt) => (
                  <tr key={pt.horizon_step} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 text-slate-500">
                      t + {pt.horizon_step}
                    </td>
                    <td className="py-2.5 px-4 font-sans text-slate-200">
                      {pt.timestamp}
                    </td>
                    <td className="py-2.5 px-4 text-right font-bold text-emerald-400">
                      {pt.value.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-400">
                      {pt.lower_bound !== undefined
                        ? pt.lower_bound.toFixed(4)
                        : "-"}
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-400">
                      {pt.upper_bound !== undefined
                        ? pt.upper_bound.toFixed(4)
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
