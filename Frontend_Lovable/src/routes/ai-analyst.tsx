import { createFileRoute } from "@tanstack/react-router";
import React, { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { AIAnalystWorkspace } from "@/components/chat/AIAnalystWorkspace";
import { AICopilotWorkspace } from "@/components/chat/AICopilotWorkspace";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import { useDataset } from "@/context/DatasetContext";
import { Bot } from "lucide-react";

export const Route = createFileRoute("/ai-analyst")({
  head: () => ({
    meta: [
      { title: "AI Data Analyst — AnalyzaX" },
      {
        name: "description",
        content:
          "Ask questions in plain English and get instant answers, visualizations, and executive summaries from your data — no SQL or code required.",
      },
      { property: "og:title", content: "AI Data Analyst — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Ask questions in plain English and get instant answers, visualizations, and summaries from your data.",
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
  const { datasets, activeDataset } = useDataset();

  return (
    <div className="ax-stack">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <PageHeader
          title="AI Copilot & Analytical Studio"
          description="Evolved from reactive question-answering into an autonomous analytical partner. Discover signals, run multi-step investigations, and plan dashboards with explicit human approval boundaries."
          badge={{ text: "Phase 25 — Advanced AI Product Intelligence", variant: "indigo" }}
        />

        <div style={{ display: "flex", alignItems: "center", backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "8px", padding: "0.25rem", shrink: 0 }}>
          <button
            onClick={() => setActiveTab("copilot")}
            className={`btn btn-sm ${activeTab === "copilot" ? "btn-primary" : "btn-secondary"}`}
            style={{ display: "flex", alignItems: "center", gap: "0.35rem", fontSize: "0.75rem" }}
          >
            <img src="/logo.png" alt="" style={{ width: "14px", height: "14px", objectFit: "contain" }} />
            AI Copilot
          </button>
          <button
            onClick={() => setActiveTab("classic")}
            className={`btn btn-sm ${activeTab === "classic" ? "btn-primary" : "btn-secondary"}`}
            style={{ display: "flex", alignItems: "center", gap: "0.35rem", fontSize: "0.75rem", marginLeft: "0.25rem" }}
          >
            <Bot className="w-3.5 h-3.5" />
            Classic Studio
          </button>
        </div>
      </div>

      <div style={{ marginTop: "1rem" }}>
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
