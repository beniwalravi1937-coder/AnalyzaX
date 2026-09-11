"use client";

import React from "react";

interface FeatureSelectorProps {
  columns: string[];
  targetColumn: string;
  selectedFeatures: string[];
  onSelectedFeaturesChange: (features: string[]) => void;
  recommendedFeatures: string[];
  excludedFeatures: Record<string, string>;
}

export const FeatureSelector: React.FC<FeatureSelectorProps> = ({
  columns,
  targetColumn,
  selectedFeatures,
  onSelectedFeaturesChange,
  recommendedFeatures,
  excludedFeatures,
}) => {
  const availableColumns = columns.filter((col) => col !== targetColumn);

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
    onSelectedFeaturesChange(recommendedFeatures.filter((f) => f !== targetColumn));
  };

  const clearAll = () => {
    onSelectedFeaturesChange([]);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* Header controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <label style={{ fontSize: "0.875rem", fontWeight: 600 }}>
            3. Select Features ({selectedFeatures.length} of {availableColumns.length} selected)
          </label>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>
            Choose predictor variables for model training. Constant and identifier columns are flagged.
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" onClick={selectRecommended} className="btn btn-secondary btn-sm" style={{ fontSize: "0.75rem" }}>
            Select Recommended
          </button>
          <button type="button" onClick={selectAll} className="btn btn-secondary btn-sm" style={{ fontSize: "0.75rem" }}>
            Select All
          </button>
          <button type="button" onClick={clearAll} className="btn btn-secondary btn-sm" style={{ fontSize: "0.75rem" }}>
            Clear
          </button>
        </div>
      </div>

      {/* Columns Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: "0.5rem",
          maxHeight: "260px",
          overflowY: "auto",
          padding: "0.5rem",
          background: "var(--bg-subtle)",
          borderRadius: "8px",
          border: "1px solid var(--border-subtle)",
        }}
      >
        {availableColumns.map((col) => {
          const isSelected = selectedFeatures.includes(col);
          const exclusionReason = excludedFeatures[col];
          const isRecommended = recommendedFeatures.includes(col);

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
                background: isSelected ? "var(--bg-active, #6366f110)" : "var(--bg-surface)",
                border: isSelected ? "1px solid var(--color-primary, #6366f1)" : "1px solid var(--border-subtle)",
                cursor: "pointer",
                userSelect: "none",
                fontSize: "0.8125rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", overflow: "hidden" }}>
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {}} // handled by parent div
                  style={{ cursor: "pointer" }}
                />
                <span style={{ fontWeight: isSelected ? 600 : 400, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                  {col}
                </span>
              </div>

              <div>
                {exclusionReason ? (
                  <span
                    className="badge badge-warning"
                    title={exclusionReason}
                    style={{ fontSize: "0.6875rem", cursor: "help" }}
                  >
                    Excluded
                  </span>
                ) : isRecommended ? (
                  <span className="badge badge-info" style={{ fontSize: "0.6875rem" }}>
                    Rec
                  </span>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
