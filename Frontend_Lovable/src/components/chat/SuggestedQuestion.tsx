import React from "react";
import { AIAnalystIcon } from "@/components/icons";

interface SuggestedQuestionProps {
  question: string;
  onClick: (question: string) => void;
  disabled?: boolean;
}

export function SuggestedQuestion({
  question,
  onClick,
  disabled = false,
}: SuggestedQuestionProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(question)}
      disabled={disabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.45rem",
        padding: "0.45rem 0.85rem",
        backgroundColor: "rgba(255, 255, 255, 0.03)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "9999px",
        fontSize: "0.8125rem",
        color: "var(--text-secondary)",
        cursor: disabled ? "not-allowed" : "pointer",
        textAlign: "left",
        transition: "all 0.15s ease",
        opacity: disabled ? 0.6 : 1,
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.4)";
          e.currentTarget.style.color = "var(--text-primary)";
          e.currentTarget.style.backgroundColor = "rgba(99, 102, 241, 0.08)";
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          e.currentTarget.style.borderColor = "var(--border-subtle)";
          e.currentTarget.style.color = "var(--text-secondary)";
          e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.03)";
        }
      }}
    >
      <span style={{ color: "var(--accent-primary)", display: "flex" }}>
        <AIAnalystIcon size={14} />
      </span>
      <span>{question}</span>
    </button>
  );
}
