import { createFileRoute } from "@tanstack/react-router";
import React, { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { AIAnalystWorkspace } from "@/components/chat/AIAnalystWorkspace";
import { AICopilotWorkspace } from "@/components/chat/AICopilotWorkspace";
import { Bot, Sparkles } from "lucide-react";

export const Route = createFileRoute("/ai-analyst")({
  head: () => ({
    meta: [
      { title: "AI Copilot & Analytical Studio — AnalyzaX" },
      {
        name: "description",
        content:
          "Autonomous analytical partner. Discover signals, run multi-step investigations, and plan dashboards with explicit human approval boundaries.",
      },
      { property: "og:title", content: "AI Copilot & Analytical Studio — AnalyzaX" },
      {
        property: "og:description",
        content: "Autonomous analytical AI partner powered by DuckDB SQL validation.",
      },
    ],
  }),
  component: AIAnalystPage,
});

function AIAnalystPage() {
  const [activeTab, setActiveTab] = useState<"copilot" | "classic">("copilot");

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
            <Sparkles className="w-3.5 h-3.5" />
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
        {activeTab === "copilot" ? <AICopilotWorkspace /> : <AIAnalystWorkspace />}
      </div>
    </div>
  );
}
