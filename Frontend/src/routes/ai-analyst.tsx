import { createFileRoute } from "@tanstack/react-router";
import React, { useState } from "react";
import { AIAnalystWorkspace } from "@/components/chat/AIAnalystWorkspace";
import { AICopilotWorkspace } from "@/components/chat/AICopilotWorkspace";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import { useDataset } from "@/context/DatasetContext";
import { Bot, ChevronDown, Database, Sparkles } from "lucide-react";

export const Route = createFileRoute("/ai-analyst")({
  head: () => ({
    meta: [
      { title: "AI Copilot — AnalyzaX" },
      {
        name: "description",
        content:
          "Ask questions, investigate trends, and turn data into decisions with your autonomous AI analytics teammate.",
      },
      { property: "og:title", content: "AI Copilot — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Ask questions, investigate trends, and turn data into decisions with your AI analytics teammate.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-ai-analyst.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-ai-analyst.png" },
    ],
  }),
  component: AIAnalystPage,
});

function AIAnalystPage() {
  const [activeTab, setActiveTab] = useState<"copilot" | "classic">("copilot");
  const { datasets, activeDataset, selectDataset } = useDataset();
  const [isDatasetMenuOpen, setIsDatasetMenuOpen] = useState(false);

  const datasetName = activeDataset?.name || activeDataset?.original_filename || "Select Dataset";
  const datasetVersion = activeDataset?.active_version_id
    ? activeDataset.active_version_id.toUpperCase()
    : "V1";

  return (
    <div className="ax-stack" style={{ gap: "1.25rem" }}>
      {/* ============================================================ */}
      {/* PREMIUM HEADER                                               */}
      {/* ============================================================ */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "1rem",
          paddingBottom: "1rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--text-primary)",
              letterSpacing: "-0.02em",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Sparkles style={{ width: "20px", height: "20px", color: "var(--color-primary, #f59e0b)" }} />
            AI Copilot
          </h1>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Ask questions, investigate trends, and turn data into decisions.
          </p>
        </div>

        {/* Controls: Mode Switcher + Dataset Dropdown */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          {/* Controls: [AI Copilot] [Classic Studio] */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              padding: "0.2rem",
            }}
          >
            <button
              type="button"
              onClick={() => setActiveTab("copilot")}
              className={`btn btn-sm ${activeTab === "copilot" ? "btn-primary" : "btn-secondary"}`}
              style={{
                fontSize: "0.75rem",
                padding: "0.25rem 0.6rem",
                borderRadius: "4px",
                border: "none",
              }}
            >
              <Sparkles style={{ width: "13px", height: "13px" }} />
              AI Copilot
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("classic")}
              className={`btn btn-sm ${activeTab === "classic" ? "btn-primary" : "btn-secondary"}`}
              style={{
                fontSize: "0.75rem",
                padding: "0.25rem 0.6rem",
                borderRadius: "4px",
                border: "none",
                marginLeft: "0.2rem",
              }}
            >
              <Bot style={{ width: "13px", height: "13px" }} />
              Classic Studio
            </button>
          </div>

          {/* Dataset Selector: ${datasetName} · ${version} ▼ */}
          <div style={{ position: "relative" }}>
            <button
              type="button"
              onClick={() => setIsDatasetMenuOpen(!isDatasetMenuOpen)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.35rem 0.75rem",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-primary)",
                backgroundColor: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              <Database style={{ width: "13px", height: "13px", color: "var(--color-primary, #f59e0b)" }} />
              <span>{datasetName} · {datasetVersion}</span>
              <ChevronDown style={{ width: "13px", height: "13px", color: "var(--text-muted)" }} />
            </button>

            {isDatasetMenuOpen && (
              <>
                <div
                  style={{ position: "fixed", inset: 0, zIndex: 90 }}
                  onClick={() => setIsDatasetMenuOpen(false)}
                />
                <div
                  style={{
                    position: "absolute",
                    right: 0,
                    top: "calc(100% + 4px)",
                    zIndex: 100,
                    minWidth: "220px",
                    backgroundColor: "var(--bg-surface)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "8px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
                    padding: "0.35rem",
                  }}
                >
                  <div style={{ padding: "0.35rem 0.5rem", fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                    Select Active Dataset
                  </div>
                  {datasets.map((d) => (
                    <button
                      key={d.id}
                      type="button"
                      onClick={() => {
                        selectDataset(d.id);
                        setIsDatasetMenuOpen(false);
                      }}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "0.45rem 0.6rem",
                        fontSize: "0.8125rem",
                        borderRadius: "4px",
                        border: "none",
                        backgroundColor: d.id === activeDataset?.id ? "rgba(245, 158, 11, 0.15)" : "transparent",
                        color: d.id === activeDataset?.id ? "var(--color-primary, #f59e0b)" : "var(--text-primary)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                      }}
                    >
                      <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {d.name || d.original_filename}
                      </span>
                      <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                        {(d.active_version_id || "v1").toUpperCase()}
                      </span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Workspace Area */}
      <div>
        {!activeDataset && datasets.length === 0 ? (
          <GuidedOnboarding
            title="Ask Questions & Chat With Your Data"
            description="Your AI analytical partner. Ask questions in plain English, discover hidden anomalies, generate automated charts, and receive executive summaries — with zero code required."
            badgeText="AI Analyst Setup"
            features={[
              "Natural language Q&A backed by real analytical data execution",
              "Proactive anomaly detection & multi-step investigative plans",
              "Instant chart synthesis and automated dashboard recommendations",
            ]}
          />
        ) : activeTab === "copilot" ? (
          <AICopilotWorkspace />
        ) : (
          <AIAnalystWorkspace />
        )}
      </div>
    </div>
  );
}
