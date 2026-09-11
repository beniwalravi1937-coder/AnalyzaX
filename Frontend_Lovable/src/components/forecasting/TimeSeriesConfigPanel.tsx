"use client";

import React, { useEffect, useState } from "react";
import {
  ForecastFrequency,
  TemporalValidationReport,
} from "@/types/forecasting";
import { forecastingApi } from "@/services/forecastingApi";
import { Calendar, CheckCircle2, Clock, Play, Sparkles } from "./icons";

interface TimeSeriesConfigPanelProps {
  datasetId: string;
  versionId: string;
  columns: Array<{ name: string; type: string }>;
  timeColumn: string;
  setTimeColumn: (col: string) => void;
  targetColumn: string;
  setTargetColumn: (col: string) => void;
  frequency: ForecastFrequency;
  setFrequency: (freq: ForecastFrequency) => void;
  validationReport: TemporalValidationReport | null;
  onValidate: () => void;
  isValidating: boolean;
}

export const TimeSeriesConfigPanel: React.FC<TimeSeriesConfigPanelProps> = ({
  datasetId,
  versionId,
  columns,
  timeColumn,
  setTimeColumn,
  targetColumn,
  setTargetColumn,
  frequency,
  setFrequency,
  validationReport,
  onValidate,
  isValidating,
}) => {
  const [candidates, setCandidates] = useState<Array<{ column_name: string; confidence: number }>>([]);

  useEffect(() => {
    if (datasetId && versionId) {
      forecastingApi
        .getTimeCandidates(datasetId, versionId)
        .then((res) => {
          setCandidates(res);
          if (!timeColumn && res.length > 0) {
            setTimeColumn(res[0].column_name);
          }
        })
        .catch(() => {});
    }
  }, [datasetId, versionId, timeColumn, setTimeColumn]);

  // Numeric columns for target
  const numericColumns = columns.filter((c) =>
    ["numeric", "float", "integer", "int", "decimal", "number"].some((t) =>
      c.type.toLowerCase().includes(t)
    )
  );

  return (
    <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-semibold text-slate-100">Time Series Configuration</h2>
        </div>
        {validationReport && validationReport.is_valid && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Valid Time Series
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Time Column */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
            <span>Time / Date Column</span>
            {candidates.length > 0 && (
              <span className="text-[10px] text-indigo-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> Auto-detected
              </span>
            )}
          </label>
          <select
            value={timeColumn}
            onChange={(e) => setTimeColumn(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select timestamp column...</option>
            {columns.map((c) => {
              const isCandidate = candidates.some((cand) => cand.column_name === c.name);
              return (
                <option key={c.name} value={c.name}>
                  {c.name} {isCandidate ? "★" : ""} ({c.type})
                </option>
              );
            })}
          </select>
        </div>

        {/* Target Column */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">
            Forecast Target
          </label>
          <select
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select target metric...</option>
            {(numericColumns.length > 0 ? numericColumns : columns).map((c) => (
              <option key={c.name} value={c.name} disabled={c.name === timeColumn}>
                {c.name} ({c.type})
              </option>
            ))}
          </select>
        </div>

        {/* Frequency */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">
            Sampling Frequency
          </label>
          <select
            value={frequency}
            onChange={(e) => setFrequency(e.target.value as ForecastFrequency)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="DAILY">Daily (Calendar Days)</option>
            <option value="BUSINESS_DAY">Business Days (Mon-Fri)</option>
            <option value="WEEKLY">Weekly</option>
            <option value="MONTHLY">Monthly</option>
            <option value="QUARTERLY">Quarterly</option>
            <option value="HOURLY">Hourly</option>
            <option value="YEARLY">Yearly</option>
            <option value="CUSTOM">Custom / Unspecified</option>
          </select>
        </div>
      </div>

      <div className="flex items-center justify-end pt-2">
        <button
          onClick={onValidate}
          disabled={!timeColumn || !targetColumn || isValidating}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition-colors"
        >
          {isValidating ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Validating Time Series...
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5" />
              Validate Temporal Series
            </>
          )}
        </button>
      </div>
    </div>
  );
};
