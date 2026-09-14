import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Sparkles, ChevronDown, ArrowRight, CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react";
import { Badge } from "./badge";
import { Button } from "./button";

export interface InsightCardProps extends React.HTMLAttributes<HTMLDivElement> {
  category?: string;
  title: string;
  summary: string;
  details?: string;
  severity?: "info" | "success" | "warning" | "danger";
  confidence?: number;
  impact?: string;
  actionLabel?: string;
  onAction?: () => void;
  metadata?: Record<string, string | number>;
}

export function InsightCard({
  category = "Automated Insight",
  title,
  summary,
  details,
  severity = "info",
  confidence,
  impact,
  actionLabel,
  onAction,
  metadata,
  className,
  ...props
}: InsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const severityConfig = {
    info: {
      badge: "border-cyan-500/20 bg-cyan-500/10 text-cyan-400",
      border: "border-cyan-500/20 hover:border-cyan-500/40",
      icon: <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />,
    },
    success: {
      badge: "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
      border: "border-emerald-500/20 hover:border-emerald-500/40",
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />,
    },
    warning: {
      badge: "border-amber-500/20 bg-amber-500/10 text-amber-400",
      border: "border-amber-500/20 hover:border-amber-500/40",
      icon: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />,
    },
    danger: {
      badge: "border-rose-500/20 bg-rose-500/10 text-rose-400",
      border: "border-rose-500/20 hover:border-rose-500/40",
      icon: <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />,
    },
  };

  const current = severityConfig[severity];

  return (
    <div
      className={cn(
        "rounded-xl border bg-slate-900/60 p-4 transition-all duration-200 backdrop-blur-sm",
        current.border,
        className
      )}
      {...props}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className={cn("text-[11px] font-medium", current.badge)}>
            {category}
          </Badge>

          {confidence !== undefined && (
            <span className="text-[11px] font-mono text-slate-400">
              {Math.round(confidence * 100)}% confidence
            </span>
          )}

          {impact && (
            <span className="text-[11px] font-medium text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded-full">
              Impact: {impact}
            </span>
          )}
        </div>

        {current.icon}
      </div>

      {/* Title & Summary */}
      <div className="mt-2.5">
        <h3 className="text-sm font-semibold text-white tracking-tight leading-snug">
          {title}
        </h3>
        <p className="mt-1 text-xs text-slate-300 leading-relaxed">{summary}</p>
      </div>

      {/* Expandable Technical Depth (Progressive Disclosure) */}
      {details && (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
          >
            <span>{isExpanded ? "Hide analytical details" : "Show technical breakdown"}</span>
            <ChevronDown
              className={cn(
                "w-3.5 h-3.5 transition-transform duration-200",
                isExpanded ? "rotate-180" : ""
              )}
            />
          </button>

          {isExpanded && (
            <div className="mt-2 p-3 rounded-lg bg-slate-950/70 border border-white/5 text-xs text-slate-300 space-y-2 animate-in fade-in-50 duration-200">
              <p className="leading-relaxed whitespace-pre-wrap">{details}</p>

              {metadata && Object.keys(metadata).length > 0 && (
                <div className="pt-2 border-t border-white/5 grid grid-cols-2 gap-2 text-[11px] font-mono">
                  {Object.entries(metadata).map(([k, v]) => (
                    <div key={k}>
                      <span className="text-slate-500 uppercase">{k}:</span>{" "}
                      <span className="text-slate-200">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action Footer */}
      {actionLabel && (
        <div className="mt-3.5 pt-3 border-t border-white/5 flex items-center justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={onAction}
            className="text-xs h-7 gap-1.5 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
          >
            <span>{actionLabel}</span>
            <ArrowRight className="w-3 h-3" />
          </Button>
        </div>
      )}
    </div>
  );
}

export default InsightCard;
