import React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, Loader2, Clock, Sparkles } from "lucide-react";

export type AnalysisExecutionStatus = "idle" | "running" | "loading" | "success" | "completed" | "error" | "stale";

export interface AnalysisStatusProps {
  status: AnalysisExecutionStatus;
  durationMs?: number;
  rowCount?: number;
  cached?: boolean;
  message?: string;
  className?: string;
  size?: "sm" | "md";
}

export function AnalysisStatus({
  status,
  durationMs,
  rowCount,
  cached = false,
  message,
  className,
  size = "md",
}: AnalysisStatusProps) {
  const isRunning = status === "running" || status === "loading";
  const isSuccess = status === "success" || status === "completed";
  const isError = status === "error";

  const formatDuration = (ms?: number) => {
    if (ms === undefined || ms === null) return null;
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all select-none",
        isRunning && "bg-indigo-500/10 border-indigo-500/30 text-indigo-300 animate-pulse",
        isSuccess && "bg-emerald-500/10 border-emerald-500/20 text-emerald-300",
        isError && "bg-rose-500/10 border-rose-500/25 text-rose-300",
        status === "idle" && "bg-slate-800/60 border-white/10 text-slate-400",
        status === "stale" && "bg-amber-500/10 border-amber-500/20 text-amber-300",
        size === "sm" && "text-[11px] px-2 py-0.5",
        className
      )}
    >
      {isRunning && <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400 shrink-0" />}
      {isSuccess && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
      {isError && <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />}
      {status === "idle" && <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />}
      {status === "stale" && <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />}

      <span className="font-medium">
        {message ? (
          message
        ) : isRunning ? (
          "Computing..."
        ) : isSuccess ? (
          "Ready"
        ) : isError ? (
          "Failed"
        ) : status === "stale" ? (
          "Cached"
        ) : (
          "Idle"
        )}
      </span>

      {durationMs !== undefined && isSuccess && (
        <span className="text-[10px] text-slate-400 font-mono pl-0.5 border-l border-white/10 ml-0.5">
          {formatDuration(durationMs)}
        </span>
      )}

      {rowCount !== undefined && isSuccess && (
        <span className="text-[10px] text-slate-400 font-mono">
          · {rowCount.toLocaleString()} rows
        </span>
      )}

      {cached && (
        <span className="text-[9px] uppercase tracking-wider text-slate-400 bg-white/5 px-1 rounded ml-0.5">
          Cached
        </span>
      )}
    </div>
  );
}
