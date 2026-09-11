"use client";

import React, { useState, useRef } from "react";
import { SendIcon } from "@/components/icons";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask a question about your dataset (e.g. 'What are the top 5 anomalies in revenue?')...",
}: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: "0.5rem",
        backgroundColor: "var(--bg-elevated)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        padding: "0.5rem 0.75rem",
        position: "relative",
      }}
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={text}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? "Connect a dataset to enable the AI Analyst..." : placeholder}
        style={{
          flex: 1,
          backgroundColor: "transparent",
          border: "none",
          outline: "none",
          color: "var(--text-primary)",
          fontSize: "0.875rem",
          lineHeight: 1.4,
          resize: "none",
          maxHeight: "140px",
          fontFamily: "inherit",
          padding: "0.25rem 0",
        }}
      />

      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className={`btn btn-primary btn-sm ${disabled || !text.trim() ? "btn-disabled" : ""}`}
        style={{
          borderRadius: "var(--radius-sm)",
          padding: "0.45rem 0.7rem",
          display: "inline-flex",
        }}
        aria-label="Send query"
      >
        <SendIcon size={14} />
      </button>
    </form>
  );
}
