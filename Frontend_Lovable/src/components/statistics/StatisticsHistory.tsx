"use client";

import React from "react";
import { StatisticalResult } from "@/types/statistics";

interface StatisticsHistoryProps {
  history: StatisticalResult[];
  activeId?: string;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export const StatisticsHistory: React.FC<StatisticsHistoryProps> = ({
  history,
  activeId,
  onSelect,
  onDelete,
}) => {
  if (!history || history.length === 0) {
    return (
      <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
        No historical statistical analyses found for this dataset version.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      {history.map((item) => {
        const isSelected = item.result_id === activeId;
        const rawP = item.p_values?.primary ?? item.statistics?.p_value;
        const pVal = typeof rawP === "number" ? rawP : null;
        const dateStr = new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

        return (
          <div
            key={item.result_id}
            onClick={() => onSelect(item.result_id)}
            style={{
              padding: "0.75rem 1rem",
              borderRadius: "6px",
              background: isSelected ? "var(--primary-subtle, rgba(59, 130, 246, 0.12))" : "var(--bg-subtle, rgba(255, 255, 255, 0.02))",
              border: `1px solid ${isSelected ? "var(--primary, #3b82f6)" : "var(--border-subtle, rgba(255, 255, 255, 0.08))"}`,
              cursor: "pointer",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              transition: "all 0.15s ease",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)" }}>
                  {item.method.replace(/_/g, " ").toUpperCase()}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--primary)", fontWeight: 500 }}>
                  @{item.dataset_version_id}
                </span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                Target: {item.inputs?.target_columns?.join(", ") || "N/A"}
                {item.inputs?.group_columns?.length ? ` | Group: ${item.inputs.group_columns.join(", ")}` : ""}
                {pVal != null ? ` | p=${pVal < 0.0001 ? "<0.0001" : pVal.toFixed(4)}` : ""}
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{dateStr}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(item.result_id);
                }}
                className="btn btn-xs btn-ghost text-danger"
                title="Delete from history"
              >
                ✕
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
