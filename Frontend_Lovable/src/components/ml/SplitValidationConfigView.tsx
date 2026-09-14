"use client";

import React from "react";
import { CrossValidationConfig, MLTaskType, SplitConfig } from "@/types/ml";

interface SplitValidationConfigViewProps {
  taskType: MLTaskType;
  splitConfig: SplitConfig;
  onSplitChange: (updated: SplitConfig) => void;
  cvConfig: CrossValidationConfig;
  onCVChange: (updated: CrossValidationConfig) => void;
}

export const SplitValidationConfigView: React.FC<SplitValidationConfigViewProps> = ({
  taskType,
  splitConfig,
  onSplitChange,
  cvConfig,
  onCVChange,
}) => {
  const trainPct = Math.round(splitConfig.train_size * 100);
  const valPct = Math.round(splitConfig.val_size * 100);
  const testPct = Math.round(splitConfig.test_size * 100);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        padding: "1rem",
        borderRadius: "8px",
        background: "var(--bg-subtle)",
        border: "1px solid var(--border-subtle)",
        fontSize: "0.8125rem",
      }}
    >
      {/* Visual Split Distribution Bar */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.375rem" }}>
          <span style={{ fontWeight: 600 }}>Data Partitioning ({trainPct}% Train / {valPct}% Val / {testPct}% Test)</span>
          <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Random Seed: {splitConfig.random_seed}</span>
        </div>

        <div style={{ display: "flex", height: "12px", borderRadius: "6px", overflow: "hidden" }}>
          <div style={{ width: `${trainPct}%`, background: "var(--color-primary, #6366f1)" }} title={`Train: ${trainPct}%`} />
          <div style={{ width: `${valPct}%`, background: "#38bdf8" }} title={`Validation: ${valPct}%`} />
          <div style={{ width: `${testPct}%`, background: "#94a3b8" }} title={`Test: ${testPct}%`} />
        </div>
      </div>

      {/* Split Controls */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
        <div>
          <label style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}>
            Train Proportion ({trainPct}%)
          </label>
          <input
            type="range"
            min="0.50"
            max="0.85"
            step="0.05"
            value={splitConfig.train_size}
            onChange={(e) => {
              const tr = parseFloat(e.target.value);
              const remaining = 1.0 - tr;
              onSplitChange({
                ...splitConfig,
                train_size: tr,
                val_size: Math.round((remaining / 2) * 100) / 100,
                test_size: Math.round((remaining / 2) * 100) / 100,
              });
            }}
            style={{ width: "100%" }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}>
            Random Seed
          </label>
          <input
            type="number"
            value={splitConfig.random_seed}
            onChange={(e) => {
              const seed = parseInt(e.target.value) || 42;
              onSplitChange({ ...splitConfig, random_seed: seed });
              onCVChange({ ...cvConfig, random_seed: seed });
            }}
            className="input"
            style={{ width: "100%", padding: "0.375rem", fontSize: "0.8125rem" }}
          />
        </div>

        {taskType !== "clustering" && (
          <div style={{ display: "flex", alignItems: "center" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontWeight: 600 }}>
              <input
                type="checkbox"
                checked={splitConfig.stratify}
                onChange={(e) => onSplitChange({ ...splitConfig, stratify: e.target.checked })}
              />
              Stratify Classification Splits
            </label>
          </div>
        )}
      </div>

      {/* Cross-Validation Controls */}
      {taskType !== "clustering" && (
        <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "0.75rem", display: "flex", flexWrap: "wrap", alignItems: "center", gap: "1.5rem" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={cvConfig.enabled}
              onChange={(e) => onCVChange({ ...cvConfig, enabled: e.target.checked })}
            />
            Enable Cross-Validation on Training Fold
          </label>

          {cvConfig.enabled && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ color: "var(--text-secondary)" }}>K-Fold Splits:</span>
              <select
                value={cvConfig.n_splits}
                onChange={(e) => onCVChange({ ...cvConfig, n_splits: parseInt(e.target.value) })}
                className="input"
                style={{ padding: "0.25rem 0.5rem", fontSize: "0.8125rem" }}
              >
                <option value={3}>3 Folds</option>
                <option value={5}>5 Folds (Recommended)</option>
                <option value={10}>10 Folds</option>
              </select>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
