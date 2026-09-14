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
        background: "linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.98) 100%)",
        border: "1px solid rgba(99, 102, 241, 0.45)",
        borderRadius: "10px",
        overflow: "hidden",
        boxShadow: "0 6px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(99, 102, 241, 0.12)",
      }}
    >
      {/* Header trigger with enhanced visual contrast */}
      <div
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        aria-controls="getting-started-steps"
        onClick={() => setIsExpanded(!isExpanded)}
        onKeyDown={handleHeaderKeyDown}
        style={{
          padding: "0.7rem 0.85rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          userSelect: "none",
          background: "linear-gradient(90deg, rgba(99, 102, 241, 0.18) 0%, rgba(168, 85, 247, 0.08) 100%)",
          borderBottom: isExpanded ? "1px solid rgba(99, 102, 241, 0.2)" : "none",
          outline: "none",
          transition: "background 0.15s ease",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.55rem" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "22px",
              height: "22px",
              borderRadius: "6px",
              backgroundColor: "rgba(99, 102, 241, 0.3)",
              color: "#a5b4fc",
            }}
          >
            <Sparkles style={{ width: "13px", height: "13px", color: "#c7d2fe" }} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "#ffffff", letterSpacing: "0.01em" }}>
                Getting Started
              </span>
              <span
                style={{
                  fontSize: "0.6875rem",
                  background: completedCount === steps.length ? "rgba(16, 185, 129, 0.25)" : "rgba(99, 102, 241, 0.35)",
                  color: completedCount === steps.length ? "#34d399" : "#c7d2fe",
                  border: completedCount === steps.length ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid rgba(99, 102, 241, 0.5)",
                  padding: "0.1rem 0.45rem",
                  borderRadius: "999px",
                  fontWeight: 700,
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {completedCount}/{steps.length}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
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
              padding: "3px",
              borderRadius: "4px",
              display: "flex",
              alignItems: "center",
              transition: "color 0.15s ease",
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = "#ffffff")}
            onMouseOut={(e) => (e.currentTarget.style.color = "#94a3b8")}
          >
            <X style={{ width: "13px", height: "13px" }} />
          </button>
          {isExpanded ? (
            <ChevronDown style={{ width: "15px", height: "15px", color: "#cbd5e1" }} />
          ) : (
            <ChevronRight style={{ width: "15px", height: "15px", color: "#cbd5e1" }} />
          )}
        </div>
      </div>

      {isExpanded && (
        <div id="getting-started-steps" style={{ padding: "0.65rem 0.85rem 0.75rem" }}>
          {/* Progress header with clear percentage feedback */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "0.4rem",
              fontSize: "0.6875rem",
            }}
          >
            <span style={{ color: "#94a3b8", fontWeight: 500 }}>Setup Progress</span>
            <span style={{ color: completedCount === steps.length ? "#34d399" : "#c7d2fe", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>
              {progressPercent}%
            </span>
          </div>

          {/* High-contrast Progress bar */}
          <div
            role="progressbar"
            aria-valuenow={completedCount}
            aria-valuemin={0}
            aria-valuemax={steps.length}
            aria-valuetext={`${completedCount} of ${steps.length} onboarding tasks completed (${progressPercent}%)`}
            style={{
              height: "5px",
              width: "100%",
              backgroundColor: "rgba(255, 255, 255, 0.12)",
              borderRadius: "999px",
              marginBottom: "0.75rem",
              overflow: "hidden",
              boxShadow: "inset 0 1px 2px rgba(0, 0, 0, 0.3)",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${progressPercent}%`,
                background: completedCount === steps.length
                  ? "linear-gradient(90deg, #10b981, #34d399)"
                  : "linear-gradient(90deg, #6366f1, #a855f7)",
                borderRadius: "999px",
                transition: "width 0.3s ease",
                boxShadow: completedCount > 0 ? "0 0 8px rgba(99, 102, 241, 0.6)" : "none",
              }}
            />
          </div>

          {/* Actionable task step rows */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            {steps.map((step) => (
              <Link
                key={step.id}
                to={step.to}
                aria-label={`${step.title} (${step.completed ? "Completed" : "Incomplete"})`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.55rem",
                  padding: "0.4rem 0.55rem",
                  borderRadius: "6px",
                  backgroundColor: step.completed ? "rgba(255, 255, 255, 0.02)" : "rgba(99, 102, 241, 0.08)",
                  border: step.completed ? "1px solid rgba(255, 255, 255, 0.04)" : "1px solid rgba(99, 102, 241, 0.2)",
                  fontSize: "0.75rem",
                  fontWeight: step.completed ? 500 : 600,
                  color: step.completed ? "#94a3b8" : "#f8fafc",
                  textDecoration: "none",
                  transition: "all 0.15s ease",
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = "rgba(99, 102, 241, 0.16)";
                  e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.45)";
                  e.currentTarget.style.color = "#ffffff";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = step.completed ? "rgba(255, 255, 255, 0.02)" : "rgba(99, 102, 241, 0.08)";
                  e.currentTarget.style.borderColor = step.completed ? "rgba(255, 255, 255, 0.04)" : "rgba(99, 102, 241, 0.2)";
                  e.currentTarget.style.color = step.completed ? "#94a3b8" : "#f8fafc";
                }}
              >
                {step.completed ? (
                  <CheckCircle2 style={{ width: "14px", height: "14px", color: "#10b981", flexShrink: 0 }} />
                ) : (
                  <Circle style={{ width: "14px", height: "14px", color: "#818cf8", flexShrink: 0 }} />
                )}
                <span style={{ textDecoration: step.completed ? "line-through" : "none", flex: 1 }}>
                  {step.title}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default GettingStartedChecklist;
