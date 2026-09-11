"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDataset } from "@/context/DatasetContext";
import {
  CopilotContext,
  CopilotResponse,
  DashboardPlan,
  NextAnalysisRecommendation,
} from "@/types/copilot";
import {
  approveWorkflowStep,
  cancelWorkflow,
  executeDashboardPlan,
  sendCopilotChat,
} from "@/services/copilotApi";
import {
  AlertTriangle,
  ArrowRight,
  BarChart2,
  Bot,
  CheckCircle,
  Clock,
  Compass,
  FileText,
  HelpCircle,
  Layout,
  Play,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  User,
  XCircle,
} from "lucide-react";

interface Message {
  role: "user" | "copilot";
  content: string;
  responseObj?: CopilotResponse;
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
        "Hello! I am your AI Copilot. I proactively discover signals across your dataset, synthesize multi-engine findings, plan dashboards, and orchestrate safe analytical workflows.",
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
    <div className="flex flex-col h-[calc(100vh-210px)] min-h-[600px] rounded-xl border border-zinc-800 bg-zinc-950/60 overflow-hidden">
      {/* Copilot Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 border-b border-zinc-800 bg-zinc-900/60 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-zinc-300 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-purple-400" />
            AI Copilot Mode
          </span>
          <span className="text-zinc-600">|</span>
          <span className="text-zinc-400">
            Scope: <code className="text-zinc-300">{activeWorkspace?.name || "Workspace"}</code>
            {activeDataset && (
              <>
                {" "}
                / <code className="text-zinc-300">{activeDataset.name}</code> (
                {(activeDataset as any)?.version || "v1"})
              </>
            )}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-zinc-400">
            <span>Tone:</span>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-zinc-200 outline-none"
            >
              <option value="EXECUTIVE">Executive</option>
              <option value="ANALYST">Analyst</option>
              <option value="TECHNICAL">Technical</option>
            </select>
          </div>
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
                  ? "bg-blue-600 text-white"
                  : "bg-purple-600/20 text-purple-400 border border-purple-500/30"
              }`}
            >
              {m.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`p-3.5 rounded-xl border space-y-2.5 ${
                m.role === "user"
                  ? "bg-blue-600/10 border-blue-500/30 text-zinc-100"
                  : "bg-zinc-900/60 border-zinc-800 text-zinc-200"
              }`}
            >
              <p className="leading-relaxed whitespace-pre-line">{m.content}</p>

              {/* Multi-step Agentic Workflow Progress */}
              {m.responseObj?.workflow && (
                <div className="mt-3 p-3 rounded-lg bg-zinc-950/70 border border-zinc-800 space-y-2">
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
                            className="px-2 py-0.5 rounded bg-amber-500 hover:bg-amber-400 text-black font-semibold text-[10px] transition-colors"
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
                        className="px-2.5 py-1 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/50 text-[11px] transition-colors flex items-center gap-1"
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
                <div className="flex items-center gap-3 pt-2 text-[10px] text-zinc-500 font-mono">
                  <span>Provider: {m.responseObj.provenance.provider}</span>
                  <span>Model: {m.responseObj.provenance.model}</span>
                  <span>Template: {m.responseObj.provenance.prompt_template_version}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-zinc-400 text-xs italic">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-400" />
            Analyzing telemetry, querying governed metrics, and verifying evidence...
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
            placeholder="Ask a question, request an investigation ('Why did revenue drop?'), or ask to build a dashboard..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={loading}
            className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-zinc-200 outline-none focus:border-purple-500"
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

