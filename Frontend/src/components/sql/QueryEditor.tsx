"use client";

import React, { useState } from "react";
import { PlayIcon, RefreshIcon } from "@/components/icons";

interface QueryEditorProps {
  initialQuery?: string;
  onRunQuery?: (query: string) => void;
  disabled?: boolean;
}

const TEMPLATES = [
  { label: "Preview Table", sql: "SELECT * FROM current_dataset LIMIT 10;" },
  { label: "Summarize Stats", sql: "SUMMARIZE current_dataset;" },
  { label: "Column Counts", sql: "SELECT count(*) AS total_records FROM current_dataset;" },
];

export function QueryEditor({
  initialQuery = "SELECT * FROM current_dataset LIMIT 10;",
  onRunQuery,
  disabled = false,
}: QueryEditorProps) {
  const [query, setQuery] = useState(initialQuery);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!disabled && query.trim()) {
        onRunQuery?.(query);
      }
    }
  };

  return (
    <div className="card" style={{ padding: "1rem" }}>
      {/* Action Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "0.75rem",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              textTransform: "uppercase",
              color: "var(--text-muted)",
              letterSpacing: "0.05em",
            }}
          >
            DuckDB SQL Editor
          </span>
          <span className="badge badge-indigo" style={{ fontSize: "0.625rem" }}>
            In-Memory OLAP
          </span>
        </div>

        {/* Quick Templates */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Templates:
          </span>
          {TEMPLATES.map((tmpl) => (
            <button
              key={tmpl.label}
              type="button"
              onClick={() => setQuery(tmpl.sql)}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.6875rem", padding: "0.2rem 0.5rem" }}
            >
              {tmpl.label}
            </button>
          ))}
        </div>
      </div>

      {/* Code Textarea Area */}
      <div
        style={{
          position: "relative",
          backgroundColor: "var(--bg-input)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-sm)",
          overflow: "hidden",
        }}
      >
        <textarea
          rows={6}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          spellCheck={false}
          disabled={disabled}
          placeholder="Enter SQL query (e.g. SELECT * FROM current_dataset)..."
          style={{
            width: "100%",
            backgroundColor: "transparent",
            border: "none",
            outline: "none",
            color: "#e2e8f0",
            fontFamily: "var(--font-mono)",
            fontSize: "0.875rem",
            lineHeight: 1.6,
            padding: "0.85rem 1rem",
            resize: "vertical",
          }}
        />
      </div>

      {/* Editor Footer / Run Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: "0.75rem",
          paddingTop: "0.5rem",
          borderTop: "1px solid var(--border-subtle)",
        }}
      >
        <span
          style={{
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            gap: "0.25rem",
          }}
        >
          Press <kbd style={{ backgroundColor: "rgba(255,255,255,0.08)", padding: "1px 5px", borderRadius: "3px" }}>Ctrl</kbd> + <kbd style={{ backgroundColor: "rgba(255,255,255,0.08)", padding: "1px 5px", borderRadius: "3px" }}>Enter</kbd> to execute
        </span>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={() => setQuery("")}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
          >
            <RefreshIcon size={13} />
            <span>Clear</span>
          </button>

          <button
            type="button"
            onClick={() => onRunQuery?.(query)}
            disabled={disabled || !query.trim()}
            className={`btn btn-primary btn-sm ${disabled || !query.trim() ? "btn-disabled" : ""}`}
            style={{ fontSize: "0.75rem", gap: "0.4rem" }}
          >
            <PlayIcon size={13} />
            <span>Run Query</span>
          </button>
        </div>
      </div>
    </div>
  );
}
