"use client";

import React, { useState } from "react";
import { Dashboard } from "@/types/dashboard";
import { ShareModal } from "@/components/collaboration/ShareModal";

interface DashboardHeaderProps {
  dashboard: Dashboard;
  datasetName?: string;
  isEditMode: boolean;
  saveStatus: "saved" | "saving" | "unsaved" | "error";
  onToggleEditMode: () => void;
  onRename: (newName: string) => void;
  onSave: () => void;
  onOpenPalette: () => void;
  onOpenHistory: () => void;
  onDuplicate: () => void;
  onExport: () => void;
  onDelete: () => void;
}

export function DashboardHeader({
  dashboard,
  datasetName,
  isEditMode,
  saveStatus,
  onToggleEditMode,
  onRename,
  onSave,
  onOpenPalette,
  onOpenHistory,
  onDuplicate,
  onExport,
  onDelete,
}: DashboardHeaderProps) {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleInput, setTitleInput] = useState(dashboard.name);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  const handleTitleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (titleInput.trim()) {
      onRename(titleInput.trim());
      setIsEditingTitle(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "1rem",
        marginBottom: "1.25rem",
        borderBottom: "1px solid rgba(51, 65, 85, 0.6)",
        paddingBottom: "1rem",
      }}
    >
      {/* Left title and badges */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {isEditingTitle && isEditMode ? (
            <form onSubmit={handleTitleSubmit} style={{ display: "inline-flex", gap: "0.5rem" }}>
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                className="input"
                style={{ fontSize: "1.25rem", fontWeight: 700, padding: "0.2rem 0.5rem" }}
                autoFocus
              />
              <button type="submit" className="btn btn-primary btn-sm">
                Save
              </button>
              <button
                type="button"
                onClick={() => {
                  setTitleInput(dashboard.name);
                  setIsEditingTitle(false);
                }}
                className="btn btn-secondary btn-sm"
              >
                Cancel
              </button>
            </form>
          ) : (
            <h1
              onClick={() => isEditMode && setIsEditingTitle(true)}
              style={{
                margin: 0,
                fontSize: "1.4rem",
                fontWeight: 800,
                color: "#ffffff",
                letterSpacing: "-0.02em",
                cursor: isEditMode ? "pointer" : "default",
              }}
              title={isEditMode ? "Click to rename dashboard" : ""}
            >
              {dashboard.name}
              {isEditMode && <span style={{ fontSize: "0.8rem", color: "#818cf8", marginLeft: "0.5rem" }}>✎</span>}
            </h1>
          )}

          <span
            style={{
              fontSize: "0.75rem",
              background: "rgba(99, 102, 241, 0.2)",
              color: "#a5b4fc",
              padding: "0.2rem 0.5rem",
              borderRadius: "6px",
              fontWeight: 600,
            }}
          >
            v{dashboard.version}
          </span>

          <span
            style={{
              fontSize: "0.75rem",
              background: "rgba(51, 65, 85, 0.5)",
              color: "#94a3b8",
              padding: "0.2rem 0.5rem",
              borderRadius: "6px",
            }}
          >
            {datasetName || dashboard.dataset_id} ({dashboard.dataset_version_id})
          </span>
        </div>

        {dashboard.description && (
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.85rem", color: "#94a3b8" }}>
            {dashboard.description}
          </p>
        )}
      </div>

      {/* Right controls */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
        {/* Autosave status */}
        <span
          style={{
            fontSize: "0.75rem",
            color:
              saveStatus === "saving"
                ? "#f59e0b"
                : saveStatus === "unsaved"
                ? "#f97316"
                : saveStatus === "error"
                ? "#ef4444"
                : "#10b981",
            marginRight: "0.5rem",
          }}
        >
          {saveStatus === "saving"
            ? "Saving..."
            : saveStatus === "unsaved"
            ? "Unsaved changes"
            : saveStatus === "error"
            ? "Save failed"
            : "Saved"}
        </span>

        {/* View / Edit Mode Toggle */}
        <button
          onClick={onToggleEditMode}
          className="btn btn-secondary btn-sm"
          style={{
            background: isEditMode ? "rgba(99, 102, 241, 0.2)" : "transparent",
            borderColor: isEditMode ? "#6366f1" : "rgba(51, 65, 85, 0.8)",
            color: isEditMode ? "#a5b4fc" : "#cbd5e1",
          }}
        >
          {isEditMode ? "Preview Mode" : "Edit Mode"}
        </button>

        {isEditMode && (
          <>
            <button onClick={onOpenPalette} className="btn btn-primary btn-sm">
              + Add Component
            </button>
            <button onClick={onSave} className="btn btn-secondary btn-sm">
              Save
            </button>
          </>
        )}

        <button onClick={onOpenHistory} className="btn btn-secondary btn-sm" title="Version History">
          History
        </button>

        <button onClick={onDuplicate} className="btn btn-secondary btn-sm" title="Duplicate Dashboard">
          Duplicate
        </button>

        <button
          onClick={() => setIsShareModalOpen(true)}
          className="btn btn-secondary btn-sm"
          style={{ borderColor: "rgba(99, 102, 241, 0.4)", color: "#a5b4fc" }}
          title="Share & Manage Access"
        >
          Share
        </button>

        <button onClick={onExport} className="btn btn-secondary btn-sm" title="Export JSON">
          Export
        </button>

        <button
          onClick={onDelete}
          className="btn btn-secondary btn-sm"
          style={{ color: "#f87171" }}
          title="Delete Dashboard"
        >
          Delete
        </button>
      </div>

      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        resourceType="DASHBOARD"
        resourceId={dashboard.dashboard_id}
        resourceTitle={dashboard.name}
      />
    </div>
  );
}
