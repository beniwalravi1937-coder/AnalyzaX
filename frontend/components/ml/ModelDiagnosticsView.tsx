"use client";

import React, { useState } from "react";
import { MLModelRun, MLResult } from "@/types/ml";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";

interface ModelDiagnosticsViewProps {
  modelRun: MLModelRun;
  result: MLResult;
}

export const ModelDiagnosticsView: React.FC<ModelDiagnosticsViewProps> = ({
  modelRun,
  result,
}) => {
  const [activeTab, setActiveTab] = useState<"visuals" | "metrics" | "errors" | "params">("visuals");

  const taskType = modelRun.task_type;
  const isRegression = taskType === "regression";
  const isClassification = taskType === "binary_classification" || taskType === "multiclass_classification";
  const isClustering = taskType === "clustering";

  return (
    <div
      style={{
        borderRadius: "8px",
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        padding: "1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <h4 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>
              Deep Diagnostics: {modelRun.model_name}
            </h4>
            <span className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>{taskType}</span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem", display: "block" }}>
            Run ID: {modelRun.model_run_id} · Artifact: {modelRun.artifact_reference || "Registered"}
          </span>
        </div>

        {/* Sub-tabs */}
        <div style={{ display: "flex", gap: "0.375rem" }}>
          <button
            type="button"
            onClick={() => setActiveTab("visuals")}
            className={`btn btn-sm ${activeTab === "visuals" ? "btn-primary" : "btn-secondary"}`}
            style={{ fontSize: "0.75rem" }}
          >
            Diagnostics Charts
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("metrics")}
            className={`btn btn-sm ${activeTab === "metrics" ? "btn-primary" : "btn-secondary"}`}
            style={{ fontSize: "0.75rem" }}
          >
            All Metrics
          </button>
          {isRegression && modelRun.residual_diagnostics && (
            <button
              type="button"
              onClick={() => setActiveTab("errors")}
              className={`btn btn-sm ${activeTab === "errors" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.75rem" }}
            >
              Largest Errors
            </button>
          )}
          <button
            type="button"
            onClick={() => setActiveTab("params")}
            className={`btn btn-sm ${activeTab === "params" ? "btn-primary" : "btn-secondary"}`}
            style={{ fontSize: "0.75rem" }}
          >
            Parameters
          </button>
        </div>
      </div>

      {/* Primary Metrics Summary Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "0.75rem",
          padding: "0.75rem",
          background: "var(--bg-subtle)",
          borderRadius: "6px",
        }}
      >
        {Object.entries(modelRun.metrics).map(([key, val]) => (
          <div key={key}>
            <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase", display: "block" }}>
              {key}
            </span>
            <strong style={{ fontSize: "1rem", fontFamily: "monospace" }}>
              {typeof val === "number" ? val : String(val)}
            </strong>
          </div>
        ))}
      </div>

      {/* TAB: Diagnostic Charts via Phase 9 ChartRenderer */}
      {activeTab === "visuals" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {result.visualizations && result.visualizations.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: "1rem" }}>
              {result.visualizations.map((spec: any, idx: number) => (
                <div
                  key={spec.chart_id || idx}
                  style={{
                    padding: "1rem",
                    borderRadius: "8px",
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <h5 style={{ margin: "0 0 0.25rem 0", fontSize: "0.875rem" }}>{spec.title}</h5>
                  {spec.subtitle && (
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.5rem" }}>
                      {spec.subtitle}
                    </span>
                  )}
                  <ChartRenderer spec={spec} height={280} />
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
              No visual diagnostics generated for this model run.
            </div>
          )}

          {/* Classification Per-Class Report */}
          {isClassification && modelRun.confusion_matrix?.per_class_metrics && (
            <div>
              <h5 style={{ margin: "0 0 0.5rem 0", fontSize: "0.875rem" }}>Per-Class Classification Report</h5>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem", textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "var(--bg-subtle)", borderBottom: "1px solid var(--border-subtle)" }}>
                      <th style={{ padding: "0.5rem" }}>Class</th>
                      <th style={{ padding: "0.5rem" }}>Precision</th>
                      <th style={{ padding: "0.5rem" }}>Recall</th>
                      <th style={{ padding: "0.5rem" }}>F1-Score</th>
                      <th style={{ padding: "0.5rem" }}>Support</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(modelRun.confusion_matrix.per_class_metrics).map(([cls, rep]) => (
                      <tr key={cls} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        <td style={{ padding: "0.5rem", fontWeight: 600 }}>{cls}</td>
                        <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{rep.precision}</td>
                        <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{rep.recall}</td>
                        <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{rep.f1}</td>
                        <td style={{ padding: "0.5rem", color: "var(--text-muted)" }}>{rep.support}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB: All Metrics */}
      {activeTab === "metrics" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <h5 style={{ margin: "0 0 0.5rem 0", fontSize: "0.875rem" }}>Holdout Validation Metrics</h5>
            <pre
              style={{
                padding: "0.75rem",
                borderRadius: "6px",
                background: "var(--bg-subtle)",
                border: "1px solid var(--border-subtle)",
                fontSize: "0.75rem",
                overflowX: "auto",
              }}
            >
              {JSON.stringify(modelRun.metrics, null, 2)}
            </pre>
          </div>

          {modelRun.test_metrics && (
            <div>
              <h5 style={{ margin: "0 0 0.5rem 0", fontSize: "0.875rem" }}>Test Partition Metrics</h5>
              <pre
                style={{
                  padding: "0.75rem",
                  borderRadius: "6px",
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-subtle)",
                  fontSize: "0.75rem",
                  overflowX: "auto",
                }}
              >
                {JSON.stringify(modelRun.test_metrics, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* TAB: Largest Errors (Regression) */}
      {activeTab === "errors" && isRegression && modelRun.residual_diagnostics && (
        <div>
          <h5 style={{ margin: "0 0 0.5rem 0", fontSize: "0.875rem" }}>Top 5 Largest Prediction Errors</h5>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "var(--bg-subtle)", borderBottom: "1px solid var(--border-subtle)" }}>
                  <th style={{ padding: "0.5rem" }}>Row #</th>
                  <th style={{ padding: "0.5rem" }}>Actual</th>
                  <th style={{ padding: "0.5rem" }}>Predicted</th>
                  <th style={{ padding: "0.5rem" }}>Absolute Error</th>
                </tr>
              </thead>
              <tbody>
                {modelRun.residual_diagnostics.largest_errors.map((err, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.5rem", color: "var(--text-muted)" }}>{err.row_index}</td>
                    <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{err.actual}</td>
                    <td style={{ padding: "0.5rem", fontFamily: "monospace" }}>{err.predicted}</td>
                    <td style={{ padding: "0.5rem", fontFamily: "monospace", color: "var(--color-error, #ef4444)", fontWeight: 600 }}>
                      {err.error}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB: Hyperparameters */}
      {activeTab === "params" && (
        <div>
          <h5 style={{ margin: "0 0 0.5rem 0", fontSize: "0.875rem" }}>Fitted Model Parameters</h5>
          <pre
            style={{
              padding: "0.75rem",
              borderRadius: "6px",
              background: "var(--bg-subtle)",
              border: "1px solid var(--border-subtle)",
              fontSize: "0.75rem",
              overflowX: "auto",
            }}
          >
            {JSON.stringify(modelRun.parameters, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
