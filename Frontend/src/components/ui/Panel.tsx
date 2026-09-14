import React from "react";
import { cn } from "@/lib/utils";

export interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "sunken" | "glass";
  padding?: "none" | "sm" | "md" | "lg";
}

export function Panel({
  variant = "default",
  padding = "md",
  className,
  children,
  ...props
}: PanelProps) {
  const variantClasses = {
    default: "bg-slate-900/60 border-white/10 text-white",
    elevated: "bg-slate-850 border-white/15 shadow-xl text-white",
    sunken: "bg-slate-950/70 border-white/5 text-slate-200",
    glass: "bg-slate-900/40 border-white/10 backdrop-blur-md text-white shadow-lg",
  };

  const paddingClasses = {
    none: "p-0",
    sm: "p-3",
    md: "p-5",
    lg: "p-6 sm:p-8",
  };

  return (
    <div
      className={cn(
        "rounded-xl border transition-all duration-150 overflow-hidden",
        variantClasses[variant],
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default Panel;
