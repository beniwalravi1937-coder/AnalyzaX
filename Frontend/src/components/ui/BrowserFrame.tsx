import React from "react";
import { cn } from "@/lib/utils";

export interface BrowserFrameProps extends React.HTMLAttributes<HTMLDivElement> {
  url?: string;
  title?: string;
  showDots?: boolean;
  showAddressBar?: boolean;
  aspectRatio?: "16/9" | "16/10" | "auto";
  badge?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  contentClassName?: string;
}

/**
 * BrowserFrame / ProductScreenshot component
 * Renders a high-fidelity desktop application frame with macOS window chrome,
 * address bar, status badge, and ambient drop-shadow.
 * Reusable for marketing hero showcases, product walkthroughs, and documentation.
 */
export function BrowserFrame({
  url = "app.analyzax.ai/workspace",
  title = "AnalyzaX Studio",
  showDots = true,
  showAddressBar = true,
  aspectRatio = "auto",
  badge,
  children,
  className,
  contentClassName,
  ...props
}: BrowserFrameProps) {
  const aspectClass =
    aspectRatio === "16/9"
      ? "aspect-video"
      : aspectRatio === "16/10"
      ? "aspect-[16/10]"
      : "";

  return (
    <div
      className={cn(
        "relative rounded-xl border border-white/10 bg-slate-950/90 shadow-2xl shadow-indigo-950/20 backdrop-blur-xl overflow-hidden transition-all duration-300",
        className
      )}
      {...props}
    >
      {/* Top Window Chrome */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-white/[0.07] select-none text-xs">
        {/* Left: Window Dots */}
        <div className="flex items-center gap-2 w-24">
          {showDots && (
            <>
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500/80 border border-rose-600/40" />
              <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80 border border-amber-600/40" />
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 border border-emerald-600/40" />
            </>
          )}
        </div>

        {/* Center: URL / Title Bar */}
        <div className="flex-1 max-w-md mx-auto">
          {showAddressBar ? (
            <div className="flex items-center justify-center gap-1.5 px-3 py-1 rounded-md bg-slate-950/60 border border-white/[0.08] text-slate-400 font-mono text-[11px] truncate">
              <svg
                className="w-3 h-3 text-emerald-400 shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              <span className="truncate">{url}</span>
            </div>
          ) : (
            <div className="text-center font-medium text-slate-300 text-xs truncate">
              {title}
            </div>
          )}
        </div>

        {/* Right: Badge or Balance placeholder */}
        <div className="flex items-center justify-end gap-2 w-24">
          {badge ? (
            badge
          ) : (
            <div className="flex items-center gap-1 text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </div>
          )}
        </div>
      </div>

      {/* Frame Content / Viewport Area */}
      <div
        className={cn(
          "relative overflow-hidden bg-slate-950/60",
          aspectClass,
          contentClassName
        )}
      >
        {children}
      </div>
    </div>
  );
}

export const ProductScreenshot = BrowserFrame;
export default BrowserFrame;
