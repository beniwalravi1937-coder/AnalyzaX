"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDataset } from "@/context/DatasetContext";
import {
  CopilotContext,
  CopilotResponse,
  DashboardPlan,
} from "@/types/copilot";
import {
  approveWorkflowStep,
  executeDashboardPlan,
  sendCopilotChat,
} from "@/services/copilotApi";
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Check,
  CheckCircle,
  Clock,
  Compass,
  Copy,
  Database,
  Layout,
  Play,
  RefreshCw,
  Send,
  Sparkles,
  Trash2,
  User,
} from "lucide-react";

interface Message {
  role: "user" | "copilot";
  content: string;
  responseObj?: CopilotResponse;
}

const STARTER_PROMPTS = [
  "Summarize key trends & distributions in this dataset",
  "Compare student math scores against reading scores with chart recommendations",
  "Identify outliers or anomalies across score dimensions",
  "Plan an executive performance dashboard with KPIs",
];

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-2.5 rounded-lg border border-zinc-800 bg-zinc-950 font-mono text-xs overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-zinc-800 bg-zinc-900/60 text-[11px] text-zinc-400">
        <span className="uppercase tracking-wider font-semibold text-zinc-300">{language || "code"}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-zinc-200 leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function FormattedContent({ text }: { text: string }) {
  // Parse code blocks with ```lang ... ```
  const parts = [];
  const codeRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        type: "text",
        content: text.substring(lastIndex, match.index),
      });
    }
    parts.push({
      type: "code",
      language: match[1] || "text",
      content: match[2].trim(),
    });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push({
      type: "text",
      content: text.substring(lastIndex),
    });
  }

  return (
    <div className="space-y-2 text-xs leading-relaxed text-zinc-200">
      {parts.map((part, i) => {
        if (part.type === "code") {
          return <CodeBlock key={i} code={part.content} language={part.language} />;
        }

        // Render formatted text with bolding and lists
        const lines = part.content.split("\n");
        return (
          <div key={i} className="space-y-1.5">
            {lines.map((line, lineIdx) => {
              const trimmed = line.trim();
              if (!trimmed) return <div key={lineIdx} className="h-1" />;

              // Headers
              if (trimmed.startsWith("### ")) {
                return (
                  <h4 key={lineIdx} className="font-semibold text-zinc-100 text-sm mt-2 mb-1">
                    {trimmed.replace(/^###\s+/, "")}
                  </h4>
                );
              }
              if (trimmed.startsWith("## ")) {
                return (
                  <h3 key={lineIdx} className="font-bold text-zinc-100 text-sm mt-2.5 mb-1.5 border-b border-zinc-800 pb-1">
                    {trimmed.replace(/^##\s+/, "")}
                  </h3>
              );
              }

              // Bullet points
              const isBullet = trimmed.startsWith("* ") || trimmed.startsWith("- ");
              const content = isBullet ? trimmed.substring(2) : line;

              // Parse inline bolding: **bold** and backticks: `code`
              const formattedContent = content
                .split(/(\*\*.*?\*\*|`.*?`)/g)
                .map((segment, segIdx) => {
                  if (segment.startsWith("**") && segment.endsWith("**")) {
                    return (
                      <strong key={segIdx} className="font-semibold text-zinc-100">
                        {segment.slice(2, -2)}
                      </strong>
                    );
                  }
                  if (segment.startsWith("`") && segment.endsWith("`")) {
                    return (
                      <code
                        key={segIdx}
                        className="px-1 py-0.5 rounded bg-zinc-800/80 text-purple-300 font-mono text-[11px]"
                      >
                        {segment.slice(1, -1)}
                      </code>
                    );
                  }
                  return segment;
                });

              if (isBullet) {
                return (
                  <div key={lineIdx} className="flex items-start gap-2 pl-2">
                    <span className="text-purple-400 mt-1.5">•</span>
                    <span className="flex-1">{formattedContent}</span>
                  </div>
                );
              }

              return <p key={lineIdx}>{formattedContent}</p>;
            })}
          </div>
        );
      })}
    </div>
  );
}

export function AICopilotWorkspace() {
  const { activeWorkspace, activeProject } = useWorkspace();
  const { activeDataset } = useDataset();

  const [inputMessage, setInputMessage] = useState<string>("");
  const [tone, setTone] = useState<string>("ANALYST");
  const [loading, setLoading] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "copilot",
      content:
        "Hello! I am your AI Copilot powered by Google Gemini. I proactively explore your dataset, synthesize multi-engine findings, formulate SQL, generate visualizations, plan dashboards, and orchestrate deterministic analytical workflows.",
    },
  ]);

  const [activePlan, setActivePlan] = useState<DashboardPlan | null>(null);
  const [isExecutingPlan, setIsExecutingPlan] = useState<boolean>(false);
  const [planSuccessMsg, setPlanSuccessMsg] = useState<string | null>(null);

  const handleSend = async (customPrompt?: string) => {
    const textToSend = customPrompt || inputMessage;
    if (!textToSend.trim() || loading || !activeWorkspace?.workspace_id) return;

    const userMsg: Message = { role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    if (!customPrompt) setInputMessage("");
    setLoading(true);

    try {
      const context: CopilotContext = {
        workspace_id: activeWorkspace.workspace_id,
        project_id: activeProject?.project_id,
        dataset_id: activeDataset?.id,
        dataset_version_id: (activeDataset as any)?.version || "v1",
        selected_columns: [],
        selected_metrics: [],
      };

      const response = await sendCopilotChat({
        message: textToSend,
        context,
        tone,
      });

      const copilotMsg: Message = {
        role: "copilot",
        content: response.message,
        responseObj: response,
      };
      setMessages((prev) => [...prev, copilotMsg]);

      if (response.dashboard_plan) {
        setActivePlan(response.dashboard_plan);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "copilot",
          content: `Error: ${err.message || "Unable to process request."}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: "copilot",
        content:
          "Chat cleared. I am ready to assist with your next exploration or dataset analysis.",
      },
    ]);
    setActivePlan(null);
    setPlanSuccessMsg(null);
  };

  const handleApproveStep = async (workflowId: string, stepId: string) => {
    try {
      const updatedWf = await approveWorkflowStep(workflowId, stepId);
      setMessages((prev) => [
        ...prev,
        {
          role: "copilot",
          content: `Approved step '${stepId}'. Workflow resumed and transitioned to status: ${updatedWf.status}.`,
        },
      ]);
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleExecuteDashboard = async () => {
    if (!activePlan || !activeWorkspace?.workspace_id) return;
    try {
      setIsExecutingPlan(true);
      const res = await executeDashboardPlan({
        plan: activePlan,
        workspace_id: activeWorkspace.workspace_id,
        project_id: activeProject?.project_id,
      });
      setPlanSuccessMsg(`Dashboard '${res.title}' created successfully (ID: ${res.dashboard_id})!`);
      setActivePlan(null);
    } catch (err: any) {
      alert(`Dashboard creation error: ${err.message}`);
    } finally {
      setIsExecutingPlan(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-210px)] min-h-[600px] rounded-xl border border-zinc-800 bg-zinc-950/70 overflow-hidden shadow-2xl backdrop-blur-md">
      {/* Copilot Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 border-b border-zinc-800/80 bg-zinc-900/60 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-zinc-200 flex items-center gap-1.5">
            <Bot className="w-4 h-4 text-purple-400" />
            AI Copilot Studio
          </span>
          <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-medium flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-emerald-400" />
            Google Gemini 2.5 Flash
          </span>
          <span className="text-zinc-600">|</span>
          <span className="text-zinc-400 flex items-center gap-1">
            <Database className="w-3 h-3 text-zinc-500" />
            <code className="text-zinc-300 font-mono">{activeDataset?.name || "No active dataset"}</code>
            {activeDataset && (
              <span className="text-zinc-500 font-mono text-[10px]">
                ({(activeDataset as any)?.version || "v1"})
              </span>
            )}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-zinc-400">
            <span>Tone:</span>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-zinc-200 outline-none hover:border-zinc-700 transition-colors"
            >
              <option value="EXECUTIVE">Executive</option>
              <option value="ANALYST">Analyst</option>
              <option value="TECHNICAL">Technical</option>
            </select>
          </div>

          <button
            onClick={handleClearChat}
            title="Clear Chat History"
            className="flex items-center gap-1 px-2 py-1 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-800 transition-colors"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex gap-3 max-w-3xl ${
              m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                m.role === "user"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "bg-purple-600/20 text-purple-400 border border-purple-500/30 shadow-md shadow-purple-500/10"
              }`}
            >
              {m.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`p-4 rounded-xl border space-y-2.5 max-w-2xl ${
                m.role === "user"
                  ? "bg-blue-600/10 border-blue-500/30 text-zinc-100"
                  : "bg-zinc-900/70 border-zinc-800 text-zinc-200 shadow-sm"
              }`}
            >
              <FormattedContent text={m.content} />

              {/* Multi-step Agentic Workflow Progress */}
              {m.responseObj?.workflow && (
                <div className="mt-3 p-3 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-zinc-300">
                    <span className="flex items-center gap-1.5">
                      <Play className="w-3.5 h-3.5 text-purple-400" />
                      Analytical Workflow: {m.responseObj.workflow.goal}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                        m.responseObj.workflow.status === "WAITING_FOR_APPROVAL"
                          ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse"
                          : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      }`}
                    >
                      {m.responseObj.workflow.status}
                    </span>
                  </div>

                  <div className="space-y-1.5 pt-1">
                    {m.responseObj.workflow.steps.map((step) => (
                      <div
                        key={step.step_id}
                        className="flex items-center justify-between p-2 rounded bg-zinc-900/80 border border-zinc-800 text-[11px]"
                      >
                        <div className="flex items-center gap-2">
                          {step.status === "COMPLETED" ? (
                            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                          ) : step.requires_confirmation ? (
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                          ) : (
                            <Clock className="w-3.5 h-3.5 text-zinc-500" />
                          )}
                          <span className="text-zinc-200">{step.title}</span>
                          <span className="font-mono text-[10px] text-zinc-500">({step.tool_id})</span>
                        </div>

                        {step.status === "WAITING_FOR_APPROVAL" && (
                          <button
                            onClick={() =>
                              handleApproveStep(m.responseObj!.workflow!.workflow_id, step.step_id)
                            }
                            className="px-2.5 py-1 rounded bg-amber-500 hover:bg-amber-400 text-black font-semibold text-[10px] transition-colors shadow-sm"
                          >
                            Approve Action
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations Chips */}
              {m.responseObj?.recommendations && m.responseObj.recommendations.length > 0 && (
                <div className="pt-2 border-t border-zinc-800/60 space-y-1.5">
                  <div className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1">
                    <Compass className="w-3 h-3 text-blue-400" />
                    Recommended Next Analyses
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.responseObj.recommendations.map((rec) => (
                      <button
                        key={rec.recommendation_id}
                        onClick={() => handleSend(rec.title)}
                        className="px-2.5 py-1 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/50 text-[11px] transition-colors flex items-center gap-1"
                      >
                        <span>{rec.title}</span>
                        <ArrowRight className="w-2.5 h-2.5 text-purple-400" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Provenance Footer */}
              {m.responseObj?.provenance && (
                <div className="flex items-center gap-3 pt-2 text-[10px] text-zinc-500 font-mono border-t border-zinc-800/40">
                  <span className="text-purple-400/80">Provider: {m.responseObj.provenance.provider}</span>
                  <span>Model: {m.responseObj.provenance.model}</span>
                  <span>ID: {m.responseObj.provenance.ai_generation_id?.slice(0, 10)}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-purple-950/20 border border-purple-500/20 text-zinc-300 text-xs max-w-md">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-400" />
            <span>Consulting Google Gemini, querying governed metrics, and validating grounding...</span>
          </div>
        )}
      </div>

      {/* Active Dashboard Plan Preview Banner */}
      {activePlan && (
        <div className="p-4 border-t border-purple-500/30 bg-purple-950/20 flex items-center justify-between gap-4 text-xs">
          <div className="space-y-1">
            <div className="font-semibold text-purple-300 flex items-center gap-1.5">
              <Layout className="w-4 h-4" />
              Dashboard Plan Ready: {activePlan.title}
            </div>
            <p className="text-zinc-400 text-[11px]">
              Contains {activePlan.components.length} components (KPI cards and chart specifications).
              Requires explicit confirmation before creation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActivePlan(null)}
              className="px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300"
            >
              Dismiss
            </button>
            <button
              onClick={handleExecuteDashboard}
              disabled={isExecutingPlan}
              className="px-3.5 py-1.5 rounded bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-1.5 shadow-lg shadow-purple-900/30 disabled:opacity-50"
            >
              {isExecutingPlan ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <CheckCircle className="w-3.5 h-3.5" />
              )}
              Create Live Dashboard
            </button>
          </div>
        </div>
      )}

      {planSuccessMsg && (
        <div className="p-3 border-t border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-400 flex items-center justify-between">
          <span>{planSuccessMsg}</span>
          <button onClick={() => setPlanSuccessMsg(null)} className="hover:text-emerald-300">
            Dismiss
          </button>
        </div>
      )}

      {/* Quick Prompts Chips */}
      <div className="px-3.5 py-2 border-t border-zinc-800/80 bg-zinc-900/40 flex items-center gap-2 overflow-x-auto text-[11px]">
        <span className="text-zinc-500 shrink-0 font-medium">Suggestions:</span>
        {STARTER_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            disabled={loading}
            onClick={() => handleSend(prompt)}
            className="shrink-0 px-2.5 py-1 rounded-full bg-zinc-800/70 hover:bg-zinc-700/80 text-zinc-300 border border-zinc-700/40 hover:border-purple-500/50 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Prompt Input Box */}
      <div className="p-3.5 border-t border-zinc-800 bg-zinc-900/60">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            placeholder="Ask Gemini to explore distributions, formulate SQL, detect patterns, or build a dashboard..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={loading}
            className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-zinc-200 outline-none focus:border-purple-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !inputMessage.trim()}
            className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-md shadow-purple-900/20"
          >
            <Send className="w-3.5 h-3.5" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
