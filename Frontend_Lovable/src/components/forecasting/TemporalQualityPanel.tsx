"use client";

import React from "react";
import { TemporalValidationReport } from "@/types/forecasting";
import {
  AlertCircle,
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Database,
  Hash,
  Info,
  Layers,
} from "./icons";

interface TemporalQualityPanelProps {
  report: TemporalValidationReport;
}

export const TemporalQualityPanel: React.FC<TemporalQualityPanelProps> = ({ report }) => {
  const regularityColors: Record<string, string> = {
    REGULAR: "text-emerald-400 bg-emerald-950/70 border-emerald-800/60",
    MOSTLY_REGULAR: "text-amber-400 bg-amber-950/70 border-amber-800/60",
    IRREGULAR: "text-rose-400 bg-rose-950/70 border-rose-800/60",
    INSUFFICIENT_DATA: "text-slate-400 bg-slate-900 border-slate-700",
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-slate-100">Temporal Quality & Regularity Audit</h3>
        </div>
        <span
          className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
            regularityColors[report.regularity] || "text-slate-400 bg-slate-800"
          }`}
        >
          {report.regularity.replace("_", " ")}
        </span>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
            <Hash className="w-3.5 h-3.5 text-indigo-400" /> Observations
          </span>
          <p className="text-lg font-bold text-slate-100 mt-1">
            {report.observation_count.toLocaleString()}
          </p>
          <span className="text-[10px] text-slate-500">
            Expected: {report.expected_observation_count.toLocaleString()}
          </span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-indigo-400" /> Historical Span
          </span>
          <p className="text-xs font-semibold text-slate-200 mt-1.5 truncate">
            {report.min_timestamp.split(" ")[0]} ➔ {report.max_timestamp.split(" ")[0]}
          </p>
          <span className="text-[10px] text-slate-500">Inferred: {report.inferred_frequency}</span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" /> Missing Timestamps
          </span>
          <p className={`text-lg font-bold mt-1 ${report.missing_timestamp_count > 0 ? "text-amber-400" : "text-emerald-400"}`}>
            {report.missing_timestamp_count}
          </p>
          <span className="text-[10px] text-slate-500">
            Duplicates: {report.duplicate_timestamp_count}
          </span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-indigo-400" /> Target Mean & Var
          </span>
          <p className="text-lg font-bold text-slate-100 mt-1">
            {report.target_mean.toFixed(2)}
          </p>
          <span className="text-[10px] text-slate-500">Variance: {report.target_variance.toFixed(2)}</span>
        </div>
      </div>

      {/* Issues Feed */}
      {report.issues.length > 0 && (
        <div className="space-y-2 pt-2">
          <h4 className="text-xs font-semibold text-slate-300">Detected Quality & Gap Signals:</h4>
          <div className="space-y-2">
            {report.issues.map((issue) => (
              <div
                key={issue.issue_id}
                className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
                  issue.severity === "CRITICAL"
                    ? "bg-rose-950/40 border-rose-800/60 text-rose-300"
                    : issue.severity === "HIGH"
                    ? "bg-rose-950/20 border-rose-900/40 text-rose-300"
                    : issue.severity === "MEDIUM"
                    ? "bg-amber-950/30 border-amber-800/50 text-amber-300"
                    : "bg-slate-950 border-slate-800 text-slate-300"
                }`}
              >
                {issue.severity === "CRITICAL" || issue.severity === "HIGH" ? (
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                ) : issue.severity === "MEDIUM" ? (
                  <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
                ) : (
                  <Info className="w-4 h-4 shrink-0 text-indigo-400 mt-0.5" />
                )}
                <div className="space-y-1 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-100">{issue.issue_type}</span>
                    <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/40 font-mono">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-slate-300 leading-relaxed">{issue.description}</p>
                  {issue.recommendation && (
                    <p className="text-[11px] text-indigo-300/90 font-medium">
                      Recommendation: {issue.recommendation}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
