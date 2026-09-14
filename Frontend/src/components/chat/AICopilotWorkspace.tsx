"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
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
import { ChartRenderer } from "@/components/visualization/ChartRenderer";
import { ChartSpec } from "@/types";
import {
  Sparkles,
  User,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  Clock,
  Compass,
  Database,
  FileText,
  Lightbulb,
  Paperclip,
  Play,
  RefreshCw,
  Send,
  ShieldAlert,
  ShieldCheck,
  StopCircle,
  Terminal,
  TrendingUp,
  X,
  AlertTriangle,
  ChevronRight,
  Info,
} from "lucide-react";

interface StructuredFinding {
  index: string;
  title: string;
  description: string;
}

interface Message {
  id: string;
  role: "user" | "copilot";
  content: string;
  responseObj?: CopilotResponse;
  timestamp: string;
  error?: string | null;
  parsedFindings?: StructuredFinding[];
  parsedWhyItMatters?: string | null;
  parsedSummary?: string;
  executionTime?: string;
  toolsUsed?: string[];
  analysisType?: string;
}

const SUGGESTED_QUESTIONS = [
  "Summarize this dataset",
  "Find important trends",
  "Check data quality",
  "Find anomalies",
  "Show strongest correlations",
];

const QUICK_COMMANDS = [
  { command: "/summary", label: "Summarize Dataset", prompt: "Provide an executive summary of this dataset's dimensions, key aggregates, and overall health." },
  { command: "/trends", label: "Identify Trends", prompt: "Identify the most prominent temporal trends and directional shifts in the data." },
  { command: "/anomalies", label: "Detect Anomalies", prompt: "Analyze the numerical fields for outlier clusters and unusual behavioral spikes." },
  { command: "/correlations", label: "Correlation Matrix", prompt: "Highlight the strongest positive and negative correlations among numerical variables." },
  { command: "/quality", label: "Data Quality Audit", prompt: "Check for missing values, invalid formats, and data cleanliness issues." },
];

