"use client";

import React, { useEffect, useState } from "react";
import { DatasetResponse } from "@/types";
import { AnalystSession } from "@/types/ai_analyst";
import { api } from "@/services/api";
import {
  createAnalystSession,
  deleteAnalystSession,
  listAnalystSessions,
} from "@/services/aiAnalystApi";
import { SessionSidebar } from "./SessionSidebar";
import { ChatWindow } from "./ChatWindow";

export function AIAnalystWorkspace() {
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | undefined>();
  const [activeVersionId, setActiveVersionId] = useState<string>("v1");
  const [sessions, setSessions] = useState<AnalystSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const [dsRes, sessList] = await Promise.all([
        api.listDatasets().catch(() => ({ datasets: [] })),
        listAnalystSessions().catch(() => []),
      ]);
      const dsList = dsRes.datasets || [];
      setDatasets(dsList);
      if (dsList.length > 0) {
        setActiveDatasetId(dsList[0].id);
        setActiveVersionId("v1");
      }
      setSessions(sessList);
      if (sessList.length > 0) {
        setActiveSessionId(sessList[0].session_id);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSession = async () => {
    try {
      const newSess = await createAnalystSession("New Conversation", activeDatasetId, activeVersionId);
      setSessions((prev) => [newSess, ...prev]);
      setActiveSessionId(newSess.session_id);
    } catch (err) {
      console.error("Failed to create new session:", err);
    }
  };

  const handleDeleteSession = async (sessId: string) => {
    try {
      await deleteAnalystSession(sessId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessId));
      if (activeSessionId === sessId) {
        const remaining = sessions.filter((s) => s.session_id !== sessId);
        setActiveSessionId(remaining.length > 0 ? remaining[0].session_id : undefined);
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        borderRadius: "0.75rem",
        overflow: "hidden",
        border: "1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))",
        height: "calc(100vh - 200px)",
        minHeight: "600px",
      }}
    >
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
      />

      <ChatWindow
        activeSessionId={activeSessionId}
        datasets={datasets}
        activeDatasetId={activeDatasetId}
        activeVersionId={activeVersionId}
        onDatasetChange={(dsId) => {
          setActiveDatasetId(dsId);
          setActiveVersionId("v1");
        }}
        onSessionChange={(sessId) => {
          setActiveSessionId(sessId);
          listAnalystSessions().then(setSessions).catch(() => {});
        }}
      />
    </div>
  );
}
