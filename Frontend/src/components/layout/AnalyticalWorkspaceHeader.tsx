import React from "react";
import { cn } from "@/lib/utils";
import { Database, ChevronRight, SlidersHorizontal, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DatasetSelector, DatasetItem } from "@/components/ui/DatasetSelector";
import { VersionSelector, VersionItem } from "@/components/ui/VersionSelector";
import { AnalysisStatus, AnalysisExecutionStatus } from "@/components/ui/AnalysisStatus";
import { useDataset } from "@/context/DatasetContext";

export interface WorkflowStep {
  id: string;
  label: string;
  status?: "completed" | "current" | "pending";
  onClick?: () => void;
}

export interface AnalyticalWorkspaceHeaderProps {
  title: string;
  description: string;
  badgeText?: string;
  primaryAction?: React.ReactNode;
  secondaryActions?: React.ReactNode;
  steps?: WorkflowStep[];
  currentStepId?: string;
  onStepClick?: (stepId: string) => void;
  status?: AnalysisExecutionStatus;
  statusMessage?: string;
  durationMs?: number;
  rowCount?: number;
  mode?: "beginner" | "advanced";
  onToggleMode?: (mode: "beginner" | "advanced") => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  className?: string;
  customDatasetSelector?: React.ReactNode;
}

export function AnalyticalWorkspaceHeader({
  title,
  description,
  badgeText,
  primaryAction,
  secondaryActions,
  steps,
  currentStepId,
  onStepClick,
  status = "idle",
  statusMessage,
  durationMs,
  rowCount,
  mode,
  onToggleMode,
  onRefresh,
  isRefreshing,
  className,
  customDatasetSelector,
}: AnalyticalWorkspaceHeaderProps) {
  const { activeDataset, datasets, selectDataset } = useDataset();

  // Map context datasets to DatasetItem format
  const datasetItems: DatasetItem[] = (datasets || []).map((d) => ({
    id: d.id,
    name: d.name,
    rowCount: (d as any).row_count || (d as any).rowCount || 0,
    columnCount: (d as any).column_count || (d as any).columnCount || 0,
    versionName: (d as any).current_version_name || (d as any).version || "V1",
  }));

  const activeDatasetItem = datasetItems.find((d) => d.id === activeDataset?.id) || datasetItems[0];

  return (
    <header
      className={cn(
        "flex flex-col gap-4 pb-5 border-b border-white/[0.08] mb-6",
        className
      )}
    >
      {/* Top row: Title, Subtitle, Context & Primary Action */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div className="space-y-1.5 min-w-0 max-w-3xl">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-2xl sm:text-[28px] font-bold text-white tracking-tight leading-tight">
              {title}
            </h1>
            {badgeText && (
              <Badge
                variant="outline"
                className="text-[11px] font-semibold tracking-wide bg-indigo-500/10 text-indigo-300 border-indigo-500/25 px-2.5 py-0.5 rounded-full"
              >
                {badgeText}
              </Badge>
            )}
            {status !== "idle" && (
              <AnalysisStatus
                status={status}
                message={statusMessage}
                durationMs={durationMs}
                rowCount={rowCount}
                size="sm"
              />
            )}
          </div>

          <p className="text-sm text-slate-400 leading-relaxed max-w-2xl font-normal">
            {description}
          </p>
        </div>

        {/* Dataset Context & Action Bar */}
        <div className="flex flex-wrap items-center gap-2.5 lg:self-start shrink-0">
          {customDatasetSelector ? (
            customDatasetSelector
          ) : (
            <div className="flex items-center gap-2 bg-slate-900/60 p-1 rounded-lg border border-white/10">
              <span className="text-[11px] font-medium text-slate-400 pl-2 pr-0.5 uppercase tracking-wider hidden sm:inline">
                Dataset:
              </span>
              <DatasetSelector
                datasets={datasetItems}
                activeDatasetId={activeDataset?.id}
                onSelectDataset={(id) => selectDataset(id)}
                size="sm"
              />
            </div>
          )}

          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isRefreshing}
              className="h-9 px-2.5 border-white/10 bg-slate-900/60 hover:bg-slate-850 hover:border-white/20 text-slate-300"
              title="Refresh dataset state"
            >
              <RefreshCw className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin text-indigo-400")} />
            </Button>
          )}

          {mode !== undefined && onToggleMode && (
            <div className="flex items-center bg-slate-900/80 p-0.5 rounded-lg border border-white/10">
              <button
                type="button"
                onClick={() => onToggleMode("beginner")}
                className={cn(
                  "px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors",
                  mode === "beginner"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                Simple
              </button>
              <button
                type="button"
                onClick={() => onToggleMode("advanced")}
                className={cn(
                  "px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors flex items-center gap-1",
                  mode === "advanced"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <SlidersHorizontal className="w-2.5 h-2.5" />
                <span>Advanced</span>
              </button>
            </div>
          )}

          {secondaryActions}
          {primaryAction}
        </div>
      </div>

      {/* Visual Workflow Steps (Progressive Guidance) */}
      {steps && steps.length > 0 && (
        <div className="pt-2 border-t border-white/[0.05]">
          <nav aria-label="Workflow Steps" className="flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
            {steps.map((step, idx) => {
              const isCurrent = currentStepId ? step.id === currentStepId : step.status === "current";
              const isCompleted = step.status === "completed";
              const isClickable = Boolean(step.onClick || onStepClick);

              return (
                <React.Fragment key={step.id}>
                  {idx > 0 && (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0 mx-0.5" />
                  )}

                  <button
                    type="button"
                    disabled={!isClickable}
                    onClick={() => {
                      if (step.onClick) step.onClick();
                      else if (onStepClick) onStepClick(step.id);
                    }}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all shrink-0 select-none",
                      isCurrent &&
                        "bg-indigo-500/15 border border-indigo-500/40 text-indigo-300 font-semibold shadow-sm",
                      isCompleted &&
                        "text-emerald-400 hover:bg-white/5 border border-transparent",
                      !isCurrent &&
                        !isCompleted &&
                        "text-slate-500 hover:text-slate-300 border border-transparent",
                      !isClickable && "cursor-default"
                    )}
                  >
                    <span
                      className={cn(
                        "w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-mono",
                        isCurrent
                          ? "bg-indigo-600 text-white"
                          : isCompleted
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                          : "bg-slate-800 text-slate-500"
                      )}
                    >
                      {idx + 1}
                    </span>
                    <span>{step.label}</span>
                  </button>
                </React.Fragment>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
}
