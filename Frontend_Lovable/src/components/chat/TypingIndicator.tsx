import React from "react";

export function TypingIndicator() {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "0.6rem 0.9rem",
        backgroundColor: "var(--bg-elevated)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border-subtle)",
        width: "fit-content",
      }}
    >
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          backgroundColor: "var(--accent-primary)",
          animation: "shimmer 1.2s infinite ease-in-out",
        }}
      />
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          backgroundColor: "var(--accent-primary)",
          animation: "shimmer 1.2s infinite ease-in-out 0.2s",
        }}
      />
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          backgroundColor: "var(--accent-primary)",
          animation: "shimmer 1.2s infinite ease-in-out 0.4s",
        }}
      />
      <span
        style={{
          fontSize: "0.75rem",
          color: "var(--text-muted)",
          marginLeft: "0.35rem",
          fontWeight: 500,
        }}
      >
        Analyst reasoning…
      </span>
    </div>
  );
}
