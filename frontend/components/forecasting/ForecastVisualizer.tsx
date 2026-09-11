"use client";

import React, { useState } from "react";
import {
  ForecastModelRun,
  ForecastPoint,
  ForecastResult,
} from "@/types/forecasting";
import { ChartSpec } from "@/types";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";
import {
  TrendingUp,
  Table,
  LineChart as LineChartIcon,
  ShieldCheck,
  Calendar,
  Layers,
  Sparkles,
} from "./icons";

interface ForecastVisualizerProps {
  result: ForecastResult;
  selectedModelRun?: ForecastModelRun;
}

export const ForecastVisualizer: React.FC<ForecastVisualizerProps> = ({
  result,
  selectedModelRun,
}) => {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");

  const activeModel = selectedModelRun || result.models[0];
  if (!activeModel) {
    return null;
  }

  // Find the primary forecast chart spec from result.visualizations
  const forecastChartSpec = result.visualizations?.find(
    (v) => v.chart_type === "line" && v.title.toLowerCase().includes("forecast")
  ) as ChartSpec | undefined;

  const points = activeModel.future_forecasts || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <TrendingUp className="w-5 h-5" />
            </span>
            <h3 className="text-lg font-semibold text-slate-100">
              Future Projection & Intervals
            </h3>
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
              {activeModel.model_name}
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Target: <span className="text-indigo-300 font-medium">{result.target_column}</span> • Horizon:{" "}
            <span className="text-indigo-300 font-medium">{result.forecast_horizon} periods</span> • Confidence:{" "}
            <span className="text-indigo-300 font-medium">{Math.round(result.confidence_level * 100)}%</span>
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 self-start sm:self-auto">
          <button
            onClick={() => setViewMode("chart")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              viewMode === "chart"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LineChartIcon className="w-3.5 h-3.5" />
            <span>Chart</span>
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              viewMode === "table"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            <span>Forecast Points</span>
          </button>
        </div>
      </div>

      {/* Main View Area */}
      {viewMode === "chart" ? (
        <div className="w-full min-h-[420px] bg-slate-950/60 rounded-lg p-3 border border-slate-800/80">
          {forecastChartSpec ? (
            <ChartRenderer spec={forecastChartSpec} height={400} />
          ) : (
            <div className="h-[400px] flex items-center justify-center text-slate-500 text-sm">
              No forecast visualization spec available.
            </div>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/40">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 uppercase tracking-wider">
                <th className="py-2.5 px-4">Horizon Step</th>
                <th className="py-2.5 px-4">Timestamp</th>
                <th className="py-2.5 px-4 text-right">Point Forecast</th>
                <th className="py-2.5 px-4 text-right">
                  Lower ({Math.round(result.confidence_level * 100)}%)
                </th>
                <th className="py-2.5 px-4 text-right">
                  Upper ({Math.round(result.confidence_level * 100)}%)
                </th>
                <th className="py-2.5 px-4 text-right">Interval Width</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {points.map((pt) => {
                const width =
                  pt.upper_bound !== undefined && pt.lower_bound !== undefined
                    ? pt.upper_bound - pt.lower_bound
                    : null;

                return (
                  <tr key={pt.horizon_step} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 text-slate-500">
                      t + {pt.horizon_step}
                    </td>
                    <td className="py-2.5 px-4 font-sans text-slate-200">
                      {pt.timestamp}
                    </td>
                    <td className="py-2.5 px-4 text-right font-bold text-indigo-400">
                      {pt.value.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-400">
                      {pt.lower_bound !== undefined ? pt.lower_bound.toFixed(4) : "-"}
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-400">
                      {pt.upper_bound !== undefined ? pt.upper_bound.toFixed(4) : "-"}
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-500">
                      {width !== null ? width.toFixed(4) : "-"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Uncertainty & Horizon Semantics Warning */}
      <div className="flex items-start space-x-2 text-xs text-slate-400 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
        <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">
            Temporal Leakage & Uncertainty Guarantee:
          </span>{" "}
          Future projections strictly commence after the training cutoff (
          <span className="font-mono text-slate-300">
            {result.historical_timestamps[result.historical_timestamps.length - 1]}
          </span>
          ). Prediction intervals reflect cumulative temporal uncertainty over the {result.forecast_horizon}-step horizon.
        </div>
      </div>
    </div>
  );
};
