"use client";

import React, { useEffect, useRef, useState } from "react";
import { AnalystMessage, AnalystSession } from "@/types/ai_analyst";
import { DatasetResponse } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
import { EmptyState } from "@/components/ui/EmptyState";
import { AIAnalystIcon } from "@/components/icons";
import {
  createAnalystSession,
  getAnalystSession,
  sendChatMessage,
} from "@/services/aiAnalystApi";

interface ChatWindowProps {
  activeSessionId?: string;
  datasets: DatasetResponse[];
  activeDatasetId?: string;
  activeVersionId?: string;
  onDatasetChange?: (datasetId: string) => void;
  onSessionChange?: (sessionId: string) => void;
}

const DEFAULT_SUGGESTIONS = [
  "What columns and statistics are in this dataset?",
  "Is my data clean and are there any missing values?",
  "What is the average revenue and summary distribution?",
  "Is revenue significantly different across categories?",
  "Build a machine learning model to predict target",
  "Forecast revenue for the next 6 months",
  "Remove duplicate records from this table",
];

export function ChatWindow({
  activeSessionId,
  datasets,
  activeDatasetId,
  activeVersionId,
  onDatasetChange,
  onSessionChange,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<AnalystMessage[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(activeSessionId);
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Sync session prop
  useEffect(() => {
    if (activeSessionId && activeSessionId !== currentSessionId) {
      setCurrentSessionId(activeSessionId);
      loadSession(activeSessionId);
    }
  }, [activeSessionId]);

  const loadSession = async (sessId: string) => {
    try {
      const sess = await getAnalystSession(sessId);
      setMessages(sess.messages || []);
    } catch (err: any) {
      setError(err.message || "Failed to load session messages.");
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isThinking]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    setError(null);

    // Optimistic user message
    const userMsg: AnalystMessage = {
      message_id: `msg_${Date.now()}`,
      role: "user",
      content: text,
      tool_calls: [],
      tool_results: [],
      visualizations: [],
      citations: [],
      warnings: [],
      limitations: [],
      follow_up_questions: [],
      provenance: {},
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);

    try {
      const resp = await sendChatMessage({
        session_id: currentSessionId,
        dataset_id: activeDatasetId,
        dataset_version_id: activeVersionId,
        message: text,
      });

      if (!currentSessionId && resp.session_id) {
        setCurrentSessionId(resp.session_id);
        if (onSessionChange) {
          onSessionChange(resp.session_id);
        }
      }

      const assistantMsg: AnalystMessage = {
        message_id: resp.response_id,
        role: "assistant",
        content: resp.message,
        intent: resp.intent,
        plan: resp.plan,
        tool_calls: resp.tool_calls,
        tool_results: resp.tool_results,
        visualizations: resp.visualizations,
        citations: resp.citations,
        cleaning_proposal: resp.cleaning_proposal,
        warnings: resp.warnings,
        limitations: resp.limitations,
        follow_up_questions: resp.follow_up_questions,
        provenance: resp.provenance,
        created_at: resp.created_at,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || "Failed to process inquiry.");
      const errorMsg: AnalystMessage = {
        message_id: `msg_err_${Date.now()}`,
        role: "assistant",
        content: `Error: ${err.message || "Analytical engine encountered an error."}`,
        tool_calls: [],
        tool_results: [],
        visualizations: [],
        citations: [],
        warnings: ["Request execution failed."],
        limitations: [],
        follow_up_questions: [],
        provenance: {},
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        height: "calc(100vh - 200px)",
        minHeight: "560px",
        padding: "1.25rem",
        background: "var(--bg-surface, #0f172a)",
      }}
    >
      {/* Top Context Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingBottom: "0.75rem",
          marginBottom: "0.75rem",
          borderBottom: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
          fontSize: "0.85rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ color: "var(--text-muted)" }}>Active Dataset:</span>
          <select
            value={activeDatasetId || ""}
            onChange={(e) => onDatasetChange && onDatasetChange(e.target.value)}
            style={{
              padding: "0.3rem 0.6rem",
              background: "rgba(0, 0, 0, 0.3)",
              border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.1))",
              borderRadius: "0.375rem",
              color: "var(--text-primary)",
              fontSize: "0.85rem",
            }}
          >
            <option value="">Select a dataset...</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.format.toUpperCase()})
              </option>
            ))}
          </select>
          {activeVersionId && (
            <span
              style={{
                padding: "0.15rem 0.5rem",
                background: "rgba(99, 102, 241, 0.15)",
                border: "1px solid rgba(99, 102, 241, 0.3)",
                borderRadius: "0.25rem",
                fontSize: "0.75rem",
                color: "var(--accent-primary, #6366f1)",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {activeVersionId}
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)", fontSize: "0.75rem" }}>
          <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
          <span>Engines Ready</span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          paddingRight: "0.5rem",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {messages.length === 0 ? (
          <div style={{ margin: "auto", width: "100%", maxWidth: "600px", padding: "1.5rem 0" }}>
            <EmptyState
              icon={<AIAnalystIcon size={28} />}
              title="AnalyzaX AI Data Analyst"
              description="Ask natural-language questions about your dataset. The AI Analyst translates intent into deterministic analytical engine calls across Profiling, Quality, SQL, Statistics, ML, Forecasting, and Visualizations."
            />

            {/* Suggested Starter Questions */}
            <div style={{ marginTop: "1.5rem" }}>
              <p
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  color: "var(--text-muted)",
                  letterSpacing: "0.05em",
                  marginBottom: "0.6rem",
                }}
              >
                Suggested Analytical Inquiries
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                {DEFAULT_SUGGESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    style={{
                      padding: "0.6rem 0.85rem",
                      background: "rgba(255, 255, 255, 0.03)",
                      border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
                      borderRadius: "0.375rem",
                      color: "var(--text-secondary)",
                      fontSize: "0.85rem",
                      textAlign: "left",
                      cursor: "pointer",
                      transition: "all 0.15s",
                    }}
                  >
                    💬 {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.message_id}
              message={msg}
              sessionId={currentSessionId || ""}
              onSelectSuggestion={handleSend}
            />
          ))
        )}

        {isThinking && (
          <div style={{ padding: "0.5rem 0", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <TypingIndicator />
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Analyzing dataset & orchestrating analytical engines...
            </span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div style={{ marginTop: "0.75rem" }}>
        <ChatInput onSend={handleSend} disabled={isThinking} />
      </div>
    </div>
  );
}
