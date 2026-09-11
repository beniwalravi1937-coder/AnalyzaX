"use client";

import React from "react";
import { PreprocessingConfig } from "@/types/ml";

interface PreprocessingConfigViewProps {
  config: PreprocessingConfig;
  onChange: (updated: PreprocessingConfig) => void;
}

export const PreprocessingConfigView: React.FC<PreprocessingConfigViewProps> = ({
  config,
  onChange,
}) => {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "1rem",
        padding: "1rem",
        borderRadius: "8px",
        background: "var(--bg-subtle)",
        border: "1px solid var(--border-subtle)",
        fontSize: "0.8125rem",
      }}
    >
      {/* Numeric Imputation */}
      <div>
        <label style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}>
          Numeric Imputation
        </label>
        <select
          value={config.numeric_impute}
          onChange={(e) => onChange({ ...config, numeric_impute: e.target.value as any })}
          className="input"
          style={{ width: "100%", padding: "0.375rem", fontSize: "0.8125rem" }}
        >
          <option value="median">Median (Default, robust to outliers)</option>
          <option value="mean">Mean (Arithmetic average)</option>
          <option value="constant">Constant Fill Value</option>
        </select>
      </div>

      {/* Numeric Scaling */}
      <div>
        <label style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}>
          Numeric Scaling
        </label>
        <select
          value={config.numeric_scale}
          onChange={(e) => onChange({ ...config, numeric_scale: e.target.value as any })}
          className="input"
          style={{ width: "100%", padding: "0.375rem", fontSize: "0.8125rem" }}
        >
          <option value="standard">StandardScaler (Zero mean, unit variance)</option>
          <option value="minmax">MinMaxScaler ([0, 1] range)</option>
          <option value="robust">RobustScaler (Median and IQR)</option>
          <option value="passthrough">Passthrough (No scaling)</option>
        </select>
      </div>

      {/* Categorical Encoding */}
      <div>
        <label style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}>
          Categorical Encoding
        </label>
        <select
          value={config.categorical_encode}
          onChange={(e) => onChange({ ...config, categorical_encode: e.target.value as any })}
          className="input"
          style={{ width: "100%", padding: "0.375rem", fontSize: "0.8125rem" }}
        >
          <option value="one_hot">One-Hot Encoding (Ignore unseen)</option>
          <option value="ordinal">Ordinal Encoding (Integer indices)</option>
        </select>
      </div>

      {/* Date Features Toggle */}
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontWeight: 600 }}>
          <input
            type="checkbox"
            checked={config.extract_date_features}
            onChange={(e) => onChange({ ...config, extract_date_features: e.target.checked })}
          />
          Extract Date/Time Features
        </label>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
          Extracts year, month, day, and day-of-week from date columns.
        </span>
      </div>
    </div>
  );
};
