import { createFileRoute } from "@tanstack/react-router";
import React, { useEffect, useState } from "react";
import { useWorkspace } from "../context/WorkspaceContext";
import { useDataset } from "../context/DatasetContext";
import {
  Insight,
  InsightSeverity,
  InsightStatus,
  InsightType,
} from "../types/copilot";
import {
  dismissInsight,
  listInsights,
  triggerInsightDiscovery,
} from "../services/copilotApi";
import {
  AlertCircle,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  Clock,
  Filter,
  Lightbulb,
  RefreshCw,
  Sparkles,
  TrendingUp,
  XCircle,
} from "lucide-react";

export const Route = createFileRoute("/insights")({
  head: () => ({
    meta: [
      { title: "Proactive Insight Center — AnalyzaX" },
      {
        name: "description",
        content:
          "Automated multi-engine discovery across data quality, anomalies, distributions, and trends.",
      },
    ],
  }),
  component: InsightsPage,
});

function InsightsPage() {
  const { activeWorkspace, activeProject } = useWorkspace();
  const { activeDataset } = useDataset();

  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [activeInsight, setActiveInsight] = useState<Insight | null>(null);
  const [isDiscovering, setIsDiscovering] = useState<boolean>(false);

  const fetchInsights = async () => {
    if (!activeWorkspace?.workspace_id) return;
    try {
      setLoading(true);
      const data = await listInsights({
        workspace_id: activeWorkspace.workspace_id,
        project_id: activeProject?.project_id,
        dataset_id: activeDataset?.id,
        severity: selectedSeverity !== "ALL" ? (selectedSeverity as InsightSeverity) : undefined,
        insight_type: selectedType !== "ALL" ? (selectedType as InsightType) : undefined,
      });
      setInsights(data);
      if (data.length > 0 && !activeInsight) {
        setActiveInsight(data[0]);
      }
    } catch (err) {
      console.error("Failed to load insights:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [activeWorkspace?.workspace_id, activeProject?.project_id, activeDataset?.id, selectedSeverity, selectedType]);

  const handleDismiss = async (insightId: string) => {
    try {
      await dismissInsight(insightId);
      setInsights((prev) => prev.filter((i) => i.insight_id !== insightId));
      if (activeInsight?.insight_id === insightId) {
        setActiveInsight(null);
      }
    } catch (err) {
      console.error("Failed to dismiss insight:", err);
    }
  };

  const handleRunDiscovery = async () => {
    if (!activeWorkspace?.workspace_id || !activeDataset?.id) return;
    try {
      setIsDiscovering(true);
      const newInsights = await triggerInsightDiscovery({
        workspace_id: activeWorkspace.workspace_id,
        dataset_id: activeDataset.id,
        version_id: (activeDataset as any).version || "v1",
        project_id: activeProject?.project_id,
      });
      setInsights(newInsights);
      if (newInsights.length > 0) setActiveInsight(newInsights[0]);
    } catch (err) {
      console.error("Discovery error:", err);
    } finally {
      setIsDiscovering(false);
    }
  };

  const getSeverityBadge = (severity: InsightSeverity) => {
    switch (severity) {
      case "CRITICAL":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-red-500/20 text-red-400 border border-red-500/30">Critical</span>;
      case "HIGH":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">High</span>;
      case "MEDIUM":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">Medium</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-zinc-500/20 text-zinc-400 border border-zinc-500/30">Low</span>;
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden p-6 space-y-6 text-zinc-100">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2.5">
            <Sparkles className="w-6 h-6 text-purple-400" />
            Proactive Insight Center
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Automated multi-engine discovery across data quality, anomalies, distributions, and trends.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunDiscovery}
            disabled={isDiscovering || !activeDataset}
            className="flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50 transition-all shadow-lg shadow-purple-900/20"
          >
            <RefreshCw className={`w-4 h-4 ${isDiscovering ? "animate-spin" : ""}`} />
            {isDiscovering ? "Scanning Engines..." : "Scan for Signals"}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center gap-1.5 text-zinc-400">
          <Filter className="w-3.5 h-3.5" />
          <span>Severity:</span>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-400">
          <span>Signal Type:</span>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 outline-none"
          >
            <option value="ALL">All Types</option>
            <option value="DATA_QUALITY">Data Quality</option>
            <option value="ANOMALY">Anomaly</option>
            <option value="CORRELATION">Correlation</option>
            <option value="TREND_CHANGE">Trend Change</option>
            <option value="SEGMENT_DIFFERENCE">Segment Difference</option>
            <option value="STATISTICAL_SIGNAL">Statistical Signal</option>
          </select>
        </div>

        <div className="ml-auto text-zinc-400">
          Found <span className="font-semibold text-zinc-200">{insights.length}</span> prioritized signals
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        <div className="lg:col-span-5 flex flex-col space-y-3 overflow-y-auto pr-1">
          {loading ? (
            <div className="flex items-center justify-center p-12 text-zinc-500">
              <RefreshCw className="w-5 h-5 animate-spin mr-2" />
              Loading prioritized insights...
            </div>
          ) : insights.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl border border-zinc-800/80 bg-zinc-900/30">
              <Lightbulb className="w-10 h-10 text-zinc-600 mb-3" />
              <p className="font-medium text-zinc-300">No signals detected</p>
              <p className="text-xs text-zinc-500 mt-1 max-w-xs">
                Run an automated scan or verify that a dataset version with profiling/quality is active.
              </p>
            </div>
          ) : (
            insights.map((ins) => (
              <div
                key={ins.insight_id}
                onClick={() => setActiveInsight(ins)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  activeInsight?.insight_id === ins.insight_id
                    ? "border-purple-500/60 bg-purple-950/20 shadow-md shadow-purple-900/10"
                    : "border-zinc-800/80 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-900/70"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {getSeverityBadge(ins.severity)}
                    <span className="text-xs text-zinc-400 font-mono">
                      Priority: {Math.round(ins.importance_score)}/100
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDismiss(ins.insight_id);
                    }}
                    title="Dismiss"
                    className="text-zinc-500 hover:text-zinc-300"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>

                <h3 className="font-semibold text-sm text-zinc-100 mt-2.5 line-clamp-1">
                  {ins.title}
                </h3>
                <p className="text-xs text-zinc-400 mt-1 line-clamp-2 leading-relaxed">
                  {ins.summary}
                </p>

                {ins.affected_columns.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {ins.affected_columns.slice(0, 3).map((col) => (
                      <span
                        key={col}
                        className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-zinc-800 text-zinc-300 border border-zinc-700/50"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="lg:col-span-7 flex flex-col rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 overflow-y-auto">
          {activeInsight ? (
            <div className="space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    {getSeverityBadge(activeInsight.severity)}
                    <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                      {activeInsight.insight_type}
                    </span>
                    <span className="text-xs text-zinc-500">
                      Dataset: {activeInsight.dataset_id} ({activeInsight.dataset_version_id})
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-zinc-100">{activeInsight.title}</h2>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-zinc-950/50 border border-zinc-800/80">
                <p className="text-sm text-zinc-300 leading-relaxed">{activeInsight.summary}</p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Deterministic Evidence Citations ({activeInsight.evidence.length})
                </h4>
                <div className="space-y-2">
                  {activeInsight.evidence.length === 0 ? (
                    <p className="text-xs text-zinc-500">No isolated metric nodes attached.</p>
                  ) : (
                    activeInsight.evidence.map((ev, idx) => (
                      <div
                        key={ev.evidence_id || idx}
                        className="p-3 rounded-lg bg-zinc-900 border border-zinc-800 text-xs space-y-1.5"
                      >
                        <div className="flex items-center justify-between text-zinc-400">
                          <span className="font-mono text-purple-300">{ev.evidence_type}</span>
                          <span className="text-[10px] text-zinc-500">{ev.created_at?.slice(0, 19)}</span>
                        </div>
                        <p className="text-zinc-200">{ev.description}</p>
                        {ev.metrics && Object.keys(ev.metrics).length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-1 font-mono text-[11px] text-zinc-400">
                            {Object.entries(ev.metrics).map(([k, v]) => (
                              <span key={k} className="bg-zinc-800/80 px-1.5 py-0.5 rounded">
                                {k}: {String(v)}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {activeInsight.recommended_actions.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    Recommended Next Actions
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {activeInsight.recommended_actions.map((act) => (
                      <div
                        key={act.action_id}
                        className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-all flex flex-col justify-between"
                      >
                        <div>
                          <div className="font-semibold text-xs text-zinc-200">{act.title}</div>
                          <p className="text-[11px] text-zinc-400 mt-1">{act.description}</p>
                        </div>
                        <div className="flex items-center justify-between mt-3 pt-2 border-t border-zinc-800/60 text-[10px] text-zinc-500">
                          <span className="font-mono">Tool: {act.tool_id}</span>
                          <span className="text-purple-400 font-semibold flex items-center gap-1">
                            Action <ArrowUpRight className="w-3 h-3" />
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-zinc-500 text-sm">
              Select an insight to inspect underlying evidence and citations.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