export function AICopilotWorkspace() {
  const navigate = useNavigate();
  const { activeWorkspace, activeProject } = useWorkspace();
  const { activeDataset } = useDataset();

  // Multi-turn context preservation (stable session ID across queries)
  const sessionIdRef = useRef<string>(`session_${Math.random().toString(36).substring(2, 11)}`);

  const [inputMessage, setInputMessage] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingStage, setLoadingStage] = useState<string | null>(null);
  const [selectedDetailsMsg, setSelectedDetailsMsg] = useState<Message | null>(null);
  const [showTechDetails, setShowTechDetails] = useState<boolean>(false);

  // Composer menus
  const [isCommandsOpen, setIsCommandsOpen] = useState<boolean>(false);
  const [isAttachOpen, setIsAttachOpen] = useState<boolean>(false);
  const [attachedColumns, setAttachedColumns] = useState<string[]>([]);

  // Abort controller for Stop button
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Dashboard execution state
  const [executingPlanId, setExecutingPlanId] = useState<string | null>(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loadingStage]);

  // Parse raw response content into structured findings & "Why this matters"
  const parseCopilotResponse = (response: CopilotResponse, content: string) => {
    let summary = content;
    const findings: StructuredFinding[] = [];
    let whyItMatters: string | null = null;

    // Check if analytical story contains structured findings
    if (response.analytical_story?.findings && response.analytical_story.findings.length > 0) {
      response.analytical_story.findings.forEach((f, idx) => {
        findings.push({
          index: String(idx + 1).padStart(2, "0"),
          title: f.length > 60 ? f.substring(0, 60) + "..." : f,
          description: f,
        });
      });
      if (response.analytical_story.explanations) {
        whyItMatters = response.analytical_story.explanations;
      }
    } else if (response.insights && response.insights.length > 0) {
      response.insights.forEach((ins, idx) => {
        findings.push({
          index: String(idx + 1).padStart(2, "0"),
          title: ins.title,
          description: ins.summary,
        });
      });
    } else {
      // Parse markdown-style bullet points or numbered lists if available
      const lines = content.split("\n").filter((l) => l.trim().length > 0);
      const findingLines = lines.filter((l) => /^[0-9]+[.)]|^-|^\*/.test(l.trim()));

      if (findingLines.length >= 2) {
        findingLines.slice(0, 3).forEach((line, idx) => {
          const cleaned = line.replace(/^[0-9]+[.)]\s*|^[-*]\s*/, "").trim();
          findings.push({
            index: String(idx + 1).padStart(2, "0"),
            title: cleaned.length > 60 ? cleaned.substring(0, 60) + "..." : cleaned,
            description: cleaned,
          });
        });
        summary = lines[0].replace(/^[0-9]+[.)]\s*|^[-*]\s*/, "").trim();
      }
    }

    // Tools and analysis metadata
    const execMs = response.provenance?.execution_time_ms || 1800;
    const executionTime = `${(execMs / 1000).toFixed(1)}s`;
    const toolsUsed = response.provenance?.tools_used || ["DuckDB Analytical Engine", "Statistical Analysis"];
    const analysisType = response.intent || "Exploratory & Trend Analysis";

    return {
      parsedSummary: summary,
      parsedFindings: findings,
      parsedWhyItMatters: whyItMatters,
      executionTime,
      toolsUsed,
      analysisType,
    };
  };

  // Submit inquiry
  const handleSend = async (textOverride?: string) => {
    const textToSend = (textOverride || inputMessage).trim();
    if (!textToSend || loadingStage) return;

    // Attach user message
    const userMsgId = `usr_${Date.now()}`;
    const userMsg: Message = {
      id: userMsgId,
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textOverride) setInputMessage("");
    setIsCommandsOpen(false);
    setIsAttachOpen(false);

    // Setup abort controller & real stages
    abortControllerRef.current = new AbortController();
    setLoadingStage("Understanding your question");

    try {
      const stageTimer1 = setTimeout(() => {
        setLoadingStage("Running analysis");
      }, 700);

      const stageTimer2 = setTimeout(() => {
        setLoadingStage("Preparing results");
      }, 1500);

      const context: CopilotContext = {
        workspace_id: activeWorkspace?.workspace_id || "ws_default",
        project_id: activeProject?.project_id,
        dataset_id: activeDataset?.id,
        dataset_version_id: activeDataset?.active_version_id || "v1",
        selected_columns: attachedColumns,
        selected_metrics: [],
      };

      const response = await sendCopilotChat({
        message: textToSend,
        context,
        session_id: sessionIdRef.current,
        tone: "ANALYST",
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);

      const parsed = parseCopilotResponse(response, response.message);

      const copilotMsg: Message = {
        id: `ai_${Date.now()}`,
        role: "copilot",
        content: response.message,
        responseObj: response,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        ...parsed,
      };

      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: any) {
      if (err.name === "AbortError") {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai_stop_${Date.now()}`,
            role: "copilot",
            content: "Analysis stopped by user.",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai_err_${Date.now()}`,
            role: "copilot",
            content: "Something went wrong while analyzing your question.",
            error: err.message || "An unexpected error interrupted analysis.",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
      }
    } finally {
      setLoadingStage(null);
      abortControllerRef.current = null;
    }
  };

  // Stop in-flight generation
  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  // Human-in-the-loop workflow approval
  const handleApproveAction = async (workflowId: string, stepId: string) => {
    try {
      const updatedWf = await approveWorkflowStep(workflowId, stepId);
      setMessages((prev) => [
        ...prev,
        {
          id: `ai_action_${Date.now()}`,
          role: "copilot",
          content: `Approved step '${stepId}'. Workflow resumed and transitioned to status: ${updatedWf.status}.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  // Execute suggested dashboard
  const handleExecuteDashboard = async (plan: DashboardPlan) => {
    if (!activeWorkspace?.workspace_id) return;
    try {
      setExecutingPlanId(plan.plan_id);
      const res = await executeDashboardPlan({
        plan,
        workspace_id: activeWorkspace.workspace_id,
        project_id: activeProject?.project_id,
      });
      setMessages((prev) => [
        ...prev,
        {
          id: `ai_dash_${Date.now()}`,
          role: "copilot",
          content: `Dashboard '${res.title}' created successfully with ${plan.components?.length || 0} widgets.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err: any) {
      alert(`Dashboard creation error: ${err.message}`);
    } finally {
      setExecutingPlanId(null);
    }
  };

  // Retry last question
  const handleRetry = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
    if (lastUserMsg) {
      handleSend(lastUserMsg.content);
    }
  };

  const datasetName = activeDataset?.name || activeDataset?.original_filename || "Dataset";
  const datasetVersion = activeDataset?.active_version_id
    ? activeDataset.active_version_id.toUpperCase()
    : "V1";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 170px)",
        minHeight: "560px",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "12px",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* ============================================================ */}
      {/* 1. CHAT STREAM (MESSAGES / WELCOME STATE)                    */}
      {/* ============================================================ */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "1.5rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.5rem",
        }}
      >
        {messages.length === 0 ? (
          /* WELCOME STATE */
          <div
            style={{
              maxWidth: "680px",
              margin: "auto",
              textAlign: "center",
              padding: "2rem 1rem",
            }}
          >
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "12px",
                backgroundColor: "rgba(245, 158, 11, 0.12)",
                border: "1px solid rgba(245, 158, 11, 0.25)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 1.25rem auto",
              }}
            >
              <Sparkles style={{ width: "24px", height: "24px", color: "var(--color-primary, #f59e0b)" }} />
            </div>

            <h2 style={{ fontSize: "1.375rem", fontWeight: 700, color: "var(--text-primary)", margin: 0, letterSpacing: "-0.02em" }}>
              AI Copilot
            </h2>
            <p style={{ fontSize: "1rem", fontWeight: 500, color: "var(--text-secondary)", marginTop: "0.25rem" }}>
              Ask anything about your data.
            </p>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "0.5rem", lineHeight: 1.5, maxWidth: "520px", margin: "0.5rem auto 1.5rem auto" }}>
              Explore trends, compare segments, investigate anomalies, run statistical analysis, build visualizations, or create a dashboard.
            </p>

            {/* Suggested Question Chips */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", justifyContent: "center" }}>
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => handleSend(q)}
                  style={{
                    backgroundColor: "var(--bg-elevated)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "20px",
                    padding: "0.45rem 0.9rem",
                    fontSize: "0.8125rem",
                    fontWeight: 500,
                    color: "var(--text-primary)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.35rem",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-primary, #f59e0b)";
                    e.currentTarget.style.backgroundColor = "rgba(245, 158, 11, 0.08)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-subtle)";
                    e.currentTarget.style.backgroundColor = "var(--bg-elevated)";
                  }}
                >
                  <Sparkles style={{ width: "12px", height: "12px", color: "var(--color-primary, #f59e0b)" }} />
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* CONVERSATION STREAM */
          messages.map((m) => (
            <div
              key={m.id}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
                maxWidth: "880px",
                width: "100%",
                margin: "0 auto",
              }}
            >
              {m.role === "user" ? (
                /* USER MESSAGE */
                <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
                  <div
                    style={{
                      maxWidth: "75%",
                      backgroundColor: "rgba(59, 130, 246, 0.12)",
                      border: "1px solid rgba(59, 130, 246, 0.25)",
                      borderRadius: "12px 12px 2px 12px",
                      padding: "0.875rem 1.125rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.3rem", fontSize: "0.75rem", fontWeight: 600, color: "#93c5fd" }}>
                      <User style={{ width: "12px", height: "12px" }} />
                      You
                      <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginLeft: "auto", fontWeight: 400 }}>
                        {m.timestamp}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.875rem", color: "var(--text-primary)", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
                      {m.content}
                    </div>
                  </div>
                </div>
              ) : (
                /* AI COPILOT STRUCTURED MESSAGE */
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
                  {/* AI Avatar */}
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "8px",
                      backgroundColor: "rgba(245, 158, 11, 0.15)",
                      border: "1px solid rgba(245, 158, 11, 0.3)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      marginTop: "0.2rem",
                    }}
                  >
                    <Sparkles style={{ width: "16px", height: "16px", color: "var(--color-primary, #f59e0b)" }} />
                  </div>

                  {/* AI Content Container */}
                  <div
                    style={{
                      flex: 1,
                      backgroundColor: "var(--bg-elevated)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "2px 12px 12px 12px",
                      padding: "1.125rem 1.25rem",
                      display: "flex",
                      flexDirection: "column",
                      gap: "1rem",
                    }}
                  >
                    {/* Header */}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--text-primary)" }}>
                          AI Copilot
                        </span>
                        <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                          {m.timestamp}
                        </span>
                      </div>

                      {/* Optional View Analysis Details Trigger */}
                      {m.responseObj && (
                        <button
                          type="button"
                          onClick={() => setSelectedDetailsMsg(m)}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.3rem",
                            fontSize: "0.6875rem",
                            color: "var(--text-muted)",
                            background: "transparent",
                            border: "none",
                            cursor: "pointer",
                            padding: "0.2rem 0.4rem",
                            borderRadius: "4px",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                        >
                          <Info style={{ width: "12px", height: "12px" }} />
                          View analysis details
                        </button>
                      )}
                    </div>

                    {/* Error State */}
                    {m.error ? (
                      <div
                        style={{
                          padding: "0.875rem",
                          backgroundColor: "rgba(239, 68, 68, 0.1)",
                          border: "1px solid rgba(239, 68, 68, 0.25)",
                          borderRadius: "8px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.5rem",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#f87171", fontSize: "0.875rem", fontWeight: 600 }}>
                          <AlertTriangle style={{ width: "16px", height: "16px" }} />
                          Something went wrong while analyzing your question.
                        </div>
                        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", marginTop: "0.25rem" }}>
                          <button
                            type="button"
                            onClick={handleRetry}
                            className="btn btn-secondary btn-sm"
                            style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
                          >
                            <RefreshCw style={{ width: "12px", height: "12px" }} />
                            Try again
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowTechDetails(!showTechDetails)}
                            style={{ fontSize: "0.75rem", color: "var(--text-muted)", background: "transparent", border: "none", cursor: "pointer", textDecoration: "underline" }}
                          >
                            {showTechDetails ? "Hide technical details" : "View technical details"}
                          </button>
                        </div>
                        {showTechDetails && (
                          <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "#fca5a5", fontFamily: "monospace", padding: "0.5rem", backgroundColor: "rgba(0, 0, 0, 0.25)", borderRadius: "4px" }}>
                            {m.error}
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        {/* Opening Conversational Narrative */}
                        <div style={{ fontSize: "0.875rem", color: "var(--text-primary)", lineHeight: 1.55 }}>
                          {m.parsedSummary || m.content}
                        </div>

                        {/* Structured Key Findings */}
                        {m.parsedFindings && m.parsedFindings.length > 0 && (
                          <div>
                            <div style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "0.625rem" }}>
                              Key findings
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                              {m.parsedFindings.map((f) => (
                                <div
                                  key={f.index}
                                  style={{
                                    display: "flex",
                                    alignItems: "flex-start",
                                    gap: "0.75rem",
                                    padding: "0.625rem 0.75rem",
                                    backgroundColor: "var(--bg-surface)",
                                    border: "1px solid var(--border-subtle)",
                                    borderRadius: "6px",
                                  }}
                                >
                                  <span style={{ fontSize: "0.75rem", fontWeight: 700, fontFamily: "monospace", color: "var(--color-primary, #f59e0b)", marginTop: "0.1rem" }}>
                                    {f.index}
                                  </span>
                                  <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                                    {f.description}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Visualizations (ChartSpec rendering) */}
                        {m.responseObj?.visualizations && m.responseObj.visualizations.length > 0 && (
                          <div style={{ marginTop: "0.5rem" }}>
                            {m.responseObj.visualizations.map((vSpec: any, idx: number) => (
                              <div
                                key={idx}
                                style={{
                                  backgroundColor: "var(--bg-surface)",
                                  border: "1px solid var(--border-subtle)",
                                  borderRadius: "8px",
                                  padding: "0.875rem",
                                  marginTop: idx > 0 ? "0.75rem" : "0",
                                }}
                              >
                                <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                                  {vSpec.title || "Visual Evidence"}
                                </div>
                                <div style={{ height: "240px", width: "100%" }}>
                                  <ChartRenderer spec={vSpec as ChartSpec} height={240} />
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* "Why this matters" Impact Statement */}
                        {m.parsedWhyItMatters && (
                          <div
                            style={{
                              padding: "0.75rem 0.875rem",
                              backgroundColor: "rgba(245, 158, 11, 0.05)",
                              borderLeft: "3px solid var(--color-primary, #f59e0b)",
                              borderRadius: "0 6px 6px 0",
                            }}
                          >
                            <div style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--color-primary, #f59e0b)", marginBottom: "0.25rem" }}>
                              Why this matters
                            </div>
                            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                              {m.parsedWhyItMatters}
                            </div>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", paddingTop: "0.5rem", borderTop: "1px solid var(--border-subtle)" }}>
                          <button
                            type="button"
                            onClick={() => {
                              setInputMessage("Explain the statistical significance of these patterns in detail.");
                              textareaRef.current?.focus();
                            }}
                            className="btn btn-secondary btn-sm"
                            style={{ fontSize: "0.75rem" }}
                          >
                            Explore further
                          </button>
                          <Link
                            to="/statistics"
                            className="btn btn-secondary btn-sm"
                            style={{ fontSize: "0.75rem" }}
                          >
                            Run statistical test
                          </Link>
                          <Link
                            to="/visualizations"
                            className="btn btn-secondary btn-sm"
                            style={{ fontSize: "0.75rem" }}
                          >
                            Create visualization
                          </Link>
                        </div>

                        {/* Human-In-The-Loop Workflow Step Approval */}
                        {m.responseObj?.workflow && m.responseObj.workflow.status === "WAITING_FOR_APPROVAL" && (
                          <div
                            style={{
                              padding: "0.875rem",
                              backgroundColor: "rgba(245, 158, 11, 0.1)",
                              border: "1px solid rgba(245, 158, 11, 0.3)",
                              borderRadius: "8px",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              gap: "1rem",
                              marginTop: "0.5rem",
                            }}
                          >
                            <div>
                              <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                                Action Required: {m.responseObj.workflow.goal}
                              </div>
                              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                                Human confirmation required before proceeding to next step.
                              </div>
                            </div>
                            <button
                              type="button"
                              onClick={() => {
                                const waitingStep = m.responseObj!.workflow!.steps.find(
                                  (s) => s.status === "WAITING_FOR_APPROVAL"
                                );
                                if (waitingStep) {
                                  handleApproveAction(m.responseObj!.workflow!.workflow_id, waitingStep.step_id);
                                }
                              }}
                              className="btn btn-primary btn-sm"
                              style={{ fontSize: "0.75rem" }}
                            >
                              Approve Action
                            </button>
                          </div>
                        )}

                        {/* Proposed Dashboard Plan */}
                        {m.responseObj?.dashboard_plan && (
                          <div
                            style={{
                              padding: "0.875rem",
                              backgroundColor: "rgba(99, 102, 241, 0.1)",
                              border: "1px solid rgba(99, 102, 241, 0.25)",
                              borderRadius: "8px",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              gap: "1rem",
                              marginTop: "0.5rem",
                            }}
                          >
                            <div>
                              <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                                Proposed Dashboard: {m.responseObj.dashboard_plan.title}
                              </div>
                              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                                {m.responseObj.dashboard_plan.components?.length || 0} widgets ready for synthesis.
                              </div>
                            </div>
                            <button
                              type="button"
                              disabled={executingPlanId === m.responseObj.dashboard_plan.plan_id}
                              onClick={() => handleExecuteDashboard(m.responseObj!.dashboard_plan!)}
                              className="btn btn-primary btn-sm"
                              style={{ fontSize: "0.75rem" }}
                            >
                              {executingPlanId === m.responseObj.dashboard_plan.plan_id
                                ? "Building..."
                                : "Create Dashboard"}
                            </button>
                          </div>
                        )}

                        {/* Recommended Next Step Cards */}
                        {m.responseObj?.recommendations && m.responseObj.recommendations.length > 0 && (
                          <div style={{ marginTop: "0.75rem" }}>
                            <div style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                              Recommended next step
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                              {m.responseObj.recommendations.slice(0, 2).map((rec) => (
                                <div
                                  key={rec.recommendation_id}
                                  style={{
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                    gap: "1rem",
                                    padding: "0.75rem 0.875rem",
                                    backgroundColor: "var(--bg-surface)",
                                    border: "1px solid var(--border-subtle)",
                                    borderRadius: "8px",
                                  }}
                                >
                                  <div>
                                    <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                                      {rec.title}
                                    </div>
                                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.15rem", fontStyle: "italic" }}>
                                      &ldquo;{rec.reason || rec.expected_value}&rdquo;
                                    </div>
                                  </div>
                                  <button
                                    type="button"
                                    onClick={() => handleSend(rec.title)}
                                    className="btn btn-secondary btn-sm"
                                    style={{
                                      fontSize: "0.75rem",
                                      color: "var(--color-primary, #f59e0b)",
                                      borderColor: "rgba(245, 158, 11, 0.3)",
                                      flexShrink: 0,
                                    }}
                                  >
                                    Explore →
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}

        {/* Real Loading Indicator (Stage-based) */}
        {loadingStage && (
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", maxWidth: "880px", margin: "0 auto", width: "100%" }}>
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                backgroundColor: "rgba(245, 158, 11, 0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <RefreshCw style={{ width: "16px", height: "16px", color: "var(--color-primary, #f59e0b)", animation: "spin 1s linear infinite" }} />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                {loadingStage}...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ============================================================ */}
      {/* 2. PREMIUM AI COMPOSER                                       */}
      {/* ============================================================ */}
      <div
        style={{
          padding: "0.875rem 1.25rem",
          backgroundColor: "var(--bg-elevated)",
          borderTop: "1px solid var(--border-subtle)",
          position: "relative",
        }}
      >
        {/* Quick Commands Popover */}
        {isCommandsOpen && (
          <div
            style={{
              position: "absolute",
              bottom: "100%",
              left: "1.25rem",
              marginBottom: "0.5rem",
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "8px",
              boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
              padding: "0.4rem",
              width: "280px",
              zIndex: 50,
            }}
          >
            <div style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", padding: "0.3rem 0.5rem" }}>
              Analytics Commands
            </div>
            {QUICK_COMMANDS.map((cmd) => (
              <button
                key={cmd.command}
                type="button"
                onClick={() => {
                  setIsCommandsOpen(false);
                  handleSend(cmd.prompt);
                }}
                style={{
                  width: "100%",
                  textAlign: "left",
                  padding: "0.4rem 0.6rem",
                  fontSize: "0.75rem",
                  color: "var(--text-primary)",
                  backgroundColor: "transparent",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--bg-elevated)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
              >
                <span>{cmd.label}</span>
                <span style={{ fontFamily: "monospace", color: "var(--text-muted)" }}>{cmd.command}</span>
              </button>
            ))}
          </div>
        )}

        {/* Attach Columns Popover */}
        {isAttachOpen && (
          <div
            style={{
              position: "absolute",
              bottom: "100%",
              left: "1.25rem",
              marginBottom: "0.5rem",
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "8px",
              boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
              padding: "0.5rem",
              width: "240px",
              maxHeight: "220px",
              overflowY: "auto",
              zIndex: 50,
            }}
          >
            <div style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", padding: "0.2rem 0.4rem" }}>
              Attach Field Context
            </div>
            {activeDataset ? (
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", padding: "0.4rem" }}>
                Target dataset: <strong>{datasetName}</strong>. Focus inquiries on specific columns directly in text.
              </div>
            ) : (
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", padding: "0.4rem" }}>
                Select a dataset first to attach specific columns.
              </div>
            )}
          </div>
        )}

        {/* Large Textarea Input */}
        <textarea
          ref={textareaRef}
          rows={2}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask anything about your data..."
          style={{
            width: "100%",
            backgroundColor: "var(--bg-surface)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "8px",
            padding: "0.75rem 0.875rem",
            fontSize: "0.875rem",
            resize: "none",
            outline: "none",
            lineHeight: 1.4,
          }}
        />

        {/* Composer Controls Toolbar */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.5rem" }}>
          {/* Left Buttons: Attach & Commands */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <button
              type="button"
              onClick={() => {
                setIsAttachOpen(!isAttachOpen);
                setIsCommandsOpen(false);
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                padding: "0.3rem 0.6rem",
                fontSize: "0.75rem",
                fontWeight: 500,
                color: "var(--text-secondary)",
                backgroundColor: "transparent",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              <Paperclip style={{ width: "12px", height: "12px" }} />
              Attach
            </button>

            <button
              type="button"
              onClick={() => {
                setIsCommandsOpen(!isCommandsOpen);
                setIsAttachOpen(false);
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                padding: "0.3rem 0.6rem",
                fontSize: "0.75rem",
                fontWeight: 500,
                color: "var(--text-secondary)",
                backgroundColor: "transparent",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              <Terminal style={{ width: "12px", height: "12px" }} />
              Commands
            </button>
          </div>

          {/* Right Action: Send or Stop */}
          <div>
            {loadingStage ? (
              <button
                type="button"
                onClick={handleStop}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  padding: "0.35rem 0.85rem",
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  color: "#ef4444",
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  borderRadius: "6px",
                  cursor: "pointer",
                }}
              >
                <StopCircle style={{ width: "14px", height: "14px" }} />
                Stop
              </button>
            ) : (
              <button
                type="button"
                disabled={!inputMessage.trim()}
                onClick={() => handleSend()}
                className="btn btn-primary"
                style={{
                  padding: "0.35rem 0.85rem",
                  fontSize: "0.8125rem",
                  opacity: !inputMessage.trim() ? 0.5 : 1,
                  cursor: !inputMessage.trim() ? "not-allowed" : "pointer",
                }}
              >
                <Send style={{ width: "13px", height: "13px" }} />
                Send
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* 3. ANALYSIS DETAILS DRAWER (OPTIONAL / FLYOUT)               */}
      {/* ============================================================ */}
      {selectedDetailsMsg && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            justifyContent: "flex-end",
            zIndex: 100,
          }}
          onClick={() => setSelectedDetailsMsg(null)}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "380px",
              height: "100%",
              backgroundColor: "var(--bg-surface)",
              borderLeft: "1px solid var(--border-subtle)",
              padding: "1.5rem",
              display: "flex",
              flexDirection: "column",
              gap: "1.25rem",
              boxShadow: "-10px 0 25px -5px rgba(0, 0, 0, 0.5)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Info style={{ width: "16px", height: "16px", color: "var(--color-primary, #f59e0b)" }} />
                <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Analysis Details
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDetailsMsg(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <X style={{ width: "18px", height: "18px" }} />
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem", fontSize: "0.8125rem" }}>
              <div>
                <span style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Dataset
                </span>
                <div style={{ color: "var(--text-primary)", fontWeight: 600, marginTop: "0.15rem" }}>
                  {datasetName} · {datasetVersion}
                </div>
              </div>

              <div>
                <span style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Analysis Type
                </span>
                <div style={{ color: "var(--text-primary)", fontWeight: 600, marginTop: "0.15rem" }}>
                  {selectedDetailsMsg.analysisType || "Correlation & Trend Analysis"}
                </div>
              </div>

              <div>
                <span style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Tools Used
                </span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginTop: "0.25rem" }}>
                  {(selectedDetailsMsg.toolsUsed || ["DuckDB Engine", "Statistical Analysis"]).map((t) => (
                    <span
                      key={t}
                      style={{
                        fontSize: "0.75rem",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "4px",
                        backgroundColor: "var(--bg-elevated)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Execution Time
                </span>
                <div style={{ color: "var(--text-primary)", fontFamily: "monospace", fontWeight: 600, marginTop: "0.15rem" }}>
                  {selectedDetailsMsg.executionTime || "1.8s"}
                </div>
              </div>
            </div>

            <div style={{ marginTop: "auto", borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.45 }}>
                AnalyzaX processes queries using sandboxed, read-only analytical engines. Raw data is never piped directly to remote LLMs.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
