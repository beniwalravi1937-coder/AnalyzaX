"use client";

import React from "react";
import { AnalystSession } from "@/types/ai_analyst";
import { TrashIcon, PlusIcon } from "@/components/icons";

interface SessionSidebarProps {
  sessions: AnalystSession[];
  activeSessionId?: string;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export function SessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}: SessionSidebarProps) {
  return (
    <div
      style={{
        width: "280px",
        minWidth: "240px",
        borderRight: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        padding: "1rem",
        background: "rgba(0, 0, 0, 0.15)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>Conversations</h3>
        <button
          onClick={onNewSession}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.3rem",
            padding: "0.35rem 0.65rem",
            background: "var(--accent-primary, #6366f1)",
            color: "#fff",
            border: "none",
            borderRadius: "0.375rem",
            fontSize: "0.75rem",
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          <PlusIcon size={12} />
          New
        </button>
      </div>

      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
        {sessions.length === 0 ? (
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", textAlign: "center", marginTop: "2rem" }}>
            No conversations yet.
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.session_id === activeSessionId;
            return (
              <div
                key={sess.session_id}
                onClick={() => onSelectSession(sess.session_id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.6rem 0.75rem",
                  borderRadius: "0.375rem",
                  background: isActive ? "rgba(99, 102, 241, 0.15)" : "transparent",
                  border: `1px solid ${isActive ? "rgba(99, 102, 241, 0.35)" : "transparent"}`,
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1, marginRight: "0.5rem" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: isActive ? 600 : 400, color: "var(--text-primary)" }}>
                    {sess.title || "Untitled Conversation"}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                    {sess.messages?.length || 0} messages &bull; {new Date(sess.updated_at).toLocaleDateString()}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.session_id);
                  }}
                  title="Delete conversation"
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    padding: "0.2rem",
                    display: "flex",
                  }}
                >
                  <TrashIcon size={14} />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
