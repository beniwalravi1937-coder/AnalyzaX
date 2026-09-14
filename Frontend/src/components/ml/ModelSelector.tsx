"use client";

import React, { useState } from "react";
import {
  HyperparameterSearchConfig,
  MLModelDefinition,
  MLTaskType,
} from "@/types/ml";

interface ModelSelectorProps {
  taskType: MLTaskType;
  availableModels: MLModelDefinition[];
  selectedModelIds: string[];
  onSelectedModelIdsChange: (ids: string[]) => void;
  modelParameters: Record<string, Record<string, any>>;
  onModelParametersChange: (params: Record<string, Record<string, any>>) => void;
  searchConfig: HyperparameterSearchConfig;
  onSearchConfigChange: (config: HyperparameterSearchConfig) => void;
  isAdvanced: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  taskType,
  availableModels,
  selectedModelIds,
  onSelectedModelIdsChange,
  modelParameters,
  onModelParametersChange,
  searchConfig,
  onSearchConfigChange,
  isAdvanced,
}) => {
  const [expandedModelId, setExpandedModelId] = useState<string | null>(null);

  // Filter models for task and exclude dummy baseline from candidate selection (it's auto-added by engine)
  const candidateModels = availableModels.filter(
    (m) => m.task_types.includes(taskType) && !m.model_id.startsWith("dummy")
  );

  const toggleModel = (id: string) => {
    if (selectedModelIds.includes(id)) {
      onSelectedModelIdsChange(selectedModelIds.filter((m) => m !== id));
    } else {
      onSelectedModelIdsChange([...selectedModelIds, id]);
    }
  };

  const handleParamChange = (modelId: string, paramName: string, value: any) => {
    const current = modelParameters[modelId] || {};
    onModelParametersChange({
      ...modelParameters,
      [modelId]: {
        ...current,
        [paramName]: value,
      },
    });
  };

  const selectAll = () => {
    onSelectedModelIdsChange(candidateModels.map((m) => m.model_id));
  };

  const selectRecommended = () => {
    const top = candidateModels.slice(0, 2).map((m) => m.model_id);
    onSelectedModelIdsChange(top.length > 0 ? top : candidateModels.map((m) => m.model_id));
  };

  const clearAll = () => {
    onSelectedModelIdsChange([]);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <label style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary, #f1f5f9)", display: "block" }}>
            4. Select Algorithms to Train ({selectedModelIds.length} selected)
          </label>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted, #94a3b8)", display: "block", marginTop: "0.125rem" }}>
            A baseline reference model is automatically included for objective performance benchmarking.
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={selectRecommended}
            disabled={candidateModels.length === 0}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
          >
            Select Recommended
          </button>
          <button
            type="button"
            onClick={selectAll}
            disabled={candidateModels.length === 0}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
          >
            Select All
          </button>
          <button
            type="button"
            onClick={clearAll}
            disabled={selectedModelIds.length === 0}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Validation warning if 0 selected */}
      {candidateModels.length > 0 && selectedModelIds.length === 0 && (
        <div
          style={{
            padding: "0.5rem 0.75rem",
            borderRadius: "6px",
            background: "rgba(245, 158, 11, 0.12)",
            border: "1px solid rgba(245, 158, 11, 0.4)",
            color: "#f59e0b",
            fontSize: "0.75rem",
          }}
        >
          ⚠️ Please select at least one algorithm to train.
        </div>
      )}

      {candidateModels.length === 0 ? (
        <div
          style={{
            padding: "1.5rem",
            borderRadius: "8px",
            background: "var(--bg-subtle, #1e293b50)",
            border: "1px dashed var(--border-subtle, #334155)",
            textAlign: "center",
            color: "var(--text-muted, #94a3b8)",
            fontSize: "0.8125rem",
          }}
        >
          Loading supported algorithms for {taskType.replace("_", " ")}...
        </div>
      ) : (
        /* Model Cards */
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "0.75rem" }}>
        {candidateModels.map((model) => {
          const isSelected = selectedModelIds.includes(model.model_id);
          const isExpanded = expandedModelId === model.model_id;
          const currentParams = { ...model.default_parameters, ...(modelParameters[model.model_id] || {}) };

          return (
            <div
              key={model.model_id}
              style={{
                borderRadius: "8px",
                border: isSelected ? "1px solid var(--color-primary, #6366f1)" : "1px solid var(--border-subtle)",
                background: isSelected ? "var(--bg-active, #6366f108)" : "var(--bg-surface)",
                padding: "0.875rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
                transition: "all 0.15s ease",
              }}
            >
              {/* Header */}
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.5rem" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontWeight: 600, fontSize: "0.875rem" }}>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleModel(model.model_id)}
                  />
                  <span>{model.display_name}</span>
                </label>

                {isAdvanced && model.parameter_schema.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setExpandedModelId(isExpanded ? null : model.model_id)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: "0.6875rem", padding: "0.2rem 0.4rem" }}
                  >
                    {isExpanded ? "Close" : "Params"}
                  </button>
                )}
              </div>

              {/* Description */}
              <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.35 }}>
                {model.description}
              </p>

              {/* Capability Badges */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.375rem", marginTop: "auto", paddingTop: "0.25rem" }}>
                {model.supports_probability && <span className="badge badge-info" style={{ fontSize: "0.6875rem" }}>Probabilities</span>}
                {model.supports_feature_importance && <span className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>Feature Importance</span>}
                {model.supports_coefficients && <span className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>Coefficients</span>}
                <span className="badge badge-neutral" style={{ fontSize: "0.6875rem", color: "#cbd5e1" }}>
                  {model.resource_class}
                </span>
              </div>

              {/* Hyperparameter Accordion (Advanced Mode) */}
              {isAdvanced && isExpanded && (
                <div
                  style={{
                    marginTop: "0.5rem",
                    padding: "0.625rem",
                    borderRadius: "6px",
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-subtle)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.5rem",
                    fontSize: "0.75rem",
                  }}
                >
                  <span style={{ fontWeight: 600, color: "var(--text-muted)" }}>Hyperparameters:</span>
                  {model.parameter_schema.map((p) => (
                    <div key={p.name} style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>{p.display_name}:</span>
                        <strong style={{ fontFamily: "monospace" }}>{String(currentParams[p.name])}</strong>
                      </div>
                      {p.param_type === "int" || p.param_type === "float" ? (
                        <input
                          type="number"
                          value={currentParams[p.name] ?? p.default}
                          min={p.min_val}
                          max={p.max_val}
                          step={p.param_type === "float" ? 0.05 : 1}
                          onChange={(e) =>
                            handleParamChange(
                              model.model_id,
                              p.name,
                              p.param_type === "float" ? parseFloat(e.target.value) : parseInt(e.target.value)
                            )
                          }
                          className="input"
                          style={{ padding: "0.2rem 0.4rem", fontSize: "0.75rem" }}
                        />
                      ) : p.param_type === "choice" && p.allowed_values ? (
                        <select
                          value={currentParams[p.name] ?? p.default}
                          onChange={(e) => handleParamChange(model.model_id, p.name, e.target.value)}
                          className="input"
                          style={{ padding: "0.2rem 0.4rem", fontSize: "0.75rem" }}
                        >
                          {p.allowed_values.map((val) => (
                            <option key={val} value={val}>
                              {val}
                            </option>
                          ))}
                        </select>
                      ) : p.param_type === "bool" ? (
                        <label style={{ display: "flex", alignItems: "center", gap: "0.375rem", cursor: "pointer" }}>
                          <input
                            type="checkbox"
                            checked={Boolean(currentParams[p.name] ?? p.default)}
                            onChange={(e) => handleParamChange(model.model_id, p.name, e.target.checked)}
                          />
                          Enable {p.display_name}
                        </label>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        </div>
      )}

      {/* Hyperparameter Automated Search (Advanced Mode) */}
      {isAdvanced && (
        <div
          style={{
            padding: "0.875rem",
            borderRadius: "8px",
            background: "var(--bg-subtle)",
            border: "1px solid var(--border-subtle)",
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem",
            fontSize: "0.8125rem",
          }}
        >
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={searchConfig.enabled}
              onChange={(e) => onSearchConfigChange({ ...searchConfig, enabled: e.target.checked })}
            />
            Bounded Hyperparameter Search (GridSearchCV / RandomizedSearchCV)
          </label>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Automatically explores hyperparameter candidates with bounded search iterations and time limits.
          </span>

          {searchConfig.enabled && (
            <div style={{ display: "flex", gap: "1rem", marginTop: "0.25rem", flexWrap: "wrap" }}>
              <div>
                <span style={{ color: "var(--text-secondary)", marginRight: "0.5rem" }}>Method:</span>
                <select
                  value={searchConfig.search_method}
                  onChange={(e) => onSearchConfigChange({ ...searchConfig, search_method: e.target.value as any })}
                  className="input"
                  style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }}
                >
                  <option value="random">RandomizedSearchCV (Bounded, fast)</option>
                  <option value="grid">GridSearchCV (Exhaustive over grid)</option>
                </select>
              </div>

              <div>
                <span style={{ color: "var(--text-secondary)", marginRight: "0.5rem" }}>Max Iterations:</span>
                <input
                  type="number"
                  min="2"
                  max="20"
                  value={searchConfig.n_iter}
                  onChange={(e) => onSearchConfigChange({ ...searchConfig, n_iter: parseInt(e.target.value) || 10 })}
                  className="input"
                  style={{ width: "60px", padding: "0.2rem 0.4rem", fontSize: "0.75rem" }}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
