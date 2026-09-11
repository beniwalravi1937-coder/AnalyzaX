import React from "react";
import { AlertCircleIcon, RefreshIcon } from "@/components/icons";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message = "An unexpected error occurred while processing this analytical workspace. Please check your connection or try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      style={{
        backgroundColor: "rgba(244, 63, 94, 0.05)",
        border: "1px solid rgba(244, 63, 94, 0.2)",
        borderRadius: "var(--radius-md)",
        padding: "2rem",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        textAlign: "center",
        gap: "1rem",
        maxWidth: "540px",
        margin: "2rem auto",
      }}
    >
      <div
        style={{
          width: "42px",
          height: "42px",
          borderRadius: "50%",
          backgroundColor: "rgba(244, 63, 94, 0.12)",
          color: "var(--accent-rose)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <AlertCircleIcon size={22} />
      </div>

      <div>
        <h4
          style={{
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--text-primary)",
            marginBottom: "0.25rem",
          }}
        >
          {title}
        </h4>
        <p
          style={{
            fontSize: "0.875rem",
            color: "var(--text-secondary)",
            lineHeight: 1.5,
          }}
        >
          {message}
        </p>
      </div>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="btn btn-secondary btn-sm"
          style={{ gap: "0.4rem" }}
        >
          <RefreshIcon size={14} />
          <span>Retry Operation</span>
        </button>
      )}
    </div>
  );
}
