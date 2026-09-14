"use client";

import React, { useState } from "react";
import { QueryHistoryItem } from "@/types";
import {
  HistoryIcon,
  PlayIcon,
  SearchIcon,
  TrashIcon,
  CopyIcon,
  CheckIcon,
} from "@/components/icons";

interface QueryHistoryPanelProps {
  history: QueryHistoryItem[];
  onLoadQuery: (sql: string) => void;
  onClearHistory: () => void;
  loading?: boolean;
}

export function QueryHistoryPanel({
  history,
  onLoadQuery,
  onClearHistory,
  loading = false,
}: QueryHistoryPanelProps) {
  const [search, setSearch] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const filtered = history.filter((h) =>
    h.query_text.toLowerCase().includes(search.toLowerCase()) ||
    h.status.toLowerCase().includes(search.toLowerCase())
  );

  const handleCopy = (e: React.MouseEvent, id: string, text: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <span className="badge badge-emerald" style={{ fontSize: "0.625rem" }}>COMPLETED</span>;
      case "FAILED":
        return <span className="badge badge-danger" style={{ fontSize: "0.625rem" }}>FAILED</span>;
      case "TIMEOUT":
        return <span className="badge badge-amber" style={{ fontSize: "0.625rem" }}>TIMEOUT</span>;
      case "CANCELLED":
        return <span className="badge badge-neutral" style={{ fontSize: "0.625rem" }}>CANCELLED</span>;
      default:
        return <span className="badge badge-neutral" style={{ fontSize: "0.625rem" }}>{status}</span>;
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Search & Actions Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.6rem 0.75rem",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          gap: "0.5rem",
        }}
      >
        <div style={{ position: "relative", flex: 1 }}>
          <SearchIcon
            size={13}
            style={{
              position: "absolute",
              left: "0.5rem",
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-muted)",
            }}
          />
          <input
            type="text"
            placeholder="Search execution history..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input input-sm"
            style={{
              paddingLeft: "1.75rem",
              fontSize: "0.75rem",
              width: "100%",
              backgroundColor: "var(--bg-input)",
            }}
          />
        </div>

        {history.length > 0 && (
          <button
            type="button"
            onClick={onClearHistory}
            className="btn btn-ghost btn-sm"
            style={{ fontSize: "0.75rem", color: "var(--color-danger)", padding: "0.25rem 0.5rem" }}
            title="Clear all history"
          >
            <TrashIcon size={13} />
            Clear
          </button>
        )}
      </div>

      {/* History Items List */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0.5rem" }}>
        {loading ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
            <div className="spinner-border spinner-border-sm" style={{ marginBottom: "0.5rem" }} />
            <div style={{ fontSize: "0.8125rem" }}>Loading query history...</div>
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
            <HistoryIcon size={28} style={{ marginBottom: "0.5rem", opacity: 0.5 }} />
            <div style={{ fontWeight: 500, fontSize: "0.875rem" }}>
              {search ? "No matching queries found." : "No queries executed yet."}
            </div>
            <div style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
              Executed queries will be logged with timing, status, and row counts.
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {filtered.map((item) => (
              <div
                key={item.query_id}
                className="card"
                style={{
                  padding: "0.6rem 0.75rem",
                  backgroundColor: "var(--bg-card)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-sm)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
                onClick={() => onLoadQuery(item.query_text)}
                title="Click to load query into editor"
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.35rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    {getStatusBadge(item.status)}
                    <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                      {item.execution_time_ms} ms • {item.row_count} rows
                    </span>
                    <span className="badge badge-neutral" style={{ fontSize: "0.625rem" }}>
                      {item.version_id}
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                    <button
                      type="button"
                      onClick={(e) => handleCopy(e, item.query_id, item.query_text)}
                      className="btn btn-ghost btn-xs"
                      style={{ padding: "0.15rem 0.35rem" }}
                      title="Copy SQL"
                    >
                      {copiedId === item.query_id ? <CheckIcon size={12} color="var(--color-success)" /> : <CopyIcon size={12} />}
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onLoadQuery(item.query_text);
                      }}
                      className="btn btn-secondary btn-xs"
                      style={{ padding: "0.15rem 0.4rem", fontSize: "0.6875rem" }}
                      title="Load into Editor"
                    >
                      <PlayIcon size={10} />
                      Load
                    </button>
                  </div>
                </div>

                <div
                  style={{
                    fontFamily: "var(--font-mono, monospace)",
                    fontSize: "0.75rem",
                    color: "var(--text-primary)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {item.query_text}
                </div>

                {item.error_message && (
                  <div style={{ marginTop: "0.3rem", fontSize: "0.6875rem", color: "var(--color-danger)" }}>
                    Error: {item.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
