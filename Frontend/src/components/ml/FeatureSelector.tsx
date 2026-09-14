"use client";

import React from "react";

interface FeatureSelectorProps {
  columns: string[];
  targetColumn: string;
  selectedFeatures: string[];
  onSelectedFeaturesChange: (features: string[]) => void;
  recommendedFeatures: string[];
  excludedFeatures: Record<string, string>;
  isLoading?: boolean;
  onReloadColumns?: () => void;
}

export const FeatureSelector: React.FC<FeatureSelectorProps> = ({
  columns,
  targetColumn,
  selectedFeatures,
  onSelectedFeaturesChange,
  recommendedFeatures = [],
  excludedFeatures = {},
  isLoading = false,
  onReloadColumns,
}) => {
  const availableColumns = columns.filter((col) => col !== targetColumn);

  const isIdentifier = (col: string) => {
    return /id$|^id$|^uuid$|identifier|student_id|order_id|customer_id/i.test(col);
  };

  const toggleFeature = (col: string) => {
    if (selectedFeatures.includes(col)) {
      onSelectedFeaturesChange(selectedFeatures.filter((f) => f !== col));
    } else {
      onSelectedFeaturesChange([...selectedFeatures, col]);
    }
  };

  const selectAll = () => {
    onSelectedFeaturesChange(availableColumns);
  };

  const selectRecommended = () => {
    // If explicit recommended features are provided, use those that are not target or identifiers
    if (recommendedFeatures && recommendedFeatures.length > 0) {
      const rec = recommendedFeatures.filter(
        (f) => f !== targetColumn && !isIdentifier(f) && !excludedFeatures[f]
      );
      if (rec.length > 0) {
        onSelectedFeaturesChange(rec);
        return;
      }
    }

    // Default recommendation logic: select all valid non-identifier columns
    const safeCandidates = availableColumns.filter(
      (col) => !isIdentifier(col) && !excludedFeatures[col]
    );
    onSelectedFeaturesChange(safeCandidates.length > 0 ? safeCandidates : availableColumns);
  };

  const clearAll = () => {
    onSelectedFeaturesChange([]);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* Header controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <label style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary, #f1f5f9)", display: "block" }}>
            3. Select Predictor Variables ({selectedFeatures.length} of {availableColumns.length} selected)
          </label>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted, #94a3b8)", display: "block", marginTop: "0.125rem" }}>
            Choose predictor variables for model training. Constant and identifier columns are flagged.
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={selectRecommended}
            disabled={availableColumns.length === 0}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
          >
            Select Recommended
          </button>
          <button
            type="button"
            onClick={selectAll}
            disabled={availableColumns.length === 0}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
          >
            Select All
          </button>
          <button
            type="button"
            onClick={clearAll}
            disabled={selectedFeatures.length === 0}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Validation alert if 0 selected */}
      {availableColumns.length > 0 && selectedFeatures.length === 0 && (
        <div
          style={{
            padding: "0.5rem 0.75rem",
            borderRadius: "6px",
            background: "rgba(245, 158, 11, 0.12)",
            border: "1px solid rgba(245, 158, 11, 0.4)",
            color: "#f59e0b",
            fontSize: "0.75rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <span>⚠️</span>
          <span>Please select at least one predictor variable to train models. Click <strong>Select Recommended</strong> to quickly choose clean features.</span>
        </div>
      )}

      {/* Loading or Empty State */}
      {availableColumns.length === 0 ? (
        <div
          style={{
            padding: "1.5rem",
            borderRadius: "8px",
            background: "var(--bg-subtle, #1e293b50)",
            border: "1px dashed var(--border-subtle, #334155)",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "0.75rem",
          }}
        >
          {isLoading ? (
            <span style={{ fontSize: "0.8125rem", color: "var(--text-muted, #94a3b8)" }}>
              Loading column schema for the selected dataset...
            </span>
          ) : (
            <>
              <span style={{ fontSize: "0.8125rem", color: "var(--text-muted, #94a3b8)" }}>
                No columns loaded yet for this dataset.
              </span>
              {onReloadColumns && (
                <button
                  type="button"
                  onClick={onReloadColumns}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: "0.75rem" }}
                >
                  Retry Loading Columns
                </button>
              )}
            </>
          )}
        </div>
      ) : (
        /* Columns Grid */
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: "0.5rem",
            maxHeight: "260px",
            overflowY: "auto",
            padding: "0.5rem",
            background: "var(--bg-subtle, #0f172a50)",
            borderRadius: "8px",
            border: "1px solid var(--border-subtle, #334155)",
          }}
        >
          {availableColumns.map((col) => {
            const isSelected = selectedFeatures.includes(col);
            const isId = isIdentifier(col);
            const exclusionReason = excludedFeatures[col] || (isId ? "Identifier column (potential leakage)" : undefined);
            const isRecommended = recommendedFeatures.includes(col) || (!isId && !exclusionReason);

            return (
              <div
                key={col}
                onClick={() => toggleFeature(col)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.5rem 0.75rem",
                  borderRadius: "6px",
                  background: isSelected ? "var(--bg-active, rgba(99, 102, 241, 0.12))" : "var(--bg-surface, #1e293b)",
                  border: isSelected ? "1px solid var(--color-primary, #6366f1)" : "1px solid var(--border-subtle, #334155)",
                  cursor: "pointer",
                  userSelect: "none",
                  fontSize: "0.8125rem",
                }}
              >
                <label
                  htmlFor={`feature-checkbox-${col}`}
                  style={{ display: "flex", alignItems: "center", gap: "0.5rem", overflow: "hidden", cursor: "pointer", flex: 1 }}
                >
                  <input
                    id={`feature-checkbox-${col}`}
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}} // handled by parent div
                    aria-label={`Select feature ${col}`}
                    style={{ cursor: "pointer" }}
                  />
                  <span
                    style={{
                      fontWeight: isSelected ? 600 : 400,
                      color: isSelected ? "var(--text-primary, #f8fafc)" : "var(--text-secondary, #cbd5e1)",
                      textOverflow: "ellipsis",
                      overflow: "hidden",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {col}
                  </span>
                </label>

                <div>
                  {exclusionReason ? (
                    <span
                      className="badge badge-warning"
                      title={exclusionReason}
                      style={{ fontSize: "0.6875rem", cursor: "help", background: "rgba(245, 158, 11, 0.2)", color: "#f59e0b" }}
                    >
                      {isId ? "Identifier" : "Flagged"}
                    </span>
                  ) : isRecommended ? (
                    <span
                      className="badge badge-info"
                      style={{ fontSize: "0.6875rem", background: "rgba(59, 130, 246, 0.2)", color: "#60a5fa" }}
                    >
                      Rec
                    </span>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

