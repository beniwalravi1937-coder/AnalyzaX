import { useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { CheckCircle2, Circle, ChevronDown, ChevronRight, Sparkles, X } from "lucide-react";
import { useDataset } from "@/context/DatasetContext";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface GettingStartedChecklistProps {
  isCollapsed?: boolean;
}

export function GettingStartedChecklist({ isCollapsed = false }: GettingStartedChecklistProps) {
  const { datasets, activeDataset } = useDataset();
  const [isDismissed, setIsDismissed] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  useEffect(() => {
    const dismissed = localStorage.getItem("analyzax_checklist_dismissed");
    if (dismissed === "true") {
      setIsDismissed(true);
    }
  }, []);

  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDismissed(true);
    localStorage.setItem("analyzax_checklist_dismissed", "true");
  };

  const steps = [
    {
      id: "upload",
      title: "Upload or select dataset",
      to: "/data",
      completed: datasets.length > 0,
    },
    {
      id: "visualize",
      title: "Create visual or explore EDA",
      to: "/visualizations",
      completed: Boolean(activeDataset),
    },
    {
      id: "copilot",
      title: "Inquire with AI Copilot",
      to: "/ai-analyst",
      completed: false,
    },
  ];

  const completedCount = steps.filter((s) => s.completed).length;
  const progressPercent = Math.round((completedCount / steps.length) * 100);

  if (isDismissed) return null;

  // Collapsed icon-only mode with accessible tooltip
  if (isCollapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            role="region"
            aria-label={`Getting Started Checklist: ${completedCount} of ${steps.length} completed`}
            className="flex items-center justify-center h-9 w-9 mx-auto rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 cursor-pointer relative"
          >
            <Sparkles className="w-4 h-4" />
            <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full bg-indigo-600 text-white text-[9px] font-bold flex items-center justify-center">
              {completedCount}/{steps.length}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="right" className="bg-slate-900 border-slate-700 text-xs text-white">
          <span>Getting Started: {completedCount}/{steps.length} tasks completed</span>
        </TooltipContent>
      </Tooltip>
    );
  }

  const handleHeaderKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setIsExpanded((prev) => !prev);
    }
  };

  return (
    <div
      role="region"
      aria-label="Getting Started Onboarding Checklist"
      style={{
        display: "block",
        visibility: "visible",
        opacity: 1,
        position: "relative",
        zIndex: 10,
        margin: "0.75rem 0.5rem 1rem 0.5rem",
        background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.95))",
        border: "1px solid rgba(99, 102, 241, 0.25)",
        borderRadius: "10px",
        overflow: "hidden",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.25)",
      }}
    >
      {/* Header trigger */}
      <div
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        aria-controls="getting-started-steps"
        onClick={() => setIsExpanded(!isExpanded)}
        onKeyDown={handleHeaderKeyDown}
        style={{
          padding: "0.6rem 0.75rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          userSelect: "none",
          background: "rgba(99, 102, 241, 0.08)",
          outline: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
          <Sparkles style={{ width: "14px", height: "14px", color: "#818cf8" }} />
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#e2e8f0" }}>
            Getting Started
          </span>
          <span
            style={{
              fontSize: "0.6875rem",
              background: completedCount === steps.length ? "rgba(16, 185, 129, 0.2)" : "rgba(99, 102, 241, 0.25)",
              color: completedCount === steps.length ? "#34d399" : "#a5b4fc",
              padding: "0.1rem 0.35rem",
              borderRadius: "999px",
              fontWeight: 600,
            }}
          >
            {completedCount}/{steps.length}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <button
            type="button"
            onClick={handleDismiss}
            aria-label="Dismiss Getting Started checklist"
            title="Dismiss checklist"
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              padding: "2px",
              display: "flex",
              alignItems: "center",
            }}
          >
            <X style={{ width: "12px", height: "12px" }} />
          </button>
          {isExpanded ? (
            <ChevronDown style={{ width: "14px", height: "14px", color: "#94a3b8" }} />
          ) : (
            <ChevronRight style={{ width: "14px", height: "14px", color: "#94a3b8" }} />
          )}
        </div>
      </div>

      {isExpanded && (
        <div id="getting-started-steps" style={{ padding: "0.5rem 0.75rem 0.65rem" }}>
          {/* Progress bar */}
          <div
            role="progressbar"
            aria-valuenow={completedCount}
            aria-valuemin={0}
            aria-valuemax={steps.length}
            aria-valuetext={`${completedCount} of ${steps.length} onboarding tasks completed`}
            style={{
              height: "4px",
              width: "100%",
              backgroundColor: "rgba(255, 255, 255, 0.1)",
              borderRadius: "999px",
              marginBottom: "0.6rem",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${progressPercent}%`,
                background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
                borderRadius: "999px",
                transition: "width 0.3s ease",
              }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {steps.map((step) => (
              <Link
                key={step.id}
                to={step.to}
                aria-label={`${step.title} (${step.completed ? "Completed" : "Incomplete"})`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.45rem",
                  fontSize: "0.725rem",
                  color: step.completed ? "#94a3b8" : "#cbd5e1",
                  textDecoration: step.completed ? "line-through" : "none",
                  transition: "color 0.15s ease",
                }}
              >
                {step.completed ? (
                  <CheckCircle2 style={{ width: "13px", height: "13px", color: "#34d399", flexShrink: 0 }} />
                ) : (
                  <Circle style={{ width: "13px", height: "13px", color: "#64748b", flexShrink: 0 }} />
                )}
                <span>{step.title}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default GettingStartedChecklist;
