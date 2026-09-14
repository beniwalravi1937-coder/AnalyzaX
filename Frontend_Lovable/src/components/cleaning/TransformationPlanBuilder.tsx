"use client";

import React, { useState } from "react";
import { TransformationStep, TransformationType } from "@/types";
import {
  TrashIcon,
  PlayIcon,
  PlusIcon,
  CheckIcon,
  AlertCircleIcon,
  WandIcon,
} from "@/components/icons";

interface TransformationPlanBuilderProps {
  steps: TransformationStep[];
  availableColumns: string[];
  onUpdateSteps: (newSteps: TransformationStep[]) => void;
  onPreview: () => void;
  onApply: () => void;
  isPreviewLoading?: boolean;
  isApplyLoading?: boolean;
}

export function TransformationPlanBuilder({
  steps,
  availableColumns,
  onUpdateSteps,
  onPreview,
  onApply,
  isPreviewLoading = false,
  isApplyLoading = false,
}: TransformationPlanBuilderProps) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedType, setSelectedType] = useState<TransformationType>("FILL_MISSING");
  const [targetColumn, setTargetColumn] = useState<string>(availableColumns[0] || "");
  const [customParams, setCustomParams] = useState<Record<string, any>>({});

  const handleToggleStep = (index: number) => {
    const updated = [...steps];
    updated[index] = {
      ...updated[index],
      enabled: updated[index].enabled !== false ? false : true,
    };
    onUpdateSteps(updated);
  };

  const handleRemoveStep = (index: number) => {
    const updated = steps.filter((_, i) => i !== index);
    onUpdateSteps(updated);
  };

  const handleMoveStep = (index: number, direction: "up" | "down") => {
    if (
      (direction === "up" && index === 0) ||
      (direction === "down" && index === steps.length - 1)
    ) {
      return;
    }
    const targetIdx = direction === "up" ? index - 1 : index + 1;
    const updated = [...steps];
    const temp = updated[index];
    updated[index] = updated[targetIdx];
    updated[targetIdx] = temp;
    onUpdateSteps(updated);
  };

  const handleAddCustomStep = () => {
    const stepId = `step_${Date.now()}`;
    let desc = "";
    const params: Record<string, any> = { ...customParams };

    switch (selectedType) {
      case "FILL_MISSING":
        params.column = targetColumn;
        params.strategy = params.strategy || "median";
        desc = `Fill missing in '${targetColumn}' with ${params.strategy}`;
        break;
      case "DROP_MISSING":
        params.columns = [targetColumn];
        params.strategy = params.strategy || "drop_rows";
        desc = `Drop missing rows in '${targetColumn}'`;
        break;
      case "DROP_DUPLICATES":
        params.keep = params.keep || "first";
        desc = `Deduplicate identical records (keep ${params.keep})`;
        break;
      case "TRIM_WHITESPACE":
        params.column = targetColumn;
        desc = `Trim whitespace in '${targetColumn}'`;
        break;
      case "TEXT_CASE":
        params.column = targetColumn;
        params.case = params.case || "lower";
        desc = `Convert '${targetColumn}' to ${params.case}`;
        break;
      case "REPLACE_TEXT":
        params.column = targetColumn;
        params.find = params.find || "";
        params.replace = params.replace || "";
        desc = `Replace '${params.find}' with '${params.replace}' in '${targetColumn}'`;
        break;
      case "CAST_TYPE":
        params.column = targetColumn;
        params.target_type = params.target_type || "float";
        desc = `Cast '${targetColumn}' to ${params.target_type}`;
        break;
      case "PARSE_DATE":
        params.column = targetColumn;
        desc = `Parse '${targetColumn}' as Date`;
        break;
      case "FILTER_ROWS":
        params.column = targetColumn;
        params.operator = params.operator || ">=";
        params.value = params.value ?? 0;
        desc = `Filter '${targetColumn}' ${params.operator} ${params.value}`;
        break;
      case "DROP_COLUMNS":
        params.columns = [targetColumn];
        desc = `Drop column '${targetColumn}'`;
        break;
      case "DERIVED_COLUMN":
        params.new_column = params.new_column || "new_feature";
        params.expression = params.expression || `${targetColumn} * 2`;
        desc = `Calculate '${params.new_column}' = ${params.expression}`;
        break;
      case "ONE_HOT_ENCODE":
        params.column = targetColumn;
        desc = `One-hot encode '${targetColumn}'`;
        break;
      case "SCALE_NUMERIC":
        params.column = targetColumn;
        params.method = params.method || "min_max";
        desc = `Scale '${targetColumn}' using ${params.method}`;
        break;
      case "HANDLE_OUTLIERS":
        params.column = targetColumn;
        params.method = params.method || "clip_iqr";
        desc = `Clip outliers in '${targetColumn}' using IQR`;
        break;
      default:
        desc = `Apply ${selectedType}`;
    }

    const newStep: TransformationStep = {
      step_id: stepId,
      type: selectedType,
      parameters: params,
      input_columns: [targetColumn],
      output_columns: [targetColumn],
      description: desc,
      enabled: true,
    };

    onUpdateSteps([...steps, newStep]);
    setShowAddModal(false);
    setCustomParams({});
  };

  const getStepTypeColor = (type: TransformationType) => {
    if (type.includes("MISSING")) return "#3b82f6";
    if (type.includes("DUPLICATE")) return "#10b981";
    if (type.includes("TRIM") || type.includes("TEXT")) return "#8b5cf6";
    if (type.includes("DATE")) return "#ec4899";
    if (type.includes("FILTER")) return "#f59e0b";
    if (type.includes("DERIVED") || type.includes("SCALE")) return "#06b6d4";
    return "#6366f1";
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        height: "100%",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h3
            style={{
              fontSize: "0.95rem",
              fontWeight: 600,
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Transformation Pipeline
          </h3>
          <span
            style={{
              fontSize: "0.75rem",
              padding: "2px 8px",
              borderRadius: "12px",
              backgroundColor: "var(--bg-surface-raised)",
              color: "var(--text-secondary)",
              fontWeight: 500,
            }}
          >
            {steps.filter((s) => s.enabled !== false).length} Active Steps
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          {steps.length > 0 && (
            <button
              onClick={() => onUpdateSteps([])}
              style={{
                padding: "0.35rem 0.65rem",
                fontSize: "0.75rem",
                borderRadius: "6px",
                border: "1px solid var(--border-subtle)",
                backgroundColor: "transparent",
                color: "var(--text-tertiary)",
                cursor: "pointer",
              }}
            >
              Clear All
            </button>
          )}

          <button
            onClick={() => setShowAddModal(true)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.35rem",
              padding: "0.35rem 0.75rem",
              fontSize: "0.75rem",
              fontWeight: 600,
              borderRadius: "6px",
              border: "1px solid var(--border-subtle)",
              backgroundColor: "var(--bg-surface)",
              color: "var(--text-primary)",
              cursor: "pointer",
            }}
          >
            <PlusIcon size={12} />
            Add Custom Step
          </button>
        </div>
      </div>

      {/* Steps List */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0.6rem",
          overflowY: "auto",
          paddingRight: "4px",
          flex: 1,
        }}
      >
        {steps.length === 0 ? (
          <div
            style={{
              padding: "2.5rem 1rem",
              textAlign: "center",
              backgroundColor: "var(--bg-surface)",
              borderRadius: "8px",
              border: "1px dashed var(--border-subtle)",
              color: "var(--text-tertiary)",
            }}
          >
            <WandIcon size={24} style={{ marginBottom: "0.5rem", opacity: 0.5 }} />
            <p style={{ margin: 0, fontWeight: 500, fontSize: "0.85rem" }}>
              Pipeline is currently empty
            </p>
            <p style={{ margin: "4px 0 0 0", fontSize: "0.75rem" }}>
              Select recommendations from the left panel or click &quot;Add Custom Step&quot;.
            </p>
          </div>
        ) : (
          steps.map((step, idx) => {
            const isEnabled = step.enabled !== false;
            const badgeColor = getStepTypeColor(step.type);

            return (
              <div
                key={step.step_id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.75rem 1rem",
                  backgroundColor: isEnabled ? "var(--bg-surface)" : "var(--bg-canvas)",
                  border: `1px solid ${isEnabled ? "var(--border-subtle)" : "transparent"}`,
                  borderRadius: "8px",
                  opacity: isEnabled ? 1 : 0.6,
                  transition: "all 0.15s ease",
                  gap: "0.75rem",
                }}
              >
                {/* Index & Toggle */}
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: "var(--text-tertiary)",
                      width: "16px",
                    }}
                  >
                    {idx + 1}
                  </span>

                  <input
                    type="checkbox"
                    checked={isEnabled}
                    onChange={() => handleToggleStep(idx)}
                    style={{ cursor: "pointer" }}
                    title={isEnabled ? "Disable step" : "Enable step"}
                  />

                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span
                        style={{
                          fontSize: "0.68rem",
                          fontWeight: 700,
                          padding: "1px 6px",
                          borderRadius: "4px",
                          backgroundColor: `${badgeColor}1a`,
                          color: badgeColor,
                          border: `1px solid ${badgeColor}40`,
                        }}
                      >
                        {step.type}
                      </span>
                      <p
                        style={{
                          margin: 0,
                          fontSize: "0.82rem",
                          fontWeight: 600,
                          color: isEnabled ? "var(--text-primary)" : "var(--text-tertiary)",
                        }}
                      >
                        {step.description}
                      </p>
                    </div>

                    {/* Step details */}
                    <div
                      style={{
                        fontSize: "0.7rem",
                        color: "var(--text-tertiary)",
                        marginTop: "2px",
                      }}
                    >
                      {Object.entries(step.parameters).map(([k, v]) => (
                        <span key={k} style={{ marginRight: "0.5rem" }}>
                          {k}: <code style={{ color: "var(--text-secondary)" }}>{String(v)}</code>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions: Reorder & Remove */}
                <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <button
                    onClick={() => handleMoveStep(idx, "up")}
                    disabled={idx === 0}
                    style={{
                      padding: "0.25rem 0.4rem",
                      fontSize: "0.7rem",
                      borderRadius: "4px",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "transparent",
                      color: "var(--text-tertiary)",
                      cursor: idx === 0 ? "not-allowed" : "pointer",
                      opacity: idx === 0 ? 0.4 : 1,
                    }}
                    title="Move step up"
                  >
                    ↑
                  </button>

                  <button
                    onClick={() => handleMoveStep(idx, "down")}
                    disabled={idx === steps.length - 1}
                    style={{
                      padding: "0.25rem 0.4rem",
                      fontSize: "0.7rem",
                      borderRadius: "4px",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "transparent",
                      color: "var(--text-tertiary)",
                      cursor: idx === steps.length - 1 ? "not-allowed" : "pointer",
                      opacity: idx === steps.length - 1 ? 0.4 : 1,
                    }}
                    title="Move step down"
                  >
                    ↓
                  </button>

                  <button
                    onClick={() => handleRemoveStep(idx)}
                    style={{
                      padding: "0.25rem 0.4rem",
                      borderRadius: "4px",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "transparent",
                      color: "#f43f5e",
                      cursor: "pointer",
                    }}
                    title="Remove step from pipeline"
                  >
                    <TrashIcon size={13} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Action Footer: Preview & Apply Buttons */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          gap: "0.75rem",
          paddingTop: "0.75rem",
          borderTop: "1px solid var(--border-subtle)",
        }}
      >
        <button
          onClick={onPreview}
          disabled={steps.length === 0 || isPreviewLoading}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.55rem 1.1rem",
            fontSize: "0.82rem",
            fontWeight: 600,
            borderRadius: "6px",
            border: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-surface)",
            color: "var(--text-primary)",
            cursor: steps.length === 0 || isPreviewLoading ? "not-allowed" : "pointer",
            opacity: steps.length === 0 ? 0.5 : 1,
          }}
        >
          <PlayIcon size={13} className={isPreviewLoading ? "spin" : ""} />
          {isPreviewLoading ? "Generating Preview..." : "Preview Plan"}
        </button>

        <button
          onClick={onApply}
          disabled={steps.length === 0 || isApplyLoading}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.55rem 1.25rem",
            fontSize: "0.82rem",
            fontWeight: 600,
            borderRadius: "6px",
            border: "none",
            backgroundColor: "var(--accent-primary)",
            color: "#ffffff",
            cursor: steps.length === 0 || isApplyLoading ? "not-allowed" : "pointer",
            opacity: steps.length === 0 ? 0.5 : 1,
            boxShadow: "0 2px 8px rgba(99, 102, 241, 0.35)",
          }}
        >
          <CheckIcon size={14} />
          {isApplyLoading ? "Applying Pipeline..." : "Apply & Create Version"}
        </button>
      </div>

      {/* Add Custom Step Modal */}
      {showAddModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.65)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "12px",
              padding: "1.5rem",
              width: "100%",
              maxWidth: "500px",
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
              boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
            }}
          >
            <h3 style={{ margin: 0, fontSize: "1.05rem", color: "var(--text-primary)" }}>
              Add Transformation Step
            </h3>

            {/* Type selector */}
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: "var(--text-secondary)",
                  marginBottom: "4px",
                }}
              >
                Transformation Type
              </label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value as TransformationType)}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-subtle)",
                  backgroundColor: "var(--bg-canvas)",
                  color: "var(--text-primary)",
                  fontSize: "0.82rem",
                }}
              >
                <option value="FILL_MISSING">Fill Missing Values (Imputation)</option>
                <option value="DROP_MISSING">Drop Missing Rows/Columns</option>
                <option value="DROP_DUPLICATES">Drop Duplicate Rows</option>
                <option value="TRIM_WHITESPACE">Trim Whitespace</option>
                <option value="TEXT_CASE">Change Text Case</option>
                <option value="REPLACE_TEXT">Find & Replace Text</option>
                <option value="CAST_TYPE">Cast Data Type</option>
                <option value="PARSE_DATE">Parse Date / Datetime</option>
                <option value="FILTER_ROWS">Filter Rows (Predicate)</option>
                <option value="DROP_COLUMNS">Drop Column</option>
                <option value="DERIVED_COLUMN">Calculate Derived Feature</option>
                <option value="ONE_HOT_ENCODE">One-Hot Encode</option>
                <option value="SCALE_NUMERIC">Scale / Standardize</option>
                <option value="HANDLE_OUTLIERS">Clip Outliers (Winsorize)</option>
              </select>
            </div>

            {/* Target column selector */}
            {selectedType !== "DROP_DUPLICATES" && (
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    marginBottom: "4px",
                  }}
                >
                  Target Column
                </label>
                <select
                  value={targetColumn}
                  onChange={(e) => setTargetColumn(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    borderRadius: "6px",
                    border: "1px solid var(--border-subtle)",
                    backgroundColor: "var(--bg-canvas)",
                    color: "var(--text-primary)",
                    fontSize: "0.82rem",
                  }}
                >
                  {availableColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Dynamic parameters depending on type */}
            {selectedType === "FILL_MISSING" && (
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    marginBottom: "4px",
                  }}
                >
                  Imputation Strategy
                </label>
                <select
                  value={customParams.strategy || "median"}
                  onChange={(e) =>
                    setCustomParams({ ...customParams, strategy: e.target.value })
                  }
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    borderRadius: "6px",
                    border: "1px solid var(--border-subtle)",
                    backgroundColor: "var(--bg-canvas)",
                    color: "var(--text-primary)",
                    fontSize: "0.82rem",
                  }}
                >
                  <option value="median">Median (Continuous Numeric)</option>
                  <option value="mean">Mean (Continuous Numeric)</option>
                  <option value="mode">Mode (Most Frequent Category)</option>
                  <option value="zero">Zero (0)</option>
                  <option value="unknown">String &quot;Unknown&quot;</option>
                </select>
              </div>
            )}

            {selectedType === "TEXT_CASE" && (
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    marginBottom: "4px",
                  }}
                >
                  Target Case
                </label>
                <select
                  value={customParams.case || "lower"}
                  onChange={(e) => setCustomParams({ ...customParams, case: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    borderRadius: "6px",
                    border: "1px solid var(--border-subtle)",
                    backgroundColor: "var(--bg-canvas)",
                    color: "var(--text-primary)",
                    fontSize: "0.82rem",
                  }}
                >
                  <option value="lower">lowercase</option>
                  <option value="upper">UPPERCASE</option>
                  <option value="title">Title Case</option>
                </select>
              </div>
            )}

            {selectedType === "DERIVED_COLUMN" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: "var(--text-secondary)",
                      marginBottom: "4px",
                    }}
                  >
                    New Column Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. net_profit"
                    value={customParams.new_column || ""}
                    onChange={(e) =>
                      setCustomParams({ ...customParams, new_column: e.target.value })
                    }
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      borderRadius: "6px",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "var(--bg-canvas)",
                      color: "var(--text-primary)",
                      fontSize: "0.82rem",
                    }}
                  />
                </div>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: "var(--text-secondary)",
                      marginBottom: "4px",
                    }}
                  >
                    Formula (e.g. price * quantity)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. revenue - cost"
                    value={customParams.expression || ""}
                    onChange={(e) =>
                      setCustomParams({ ...customParams, expression: e.target.value })
                    }
                    style={{
                      width: "100%",
                      padding: "0.45rem",
                      borderRadius: "6px",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "var(--bg-canvas)",
                      color: "var(--text-primary)",
                      fontSize: "0.82rem",
                    }}
                  />
                </div>
              </div>
            )}

            {/* Modal Buttons */}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "0.5rem",
                marginTop: "0.5rem",
              }}
            >
              <button
                onClick={() => setShowAddModal(false)}
                style={{
                  padding: "0.45rem 0.9rem",
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
                onClick={handleAddCustomStep}
                style={{
                  padding: "0.45rem 1rem",
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  borderRadius: "6px",
                  border: "none",
                  backgroundColor: "var(--accent-primary)",
                  color: "#ffffff",
                  cursor: "pointer",
                }}
              >
                Add to Pipeline
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
