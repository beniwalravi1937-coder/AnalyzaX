import { useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { CheckCircle2, Circle, ChevronDown, ChevronRight, Sparkles, X } from "lucide-react";
import { useDataset } from "@/context/DatasetContext";

export function GettingStartedChecklist() {
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
      completed: false, // Completes upon active inquiry or user visit
    },
  ];

  const completedCount = steps.filter((s) => s.completed).length;
  const progressPercent = Math.round((completedCount / steps.length) * 100);

  if (isDismissed) return null;

  return (
    <div
      style={{
        margin: "0.75rem 0.5rem 1rem 0.5rem",
        background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9))",
        border: "1px solid rgba(99, 102, 241, 0.25)",
        borderRadius: "10px",
        overflow: "hidden",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.25)",
      }}
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          padding: "0.6rem 0.75rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          userSelect: "none",
          background: "rgba(99, 102, 241, 0.08)",
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
            onClick={handleDismiss}
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
        <div style={{ padding: "0.5rem 0.75rem 0.65rem" }}>
          {/* Progress bar */}
          <div
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
                  <CheckCircle2 style={{ width: "13px", height: "13px", color: "#34d399", shrink: 0 }} />
                ) : (
                  <Circle style={{ width: "13px", height: "13px", color: "#64748b", shrink: 0 }} />
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
