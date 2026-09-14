import React from "react";
import { cn } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "./card";

export interface ChartCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  loading?: boolean;
}

export function ChartCard({
  title,
  description,
  badge,
  actions,
  footer,
  children,
  loading = false,
  className,
  ...props
}: ChartCardProps) {
  return (
    <Card
      className={cn(
        "rounded-xl border border-white/10 bg-slate-900/60 shadow-lg backdrop-blur-sm flex flex-col overflow-hidden transition-all duration-200 hover:border-white/20",
        className
      )}
      {...props}
    >
      <CardHeader className="p-4 sm:p-5 border-b border-white/5 flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <CardTitle className="text-base font-semibold text-white tracking-tight truncate">
              {title}
            </CardTitle>
            {badge}
          </div>
          {description && (
            <CardDescription className="text-xs text-slate-400">
              {description}
            </CardDescription>
          )}
        </div>

        {actions && <div className="flex items-center gap-1.5 shrink-0">{actions}</div>}
      </CardHeader>

      <CardContent className="p-4 sm:p-5 flex-1 relative min-h-[260px] flex flex-col justify-center">
        {loading ? (
          <div className="absolute inset-0 bg-slate-950/40 backdrop-blur-[2px] flex items-center justify-center z-10">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
              Rendering analytical visualization...
            </div>
          </div>
        ) : null}

        {children}
      </CardContent>

      {footer && (
        <div className="px-4 py-2.5 bg-slate-950/40 border-t border-white/5 text-xs text-slate-400 flex items-center justify-between">
          {footer}
        </div>
      )}
    </Card>
  );
}

export default ChartCard;
