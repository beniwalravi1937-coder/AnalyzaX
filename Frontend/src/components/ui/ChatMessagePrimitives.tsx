import React from "react";
import { cn } from "@/lib/utils";
import { Sparkles, User, ArrowRight } from "lucide-react";
import { Button } from "./button";

export interface UserMessageProps extends React.HTMLAttributes<HTMLDivElement> {
  content: string;
  timestamp?: string;
  userInitials?: string;
}

export function UserMessage({
  content,
  timestamp,
  userInitials = "U",
  className,
  ...props
}: UserMessageProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 justify-end max-w-3xl ml-auto group",
        className
      )}
      {...props}
    >
      <div className="space-y-1 text-right">
        <div className="inline-block rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-2.5 text-sm text-white shadow-md text-left leading-relaxed">
          {content}
        </div>
        {timestamp && (
          <div className="text-[10px] text-slate-500 font-mono pr-1">{timestamp}</div>
        )}
      </div>

      <div className="w-8 h-8 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center text-xs font-semibold text-slate-200 shrink-0">
        {userInitials ? userInitials : <User className="w-4 h-4" />}
      </div>
    </div>
  );
}

export interface AIMessageProps extends React.HTMLAttributes<HTMLDivElement> {
  content: string;
  timestamp?: string;
  badge?: string;
  toolExecutions?: React.ReactNode;
  actions?: React.ReactNode;
  recommendations?: Array<{
    title: string;
    description?: string;
    actionLabel?: string;
    onApply?: () => void;
  }>;
}

export function AIMessage({
  content,
  timestamp,
  badge = "AnalyzaX Copilot",
  toolExecutions,
  actions,
  recommendations,
  className,
  ...props
}: AIMessageProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 max-w-3xl mr-auto group animate-in fade-in-50 duration-200",
        className
      )}
      {...props}
    >
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-cyan-500 p-0.5 shrink-0 shadow-lg shadow-indigo-600/20">
        <div className="w-full h-full rounded-full bg-slate-950 flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-indigo-400" />
        </div>
      </div>

      <div className="space-y-2 flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-white">{badge}</span>
          {timestamp && (
            <span className="text-[10px] text-slate-500 font-mono">{timestamp}</span>
          )}
        </div>

        {toolExecutions && <div className="text-xs">{toolExecutions}</div>}

        <div className="rounded-2xl rounded-tl-sm border border-white/10 bg-slate-900/80 p-4 text-sm text-slate-200 shadow-md leading-relaxed whitespace-pre-wrap">
          {content}
        </div>

        {recommendations && recommendations.length > 0 && (
          <div className="space-y-2 pt-1">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Recommended Next Actions
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {recommendations.map((rec, i) => (
                <RecommendationCard
                  key={i}
                  title={rec.title}
                  description={rec.description}
                  actionLabel={rec.actionLabel}
                  onApply={rec.onApply}
                />
              ))}
            </div>
          </div>
        )}

        {actions && <div className="flex items-center gap-2 pt-1">{actions}</div>}
      </div>
    </div>
  );
}

export interface RecommendationCardProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onApply?: () => void;
  className?: string;
}

export function RecommendationCard({
  title,
  description,
  actionLabel = "Run analysis",
  onApply,
  className,
}: RecommendationCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-white/10 bg-slate-950/60 p-3 flex flex-col justify-between gap-2 hover:border-indigo-500/40 transition-colors duration-150",
        className
      )}
    >
      <div>
        <h4 className="text-xs font-semibold text-white tracking-tight">{title}</h4>
        {description && (
          <p className="mt-0.5 text-[11px] text-slate-400 line-clamp-2 leading-normal">
            {description}
          </p>
        )}
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={onApply}
        className="h-6 px-2 text-[11px] font-medium text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 self-start gap-1"
      >
        <span>{actionLabel}</span>
        <ArrowRight className="w-3 h-3" />
      </Button>
    </div>
  );
}

export default AIMessage;
