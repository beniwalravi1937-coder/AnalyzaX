"use client";

import React from "react";
import { AnalystMessage } from "@/types/ai_analyst";
import { AIAnalystIcon } from "@/components/icons";
import { ToolExecutionIndicator } from "./ToolExecutionIndicator";
import { CleaningConfirmationCard } from "./CleaningConfirmationCard";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";

interface ChatMessageProps {
  message: AnalystMessage;
  sessionId: string;
  onSelectSuggestion?: (question: string) => void;
  onCleaningApplied?: (newVersionId: string) => void;
}

export function ChatMessage({
  message,
  sessionId,
  onSelectSuggestion,
  onCleaningApplied,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        marginBottom: "1.5rem",
        width: "100%",
      }}
    >
      {/* Header Info */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.4rem",
          marginBottom: "0.35rem",
          fontSize: "0.75rem",
          color: "var(--text-muted)",
        }}
      >
        {!isUser && (
          <span style={{ color: "var(--accent-primary, #6366f1)", display: "flex" }}>
            <AIAnalystIcon size={14} />
          </span>
        )}
        <span style={{ fontWeight: 600 }}>{isUser ? "You" : "AnalyzaX AI Analyst"}</span>
        <span>&bull;</span>
        <span>
          {message.created_at
            ? new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            : "Just now"}
        </span>
      </div>

      {/* Message Card */}
      <div
        style={{
          maxWidth: "85%",
          backgroundColor: isUser ? "rgba(99, 102, 241, 0.15)" : "var(--bg-elevated, rgba(30, 41, 59, 0.7))",
          border: `1px solid ${
            isUser ? "rgba(99, 102, 241, 0.35)" : "var(--border-subtle, rgba(255, 255, 255, 0.1))"
          }`,
          borderRadius: "var(--radius-md, 0.5rem)",
          padding: "1rem 1.25rem",
          fontSize: "0.9rem",
          color: "var(--text-primary)",
          lineHeight: 1.65,
          wordBreak: "break-word",
          boxShadow: isUser ? "0 2px 8px rgba(99, 102, 241, 0.1)" : "0 4px 12px rgba(0, 0, 0, 0.15)",
        }}
      >
        {/* Tool Execution Drawer ("How I analyzed this") */}
        {message.tool_results && message.tool_results.length > 0 && (
          <ToolExecutionIndicator toolResults={message.tool_results} />
        )}

        {/* Cleaning Proposal Confirmation Card */}
        {message.cleaning_proposal && (
          <CleaningConfirmationCard
            proposal={message.cleaning_proposal}
            sessionId={sessionId}
            onApplied={onCleaningApplied}
          />
        )}

        {/* Main Formatted Text */}
        <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>

        {/* Embedded Visualizations */}
        {message.visualizations && message.visualizations.length > 0 && (
          <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
            {message.visualizations.map((chartSpec: any, idx: number) => (
              <div
                key={chartSpec.id || idx}
                style={{
                  background: "rgba(0, 0, 0, 0.25)",
                  border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.1))",
                  borderRadius: "0.5rem",
                  padding: "0.75rem",
                }}
              >
                <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.5rem", color: "var(--text-primary)" }}>
                  📊 {chartSpec.title || "Visualization"}
                </div>
                <ChartRenderer spec={chartSpec} height={320} />
              </div>
            ))}
          </div>
        )}

        {/* Provenance / Citations */}
        {message.citations && message.citations.length > 0 && (
          <div
            style={{
              marginTop: "0.85rem",
              paddingTop: "0.5rem",
              borderTop: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              display: "flex",
              flexWrap: "wrap",
              gap: "0.5rem",
            }}
          >
            <span style={{ fontWeight: 600 }}>Evidence:</span>
            {message.citations.map((c, i) => (
              <span
                key={c.reference_id || i}
                style={{
                  padding: "0.15rem 0.4rem",
                  background: "rgba(255, 255, 255, 0.05)",
                  borderRadius: "0.25rem",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                }}
              >
                [{c.tool_id} #{c.result_id ? c.result_id.slice(-6) : i + 1}]
              </span>
            ))}
          </div>
        )}

        {/* Suggested Next Steps / Follow-ups */}
        {message.follow_up_questions && message.follow_up_questions.length > 0 && onSelectSuggestion && (
          <div
            style={{
              marginTop: "1rem",
              paddingTop: "0.75rem",
              borderTop: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
            }}
          >
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.4rem" }}>
              Suggested Next Actions:
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {message.follow_up_questions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => onSelectSuggestion(q)}
                  style={{
                    background: "rgba(99, 102, 241, 0.1)",
                    border: "1px solid rgba(99, 102, 241, 0.3)",
                    borderRadius: "1rem",
                    padding: "0.25rem 0.75rem",
                    fontSize: "0.8rem",
                    color: "var(--accent-primary, #6366f1)",
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  {q} →
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
