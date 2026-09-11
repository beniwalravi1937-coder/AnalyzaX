"use client";

import React from "react";
import { ChevronRightIcon } from "@/components/icons";

interface DrilldownStep {
  field: string;
  value: string | number;
}

interface DrilldownPanelProps {
  hierarchy: string[]; // e.g., ["category", "subcategory", "item"]
  currentPath: DrilldownStep[];
  onNavigateToStep: (stepIndex: number) => void;
  onReset: () => void;
  availableNextFields?: string[];
  onSelectNextField?: (field: string) => void;
}

export function DrilldownPanel({
  hierarchy,
  currentPath,
  onNavigateToStep,
  onReset,
  availableNextFields,
  onSelectNextField,
}: DrilldownPanelProps) {
  if (hierarchy.length === 0 && currentPath.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0.4rem 0.75rem",
        backgroundColor: "rgba(99, 102, 241, 0.08)",
        borderRadius: "0.375rem",
        border: "1px solid rgba(99, 102, 241, 0.2)",
        marginBottom: "0.75rem",
        flexWrap: "wrap",
        gap: "0.5rem",
      }}
    >
      {/* Breadcrumbs */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", fontSize: "0.8rem" }}>
        <span style={{ fontWeight: 600, color: "var(--brand-primary, #6366f1)" }}>
          Drilldown:
        </span>
        <button
          onClick={onReset}
          className="btn-link"
          style={{
            cursor: "pointer",
            color: currentPath.length === 0 ? "var(--text-primary)" : "var(--text-secondary)",
            background: "none",
            border: "none",
            padding: 0,
            fontSize: "0.8rem",
            fontWeight: currentPath.length === 0 ? 600 : 400,
          }}
        >
          All ({hierarchy[0] || "Root"})
        </button>

        {currentPath.map((step, idx) => (
          <React.Fragment key={idx}>
            <ChevronRightIcon size={12} className="text-muted" />
            <button
              onClick={() => onNavigateToStep(idx)}
              className="btn-link"
              style={{
                cursor: "pointer",
                color:
                  idx === currentPath.length - 1
                    ? "var(--brand-primary, #6366f1)"
                    : "var(--text-secondary)",
                background: "none",
                border: "none",
                padding: 0,
                fontSize: "0.8rem",
                fontWeight: idx === currentPath.length - 1 ? 600 : 400,
              }}
            >
              {step.field}: <strong>{String(step.value)}</strong>
            </button>
          </React.Fragment>
        ))}
      </div>

      {/* Next hierarchy level if applicable */}
      {availableNextFields && availableNextFields.length > 0 && onSelectNextField && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Next Level:</span>
          <select
            onChange={(e) => e.target.value && onSelectNextField(e.target.value)}
            defaultValue=""
            className="input input-sm"
            style={{ fontSize: "0.75rem", padding: "0.2rem 0.4rem" }}
          >
            <option value="" disabled>
              Select breakdown field...
            </option>
            {availableNextFields.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
