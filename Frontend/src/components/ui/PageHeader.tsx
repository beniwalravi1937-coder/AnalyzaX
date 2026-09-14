import React from "react";
import { cn } from "@/lib/utils";

export interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  eyebrow?: React.ReactNode;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  breadcrumbs?: React.ReactNode;
  badge?: React.ReactNode;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  breadcrumbs,
  badge,
  className,
  ...props
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 pb-6 border-b border-white/[0.08] mb-6",
        className
      )}
      {...props}
    >
      {breadcrumbs && <div className="text-xs text-slate-400">{breadcrumbs}</div>}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1.5 min-w-0">
          {eyebrow && (
            <div className="flex items-center gap-2">
              {typeof eyebrow === "string" ? (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wider uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {eyebrow}
                </span>
              ) : (
                eyebrow
              )}
            </div>
          )}

          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-[30px] font-bold text-white tracking-tight leading-tight">
              {title}
            </h1>
            {badge}
          </div>

          {description && (
            <p className="text-sm sm:text-[15px] text-slate-400 max-w-3xl leading-relaxed">
              {description}
            </p>
          )}
        </div>

        {actions && (
          <div className="flex items-center gap-2.5 shrink-0 flex-wrap sm:self-start mt-1 sm:mt-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}

export interface SectionHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export function SectionHeader({
  title,
  description,
  badge,
  actions,
  className,
  ...props
}: SectionHeaderProps) {
  return (
    <div
      className={cn("flex items-center justify-between gap-4 mb-4", className)}
      {...props}
    >
      <div className="space-y-0.5 min-w-0">
        <div className="flex items-center gap-2">
          <h2 className="text-lg sm:text-[20px] font-semibold text-white tracking-tight">
            {title}
          </h2>
          {badge}
        </div>
        {description && (
          <p className="text-xs sm:text-sm text-slate-400">{description}</p>
        )}
      </div>

      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

export default PageHeader;
