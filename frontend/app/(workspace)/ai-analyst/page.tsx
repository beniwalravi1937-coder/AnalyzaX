"use client";

import React, { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { AIAnalystWorkspace } from "@/components/chat/AIAnalystWorkspace";
import { AICopilotWorkspace } from "@/components/chat/AICopilotWorkspace";
import { Bot, Sparkles } from "lucide-react";

export default function AIAnalystPage() {
  const [activeTab, setActiveTab] = useState<"copilot" | "classic">("copilot");

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="AI Copilot & Analytical Studio"
          description="Evolved from reactive question-answering into an autonomous analytical partner. Discover signals, run multi-step investigations, and plan dashboards with explicit human approval boundaries."
          badge={{ text: "Phase 25 — Advanced AI Product Intelligence", variant: "indigo" }}
        />

        <div className="flex items-center bg-zinc-900 border border-zinc-800 rounded-lg p-1 shrink-0">
          <button
            onClick={() => setActiveTab("copilot")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === "copilot"
                ? "bg-purple-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Copilot
          </button>
          <button
            onClick={() => setActiveTab("classic")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === "classic"
                ? "bg-zinc-800 text-zinc-100 shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Bot className="w-3.5 h-3.5" />
            Classic Studio
          </button>
        </div>
      </div>

      <div>
        {activeTab === "copilot" ? <AICopilotWorkspace /> : <AIAnalystWorkspace />}
      </div>
    </div>
  );
}

