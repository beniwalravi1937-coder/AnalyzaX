"use client";

import React, { useState } from "react";
import { TransformationStep } from "@/types";
import { CheckIcon, CloseIcon, AlertCircleIcon } from "@/components/icons";

interface ApplyPlanDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (label: string) => void;
  steps: TransformationStep[];
  isLoading?: boolean;
}

export function ApplyPlanDialog({
  isOpen,
  onClose,
  onConfirm,
  steps,
  isLoading = false,
}: ApplyPlanDialogProps) {
  const [label, setLabel] = useState("");

  if (!isOpen) return null;

  const enabledSteps = steps.filter((s) => s.enabled !== false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm(label.trim() || `Cleaned (${enabledSteps.length} operations)`);
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.7)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1100,
        padding: "1rem",
      }}
    >
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          width: "100%",
          maxWidth: "480px",
          overflow: "hidden",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <div
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "6px",
                backgroundColor: "rgba(16, 185, 129, 0.15)",
                color: "#10b981",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CheckIcon size={16} />
            </div>
            <h3 style={{ margin: 0, fontSize: "1rem", color: "var(--text-primary)" }}>
              Apply Transformation Pipeline
            </h3>
          </div>

          <button
            onClick={onClose}
            disabled={isLoading}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-tertiary)",
              cursor: "pointer",
            }}
          >
            <CloseIcon size={18} />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.2rem" }}>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            You are about to execute <strong>{enabledSteps.length} transformation steps</strong>. This will persist a new immutable dataset version and automatically re-calculate data quality scores.
          </p>

          {/* Immutability Callout */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.6rem",
              padding: "0.75rem",
              backgroundColor: "rgba(99, 102, 241, 0.08)",
              border: "1px solid rgba(99, 102, 241, 0.25)",
              borderRadius: "6px",
            }}
          >
            <AlertCircleIcon size={16} style={{ color: "var(--accent-primary)", marginTop: "2px", flexShrink: 0 }} />
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
              <strong>Non-Destructive Assurance:</strong> The original uploaded file will never be altered or overwritten. You can rollback or switch versions at any time.
            </span>
          </div>

          {/* Version Label Input */}
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                marginBottom: "6px",
              }}
            >
              Version Label (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Cleaned Missing Values & Capped Outliers"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              disabled={isLoading}
              style={{
                width: "100%",
                padding: "0.55rem 0.75rem",
                fontSize: "0.82rem",
                backgroundColor: "var(--bg-canvas)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                color: "var(--text-primary)",
                outline: "none",
              }}
            />
          </div>

          {/* Footer Actions */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              style={{
                padding: "0.5rem 1rem",
                fontSize: "0.82rem",
                borderRadius: "6px",
                border: "1px solid var(--border-subtle)",
                backgroundColor: "transparent",
                color: "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                padding: "0.5rem 1.25rem",
                fontSize: "0.82rem",
                fontWeight: 600,
                borderRadius: "6px",
                border: "none",
                backgroundColor: "var(--accent-primary)",
                color: "#ffffff",
                cursor: isLoading ? "not-allowed" : "pointer",
                opacity: isLoading ? 0.7 : 1,
              }}
            >
              {isLoading ? "Executing Pipeline..." : "Confirm & Apply"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
