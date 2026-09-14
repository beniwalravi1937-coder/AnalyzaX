import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Copy, Check, Maximize2, Minimize2, Info } from "lucide-react";
import { Button } from "./button";
import { AnalysisStatus, AnalysisExecutionStatus } from "./AnalysisStatus";

export interface ResultCardProps {
  title: string;
  subtitle?: string;
  status?: AnalysisExecutionStatus;
  statusMessage?: string;
  durationMs?: number;
  rowCount?: number;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  secondaryDetails?: React.ReactNode;
  className?: string;
  defaultExpanded?: boolean;
  canCollapse?: boolean;
  onCopy?: () => void;
  onExport?: () => void;
}

export function ResultCard({
  title,
  subtitle,
  status = "idle",
  statusMessage,
  durationMs,
  rowCount,
  badge,
  actions,
  children,
  secondaryDetails,
  className,
  defaultExpanded = true,
  canCollapse = true,
  onCopy,
  onExport,
}: ResultCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [showDetails, setShowDetails] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = () => {
    if (onCopy) {
      onCopy();
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-white/10 bg-slate-900/60 shadow-xl overflow-hidden transition-all duration-200",
        className
      )}
    >
      {/* Header */}
      <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.06] bg-slate-900/40">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h3 className="text-base sm:text-lg font-semibold text-white tracking-tight leading-snug">
              {title}
            </h3>
            {badge}
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
          {subtitle && <p className="text-xs sm:text-sm text-slate-400">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-center">
          {secondaryDetails && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
              className={cn(
                "h-8 px-2.5 text-xs text-slate-300 hover:text-white hover:bg-white/5 gap-1.5",
                showDetails && "bg-indigo-500/10 text-indigo-300"
              )}
            >
              <Info className="w-3.5 h-3.5" />
              <span>Details</span>
            </Button>
          )}

          {onCopy && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8 px-2.5 text-xs text-slate-300 hover:text-white hover:bg-white/5 gap-1"
            >
              {isCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </Button>
          )}

          {actions}

          {canCollapse && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-white/5"
              aria-label={isExpanded ? "Collapse section" : "Expand section"}
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          )}
        </div>
      </div>

      {/* Progressively Disclosed Details */}
      {showDetails && secondaryDetails && (
        <div className="p-4 bg-slate-950/60 border-b border-white/[0.06] text-xs text-slate-300 animate-fadeIn">
          {secondaryDetails}
        </div>
      )}

      {/* Body Content */}
      {isExpanded && <div className="p-4 sm:p-5">{children}</div>}
    </div>
  );
}
