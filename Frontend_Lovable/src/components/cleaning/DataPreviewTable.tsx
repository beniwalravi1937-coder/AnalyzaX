"use client";

import React, { useState } from "react";
import { TransformationPreview } from "@/types";
import { AlertCircleIcon, CheckIcon } from "@/components/icons";

interface DataPreviewTableProps {
  preview: TransformationPreview | null;
  isLoading?: boolean;
}

export function DataPreviewTable({ preview, isLoading = false }: DataPreviewTableProps) {
  const [activeTab, setActiveTab] = useState<"after" | "before">("after");

  if (isLoading) {
    return (
      <div
        style={{
          padding: "3rem 1rem",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "8px",
          gap: "0.75rem",
          color: "var(--text-tertiary)",
        }}
      >
        <div
          className="spin"
          style={{
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            border: "3px solid var(--border-subtle)",
            borderTopColor: "var(--accent-primary)",
          }}
        />
        <p style={{ margin: 0, fontSize: "0.85rem", fontWeight: 500 }}>
          Calculating preview transformation in Polars analytical engine...
        </p>
      </div>
    );
  }

  if (!preview) {
    return (
      <div
        style={{
          padding: "3rem 1rem",
          textAlign: "center",
          backgroundColor: "var(--bg-surface)",
          border: "1px dashed var(--border-subtle)",
          borderRadius: "8px",
          color: "var(--text-tertiary)",
          fontSize: "0.85rem",
        }}
      >
        Click &quot;Preview Plan&quot; to inspect Before/After row changes without modifying the dataset.
      </div>
    );
  }

  if (preview.validation_errors.length > 0) {
    return (
      <div
        style={{
          padding: "1.25rem",
          backgroundColor: "rgba(244, 63, 94, 0.08)",
          border: "1px solid rgba(244, 63, 94, 0.3)",
          borderRadius: "8px",
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#f43f5e" }}>
          <AlertCircleIcon size={18} />
          <h4 style={{ margin: 0, fontSize: "0.9rem", fontWeight: 600 }}>
            Plan Validation Failed ({preview.validation_errors.length} error{preview.validation_errors.length > 1 ? "s" : ""})
          </h4>
        </div>
        <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          {preview.validation_errors.map((err, i) => (
            <li key={i} style={{ marginBottom: "2px" }}>
              {err}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  const columns = activeTab === "after" ? preview.columns_after : preview.columns_before;
  const sample = activeTab === "after" ? preview.sample_after : preview.sample_before;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "8px",
        overflow: "hidden",
      }}
    >
      {/* Metric Strip & Tabs */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1rem",
          borderBottom: "1px solid var(--border-subtle)",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        {/* Metric Badges */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Rows:</span>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
              {preview.rows_before} → {preview.rows_after}
            </span>
            {preview.rows_affected > 0 && (
              <span
                style={{
                  fontSize: "0.68rem",
                  padding: "1px 6px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(245, 158, 11, 0.15)",
                  color: "#f59e0b",
                  fontWeight: 600,
                }}
              >
                -{preview.rows_affected} rows
              </span>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Columns:</span>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
              {preview.columns_before.length} → {preview.columns_after.length}
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Steps:</span>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#10b981" }}>
              {preview.step_summaries.length} validated
            </span>
          </div>
        </div>

        {/* Tab Switcher */}
        <div
          style={{
            display: "flex",
            backgroundColor: "var(--bg-canvas)",
            padding: "2px",
            borderRadius: "6px",
            border: "1px solid var(--border-subtle)",
          }}
        >
          <button
            onClick={() => setActiveTab("after")}
            style={{
              padding: "0.3rem 0.75rem",
              fontSize: "0.75rem",
              fontWeight: 600,
              borderRadius: "4px",
              border: "none",
              backgroundColor: activeTab === "after" ? "var(--bg-surface)" : "transparent",
              color: activeTab === "after" ? "var(--accent-primary)" : "var(--text-tertiary)",
              cursor: "pointer",
              boxShadow: activeTab === "after" ? "0 1px 3px rgba(0,0,0,0.2)" : "none",
            }}
          >
            After Transformation ({preview.rows_after} rows)
          </button>
          <button
            onClick={() => setActiveTab("before")}
            style={{
              padding: "0.3rem 0.75rem",
              fontSize: "0.75rem",
              fontWeight: 600,
              borderRadius: "4px",
              border: "none",
              backgroundColor: activeTab === "before" ? "var(--bg-surface)" : "transparent",
              color: activeTab === "before" ? "var(--accent-primary)" : "var(--text-tertiary)",
              cursor: "pointer",
              boxShadow: activeTab === "before" ? "0 1px 3px rgba(0,0,0,0.2)" : "none",
            }}
          >
            Before Snapshot ({preview.rows_before} rows)
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div style={{ overflowX: "auto", maxHeight: "380px" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.78rem",
            textAlign: "left",
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: "var(--bg-canvas)",
                borderBottom: "1px solid var(--border-subtle)",
                position: "sticky",
                top: 0,
                zIndex: 1,
              }}
            >
              <th
                style={{
                  padding: "0.5rem 0.75rem",
                  color: "var(--text-tertiary)",
                  fontWeight: 600,
                  width: "40px",
                }}
              >
                #
              </th>
              {columns.map((col) => {
                const isNew =
                  activeTab === "after" && !preview.columns_before.includes(col);

                return (
                  <th
                    key={col}
                    style={{
                      padding: "0.5rem 0.75rem",
                      color: isNew ? "var(--accent-primary)" : "var(--text-secondary)",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {col}
                    {isNew && (
                      <span
                        style={{
                          marginLeft: "4px",
                          fontSize: "0.65rem",
                          padding: "1px 4px",
                          borderRadius: "3px",
                          backgroundColor: "rgba(99, 102, 241, 0.15)",
                          color: "var(--accent-primary)",
                        }}
                      >
                        NEW
                      </span>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {sample.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + 1}
                  style={{
                    padding: "2rem",
                    textAlign: "center",
                    color: "var(--text-tertiary)",
                  }}
                >
                  No rows returned.
                </td>
              </tr>
            ) : (
              sample.map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    backgroundColor:
                      idx % 2 === 0 ? "transparent" : "var(--bg-surface-raised)",
                  }}
                >
                  <td
                    style={{
                      padding: "0.45rem 0.75rem",
                      color: "var(--text-tertiary)",
                      fontWeight: 500,
                    }}
                  >
                    {idx + 1}
                  </td>
                  {columns.map((col) => {
                    const val = row[col];
                    const isNull = val === null || val === undefined;

                    return (
                      <td
                        key={col}
                        style={{
                          padding: "0.45rem 0.75rem",
                          color: isNull ? "var(--text-tertiary)" : "var(--text-primary)",
                          fontStyle: isNull ? "italic" : "normal",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {isNull ? (
                          <span
                            style={{
                              padding: "1px 4px",
                              borderRadius: "3px",
                              backgroundColor: "rgba(244, 63, 94, 0.1)",
                              color: "#f43f5e",
                              fontSize: "0.7rem",
                            }}
                          >
                            null
                          </span>
                        ) : (
                          String(val)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
