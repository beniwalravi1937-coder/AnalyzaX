"use client";

import React, { useEffect, useState } from "react";
import { ForecastExperiment, ForecastJobStatus } from "@/types/forecasting";
import { forecastingApi } from "@/services/forecastingApi";
import {
  History,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCw,
  ArrowRight,
  Sparkles,
} from "./icons";

interface ForecastingHistoryProps {
  datasetId: string;
  onSelectExperiment: (experimentId: string) => void;
  activeExperimentId?: string;
}

export const ForecastingHistory: React.FC<ForecastingHistoryProps> = ({
  datasetId,
  onSelectExperiment,
  activeExperimentId,
}) => {
  const [experiments, setExperiments] = useState<ForecastExperiment[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchHistory = async () => {
    if (!datasetId) return;
    setLoading(true);
    try {
      const list = await forecastingApi.listExperiments(datasetId);
      setExperiments(list);
    } catch (err) {
      console.error("Failed to fetch forecasting history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [datasetId]);

  const getStatusBadge = (status: ForecastJobStatus) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-2.5 h-2.5 mr-1" />
            COMPLETED
          </span>
        );
      case "RUNNING":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse">
            <RotateCw className="w-2.5 h-2.5 mr-1 animate-spin" />
            RUNNING
          </span>
        );
      case "FAILED":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
            <XCircle className="w-2.5 h-2.5 mr-1" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-slate-700/40 text-slate-300">
            {status}
          </span>
        );
    }
  };

  if (!experiments.length && !loading) {
    return null;
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-100">
              Experiment History
            </h3>
            <p className="text-xs text-slate-400">
              Past forecasting runs preserved with immutable version provenance
            </p>
          </div>
        </div>

        <button
          onClick={fetchHistory}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
          title="Refresh History"
        >
          <RotateCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/40">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold">
              <th className="py-2.5 px-4">Experiment ID</th>
              <th className="py-2.5 px-3">Target</th>
              <th className="py-2.5 px-3">Time Column</th>
              <th className="py-2.5 px-3">Frequency</th>
              <th className="py-2.5 px-3">Horizon</th>
              <th className="py-2.5 px-3">Models</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Created</th>
              <th className="py-2.5 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {experiments.map((exp) => {
              const isActive = exp.experiment_id === activeExperimentId;

              return (
                <tr
                  key={exp.experiment_id}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    isActive ? "bg-indigo-950/30 border-l-2 border-l-indigo-500" : ""
                  }`}
                >
                  <td className="py-3 px-4 font-bold text-slate-200">
                    {exp.experiment_id.slice(0, 12)}...
                  </td>
                  <td className="py-3 px-3 font-sans font-semibold text-indigo-300">
                    {exp.target_column}
                  </td>
                  <td className="py-3 px-3 font-sans text-slate-300">
                    {exp.time_column}
                  </td>
                  <td className="py-3 px-3 text-slate-400">{exp.frequency}</td>
                  <td className="py-3 px-3 text-slate-400">
                    {exp.forecast_horizon}p
                  </td>
                  <td className="py-3 px-3 text-slate-400">
                    {exp.models.length}
                  </td>
                  <td className="py-3 px-3 font-sans">
                    {getStatusBadge(exp.status)}
                  </td>
                  <td className="py-3 px-3 text-slate-500 font-sans">
                    {new Date(exp.created_at).toLocaleDateString()}{" "}
                    {new Date(exp.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="py-3 px-4 text-center font-sans">
                    <button
                      onClick={() => onSelectExperiment(exp.experiment_id)}
                      disabled={exp.status !== "COMPLETED"}
                      className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                        isActive
                          ? "bg-indigo-600 text-white"
                          : exp.status === "COMPLETED"
                          ? "bg-slate-800 hover:bg-slate-700 text-slate-200"
                          : "bg-slate-800/40 text-slate-600 cursor-not-allowed"
                      }`}
                    >
                      <span>{isActive ? "Active" : "Load"}</span>
                      <ArrowRight className="w-3 h-3" />
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
