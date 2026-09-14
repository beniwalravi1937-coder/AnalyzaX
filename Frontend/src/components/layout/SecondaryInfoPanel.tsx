import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { History, Info, Database, Lightbulb, ChevronDown, ChevronUp, Cpu, Clock, Layers, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { HistoryPanel, HistoryEntry } from "@/components/ui/HistoryPanel";

export interface SecondaryInfoRecommendation {
  id: string;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  impact?: "high" | "medium" | "low";
}

export interface SecondaryInfoMetadata {
  datasetName?: string;
  versionName?: string;
  rowCount?: number;
  columnCount?: number;
  storageSize?: string;
  lineageHash?: string;
  engine?: string;
  executionTimeMs?: number;
  customFields?: Record<string, string | number>;
}

export interface SecondaryInfoPanelProps {
  historyEntries?: HistoryEntry[];
  onSelectHistoryEntry?: (entry: HistoryEntry) => void;
  onRerunHistoryEntry?: (entry: HistoryEntry) => void;
  metadata?: SecondaryInfoMetadata;
  detailsContent?: React.ReactNode;
  recommendations?: SecondaryInfoRecommendation[];
  defaultTab?: "history" | "details" | "metadata" | "recommendations";
  defaultExpanded?: boolean;
  className?: string;
}

export function SecondaryInfoPanel({
  historyEntries = [],
  onSelectHistoryEntry,
  onRerunHistoryEntry,
  metadata,
  detailsContent,
  recommendations = [],
  defaultTab = "metadata",
  defaultExpanded = false,
  className,
}: SecondaryInfoPanelProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [activeTab, setActiveTab] = useState<"history" | "details" | "metadata" | "recommendations">(
    defaultTab
  );

  const tabs = [
    { id: "metadata", label: "Metadata", icon: Database, count: undefined },
    { id: "details", label: "Details", icon: Info, count: undefined },
    { id: "recommendations", label: "Recommendations", icon: Lightbulb, count: recommendations.length || undefined },
    { id: "history", label: "History", icon: History, count: historyEntries.length || undefined },
  ] as const;

  return (
    <section
      aria-label="Secondary Analytical Context"
      className={cn(
        "mt-8 rounded-xl border border-white/10 bg-slate-900/40 backdrop-blur-sm overflow-hidden shadow-lg transition-all",
        className
      )}
    >
      {/* Header bar / Tabs */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-white/[0.06] flex-wrap gap-2">
        <div className="flex items-center gap-1 sm:gap-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mr-2 hidden sm:inline">
            Workspace Context:
          </span>

          <div className="flex items-center gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = isExpanded && activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => {
                    if (!isExpanded) {
                      setIsExpanded(true);
                      setActiveTab(tab.id);
                    } else if (activeTab === tab.id) {
                      setIsExpanded(false);
                    } else {
                      setActiveTab(tab.id);
                    }
                  }}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors select-none",
                    isActive
                      ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent"
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.count !== undefined && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-white/10 text-slate-300 font-mono">
                      {tab.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {metadata?.engine && (
            <div className="hidden md:flex items-center gap-1.5 text-[11px] font-mono text-slate-400 bg-slate-950/60 px-2.5 py-1 rounded border border-white/5">
              <Cpu className="w-3 h-3 text-emerald-400" />
              <span>{metadata.engine}</span>
            </div>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-8 px-2 text-xs text-slate-400 hover:text-white hover:bg-white/5 gap-1"
          >
            <span>{isExpanded ? "Hide" : "Expand"}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </Button>
        </div>
      </div>

      {/* Expanded Content Area */}
      {isExpanded && (
        <div className="p-4 sm:p-5 bg-slate-950/40 text-xs text-slate-300 animate-fadeIn">
          {/* 1. METADATA TAB */}
          {activeTab === "metadata" && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Dataset</span>
                <span className="font-semibold text-slate-100 truncate block">
                  {metadata?.datasetName || "Active Dataset"}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Lineage Version</span>
                <span className="font-mono font-semibold text-indigo-300 truncate block">
                  {metadata?.versionName || "V1 (Original)"}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Rows</span>
                <span className="font-mono font-semibold text-emerald-400 block">
                  {metadata?.rowCount !== undefined ? metadata.rowCount.toLocaleString() : "—"}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Columns</span>
                <span className="font-mono font-semibold text-cyan-400 block">
                  {metadata?.columnCount !== undefined ? metadata.columnCount : "—"}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Engine / Runtime</span>
                <span className="font-mono font-medium text-slate-200 truncate block">
                  {metadata?.engine || "DuckDB + SciPy"}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Governance</span>
                <span className="font-medium text-emerald-400 flex items-center gap-1 truncate block">
                  Deterministic
                </span>
              </div>

              {metadata?.customFields &&
                Object.entries(metadata.customFields).map(([k, v]) => (
                  <div key={k} className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">{k}</span>
                    <span className="font-mono text-slate-200 truncate block">{v}</span>
                  </div>
                ))}
            </div>
          )}

          {/* 2. DETAILS TAB */}
          {activeTab === "details" && (
            <div className="space-y-3">
              {detailsContent ? (
                detailsContent
              ) : (
                <div className="p-4 rounded-lg bg-slate-900/60 border border-white/5 space-y-2">
                  <h4 className="text-xs font-semibold text-slate-200">Execution Methodology & Runtime</h4>
                  <p className="text-slate-400 leading-relaxed text-xs">
                    All analytics are deterministically computed on versioned columnar stores using isolated workers.
                    Data transformations create immutable DAG snapshots to ensure complete auditability.
                  </p>
                  <div className="flex items-center gap-4 pt-2 text-[11px] text-slate-400 font-mono">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-indigo-400" />
                      Execution Latency: {metadata?.executionTimeMs ? `${metadata.executionTimeMs}ms` : "< 150ms"}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Layers className="w-3 h-3 text-emerald-400" />
                      Isolation: Read-Only Replica
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 3. RECOMMENDATIONS TAB */}
          {activeTab === "recommendations" && (
            <div className="space-y-2">
              {recommendations.length === 0 ? (
                <div className="p-4 text-center text-slate-400">
                  <Lightbulb className="w-6 h-6 mx-auto mb-1 text-slate-500 opacity-60" />
                  <span>No immediate recommendations. Your dataset and parameters are aligned.</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {recommendations.map((rec) => (
                    <div
                      key={rec.id}
                      className="p-3.5 rounded-lg bg-slate-900/60 border border-white/5 flex items-start justify-between gap-3 hover:border-white/10 transition-colors"
                    >
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          <h5 className="font-semibold text-slate-200 text-xs">{rec.title}</h5>
                          {rec.impact && (
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-[9px] uppercase tracking-wider py-0 px-1.5",
                                rec.impact === "high"
                                  ? "text-rose-400 border-rose-500/20"
                                  : rec.impact === "medium"
                                  ? "text-amber-400 border-amber-500/20"
                                  : "text-slate-400 border-white/10"
                              )}
                            >
                              {rec.impact} impact
                            </Badge>
                          )}
                        </div>
                        <p className="text-slate-400 text-[11px] leading-relaxed">{rec.description}</p>
                      </div>

                      {rec.actionLabel && rec.onAction && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={rec.onAction}
                          className="h-7 px-2 text-[11px] border-white/10 bg-slate-800 hover:bg-slate-700 text-slate-200 shrink-0 gap-1"
                        >
                          <span>{rec.actionLabel}</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 4. HISTORY TAB */}
          {activeTab === "history" && (
            <div className="max-h-72 overflow-y-auto">
              <HistoryPanel
                entries={historyEntries}
                onSelectEntry={onSelectHistoryEntry}
                onRerunEntry={onRerunHistoryEntry}
                emptyMessage="No executions recorded for this workspace yet."
              />
            </div>
          )}
        </div>
      )}
    </section>
  );
}
