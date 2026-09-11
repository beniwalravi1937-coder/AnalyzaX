"use client";

import React, { useState } from "react";
import { DashboardComponent, RefreshPolicy } from "@/types/dashboard";

interface ComponentConfigDrawerProps {
  component: DashboardComponent | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updated: Partial<DashboardComponent>) => void;
  onDelete: (componentId: string) => void;
}

export function ComponentConfigDrawer({
  component,
  isOpen,
  onClose,
  onSave,
  onDelete,
}: ComponentConfigDrawerProps) {
  if (!isOpen || !component) return null;

  const [title, setTitle] = useState(component.title);
  const [subtitle, setSubtitle] = useState(component.subtitle || "");
  const [width, setWidth] = useState(component.size?.width || 6);
  const [height, setHeight] = useState(component.size?.height || 4);
  const [refreshPolicy, setRefreshPolicy] = useState<RefreshPolicy>(
    component.refresh_policy || "RELOAD"
  );
  const [textContent, setTextContent] = useState(
    component.configuration?.content || ""
  );

  const handleSave = () => {
    const updated: Partial<DashboardComponent> = {
      title,
      subtitle: subtitle || undefined,
      size: { width, height },
      refresh_policy: refreshPolicy,
    };

    if (component.type === "TEXT") {
      updated.configuration = {
        ...(component.configuration || {}),
        content: textContent,
      };
    }

    onSave(updated);
    onClose();
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.6)",
        backdropFilter: "blur(2px)",
        zIndex: 1050,
        display: "flex",
        justifyContent: "flex-end",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          background: "#1e293b",
          borderLeft: "1px solid rgba(51, 65, 85, 0.8)",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          boxShadow: "-10px 0 30px rgba(0, 0, 0, 0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid rgba(51, 65, 85, 0.6)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
              Configure Component
            </h3>
            <span style={{ fontSize: "0.75rem", color: "#818cf8", fontWeight: 600 }}>
              {component.type}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              fontSize: "1.25rem",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "1.5rem", flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
              Component Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="input"
              style={{ width: "100%", fontSize: "0.85rem" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
              Subtitle / Description
            </label>
            <input
              type="text"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
              placeholder="Optional contextual note"
              className="input"
              style={{ width: "100%", fontSize: "0.85rem" }}
            />
          </div>

          {/* Grid Dimensions */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
                Width (1–12 cols)
              </label>
              <input
                type="number"
                min={1}
                max={12}
                value={width}
                onChange={(e) => setWidth(Number(e.target.value))}
                className="input"
                style={{ width: "100%", fontSize: "0.85rem" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
                Height (Rows)
              </label>
              <input
                type="number"
                min={1}
                max={24}
                value={height}
                onChange={(e) => setHeight(Number(e.target.value))}
                className="input"
                style={{ width: "100%", fontSize: "0.85rem" }}
              />
            </div>
          </div>

          {/* Refresh Policy */}
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
              Refresh Policy
            </label>
            <select
              value={refreshPolicy}
              onChange={(e) => setRefreshPolicy(e.target.value as RefreshPolicy)}
              className="input"
              style={{ width: "100%", fontSize: "0.85rem" }}
            >
              <option value="RELOAD">RELOAD (Reload existing query / result)</option>
              <option value="RECOMPUTE">RECOMPUTE (Trigger engine recomputation)</option>
              <option value="STATIC">STATIC (Frozen snapshot)</option>
            </select>
          </div>

          {/* Text/Markdown content editor if TEXT */}
          {component.type === "TEXT" && (
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
                Narrative Content (Markdown)
              </label>
              <textarea
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                rows={8}
                className="input"
                style={{ width: "100%", fontSize: "0.85rem", fontFamily: "monospace" }}
              />
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderTop: "1px solid rgba(51, 65, 85, 0.6)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <button
            onClick={() => {
              if (confirm(`Remove component '${component.title}'?`)) {
                onDelete(component.component_id);
                onClose();
              }
            }}
            style={{
              background: "rgba(239, 68, 68, 0.15)",
              color: "#f87171",
              border: "1px solid rgba(239, 68, 68, 0.4)",
              borderRadius: "6px",
              padding: "0.5rem 0.85rem",
              fontSize: "0.8rem",
              cursor: "pointer",
            }}
          >
            Delete Component
          </button>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={onClose} className="btn btn-secondary btn-sm">
              Cancel
            </button>
            <button onClick={handleSave} className="btn btn-primary btn-sm">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
