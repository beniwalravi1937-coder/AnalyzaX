import React from "react";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: React.ReactNode;
  delta?: number | string;
  deltaType?: "increase" | "decrease" | "neutral";
  trendLabel?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  chart?: React.ReactNode;
  tone?: "indigo" | "emerald" | "amber" | "rose" | "cyan" | "default";
}

export function MetricCard({
  label,
  value,
  delta,
  deltaType = "increase",
  trendLabel,
  subtitle,
  icon,
  chart,
  tone = "default",
  className,
  ...props
}: MetricCardProps) {
  const toneMap = {
    default: "border-white/10 hover:border-white/20 bg-slate-900/60",
    indigo: "border-indigo-500/20 hover:border-indigo-500/40 bg-indigo-950/20",
    emerald: "border-emerald-500/20 hover:border-emerald-500/40 bg-emerald-950/20",
    amber: "border-amber-500/20 hover:border-amber-500/40 bg-amber-950/20",
    rose: "border-rose-500/20 hover:border-rose-500/40 bg-rose-950/20",
    cyan: "border-cyan-500/20 hover:border-cyan-500/40 bg-cyan-950/20",
  };

  return (
    <div
      className={cn(
        "relative rounded-xl border p-5 backdrop-blur-sm transition-all duration-200 flex flex-col justify-between overflow-hidden",
        toneMap[tone],
        className
      )}
      {...props}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {label}
          </span>
          <div className="mt-1 text-2xl sm:text-3xl font-bold tracking-tight text-white font-mono tabular-nums">
            {value}
          </div>
        </div>

        {icon && (
          <div className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-300">
            {icon}
          </div>
        )}
      </div>

      {(delta !== undefined || subtitle || chart) && (
        <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 flex-wrap">
            {delta !== undefined && (
              <span
                className={cn(
                  "inline-flex items-center gap-1 font-medium px-2 py-0.5 rounded-full text-[11px]",
                  deltaType === "increase"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : deltaType === "decrease"
                    ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                )}
              >
                {deltaType === "increase" ? (
                  <TrendingUp className="w-3 h-3" />
                ) : deltaType === "decrease" ? (
                  <TrendingDown className="w-3 h-3" />
                ) : (
                  <Minus className="w-3 h-3" />
                )}
                {typeof delta === "number" && delta > 0 ? `+${delta}%` : `${delta}%`}
              </span>
            )}

            {trendLabel && <span className="text-slate-400">{trendLabel}</span>}
            {subtitle && !trendLabel && <span className="text-slate-400">{subtitle}</span>}
          </div>

          {chart && <div className="shrink-0">{chart}</div>}
        </div>
      )}
    </div>
  );
}

export default MetricCard;
