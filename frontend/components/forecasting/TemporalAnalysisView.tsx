"use client";

import React from "react";
import { TemporalAnalysisSummary } from "@/types/forecasting";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";
import { ChartSpec } from "@/types";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Calendar,
  LineChart,
  Repeat,
  TrendingUp,
} from "./icons";

interface TemporalAnalysisViewProps {
  summary: TemporalAnalysisSummary;
  decompositionSpec?: ChartSpec | null;
  acfSpec?: ChartSpec | null;
}

export const TemporalAnalysisView: React.FC<TemporalAnalysisViewProps> = ({
  summary,
  decompositionSpec,
  acfSpec,
}) => {
  const { trend, seasonality, anomalies_detected } = summary;

  return (
    <div className="space-y-6">
      {/* Trend & Seasonality Diagnostic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Trend Card */}
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-indigo-400" /> Linear Trend
            </span>
            <span
              className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${
                trend.direction === "UPWARD"
                  ? "bg-emerald-950 text-emerald-400 border border-emerald-800/60"
                  : trend.direction === "DOWNWARD"
                  ? "bg-rose-950 text-rose-400 border border-rose-800/60"
                  : "bg-slate-800 text-slate-300 border border-slate-700"
              }`}
            >
              {trend.direction === "UPWARD" ? (
                <ArrowUpRight className="w-3.5 h-3.5" />
              ) : trend.direction === "DOWNWARD" ? (
                <ArrowDownRight className="w-3.5 h-3.5" />
              ) : (
                <ArrowRight className="w-3.5 h-3.5" />
              )}
              {trend.direction}
            </span>
          </div>
          <p className="text-sm text-slate-200 leading-snug">{trend.description}</p>
          <div className="grid grid-cols-3 gap-2 pt-1 text-[11px] font-mono text-slate-400 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/50">
            <div>
              <span className="text-slate-500 block text-[10px]">SLOPE</span>
              <span className="font-semibold text-slate-200">{trend.slope.toFixed(4)}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">R²</span>
              <span className="font-semibold text-slate-200">{trend.r_squared.toFixed(3)}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">P-VALUE</span>
              <span className="font-semibold text-slate-200">{trend.p_value.toFixed(4)}</span>
            </div>
          </div>
        </div>

        {/* Seasonality Card */}
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <Repeat className="w-4 h-4 text-indigo-400" /> Seasonality
            </span>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                seasonality.detected
                  ? "bg-indigo-950 text-indigo-300 border border-indigo-800/60"
                  : "bg-slate-800 text-slate-400 border border-slate-700"
              }`}
            >
              {seasonality.detected ? "DETECTED" : "NONE DOMINANT"}
            </span>
          </div>
          <p className="text-sm text-slate-200 leading-snug">{seasonality.description}</p>
          {seasonality.detected && (
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">Seasonal Strength:</span>
                <span className="font-mono text-indigo-300 font-semibold">
                  {(seasonality.seasonal_strength * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, seasonality.seasonal_strength * 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Anomalies Card */}
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-indigo-400" /> Residual Deviations
            </span>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                anomalies_detected > 0
                  ? "bg-amber-950 text-amber-300 border border-amber-800/60"
                  : "bg-emerald-950 text-emerald-400 border border-emerald-800/60"
              }`}
            >
              {anomalies_detected} Anomalies
            </span>
          </div>
          <p className="text-sm text-slate-200 leading-snug">
            {anomalies_detected > 0
              ? `Detected ${anomalies_detected} historical timestamps with unexpected deviations (> 3σ from decomposition trajectory).`
              : "No extreme residual outliers detected across historical baseline decomposition."}
          </p>
          <p className="text-[11px] text-slate-500">
            Helps isolate sudden temporary demand spikes or holiday shifts.
          </p>
        </div>
      </div>

      {/* Seasonal Decomposition Chart */}
      {decompositionSpec && (
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <LineChart className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-slate-100">
              Seasonal & Trend Decomposition (Trend, Seasonality, Residuals)
            </h3>
          </div>
          <div className="h-[320px] w-full">
            <ChartRenderer spec={decompositionSpec} height={320} />
          </div>
        </div>
      )}

      {/* ACF Autocorrelation Chart */}
      {acfSpec && (
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Activity className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-slate-100">
              Autocorrelation Function (ACF) with 95% Bartlett Confidence Bounds
            </h3>
          </div>
          <div className="h-[280px] w-full">
            <ChartRenderer spec={acfSpec} height={280} />
          </div>
        </div>
      )}
    </div>
  );
};
