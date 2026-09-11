"use client";

import React, { useState } from "react";
import { MLModelRun, MLResult, PredictionResult } from "@/types/ml";
import { mlApi } from "@/services/mlApi";

interface PredictionRunnerProps {
  result: MLResult;
  selectedModelRun: MLModelRun;
}

export const PredictionRunner: React.FC<PredictionRunnerProps> = ({
  result,
  selectedModelRun,
}) => {
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const features = result.features;

  const handleInputChange = (feat: string, val: string) => {
    setInputValues({ ...inputValues, [feat]: val });
  };

  const handleRunPrediction = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // Convert numeric fields where appropriate
      const parsedRow: Record<string, any> = {};
      for (const f of features) {
        const raw = inputValues[f] ?? "";
        if (raw !== "" && !isNaN(Number(raw))) {
          parsedRow[f] = Number(raw);
        } else {
          parsedRow[f] = raw;
        }
      }

      const pred = await mlApi.predict(selectedModelRun.model_run_id, {
        rows: [parsedRow],
      });
      setPrediction(pred);
    } catch (err: any) {
      setErrorMsg(err.message || "Prediction execution failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePredictOnDatasetVersion = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const pred = await mlApi.predict(selectedModelRun.model_run_id, {
        dataset_id: result.dataset_id,
        dataset_version_id: result.dataset_version_id,
      });
      setPrediction(pred);
    } catch (err: any) {
      setErrorMsg(err.message || "Batch prediction failed");
    } finally {
      setIsLoading(false);
    }
  };

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
      <div>
        <h4 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 600 }}>
          Interactive Inference: {selectedModelRun.model_name}
        </h4>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Run real-time predictions using the persistent model artifact ({selectedModelRun.model_run_id}).
        </span>
      </div>

      {errorMsg && (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderRadius: "6px",
            background: "var(--error-bg, #ef444415)",
            border: "1px solid var(--error-border, #ef444455)",
            color: "var(--color-error, #ef4444)",
            fontSize: "0.8125rem",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Feature Inputs Grid */}
      <div>
        <span style={{ fontSize: "0.8125rem", fontWeight: 600, display: "block", marginBottom: "0.5rem" }}>
          Input Feature Values:
        </span>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.75rem" }}>
          {features.map((feat) => (
            <div key={feat}>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 500, marginBottom: "0.25rem" }}>
                {feat}
              </label>
              <input
                type="text"
                placeholder="Enter value"
                value={inputValues[feat] ?? ""}
                onChange={(e) => handleInputChange(feat, e.target.value)}
                className="input"
                style={{ width: "100%", padding: "0.375rem 0.5rem", fontSize: "0.8125rem" }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={handleRunPrediction}
          disabled={isLoading}
          className="btn btn-primary btn-sm"
        >
          {isLoading ? "Executing Prediction..." : "Predict on Input Row"}
        </button>
        <button
          type="button"
          onClick={handlePredictOnDatasetVersion}
          disabled={isLoading}
          className="btn btn-secondary btn-sm"
        >
          Predict on Dataset Version ({result.dataset_version_id})
        </button>
      </div>

      {/* Prediction Output */}
      {prediction && (
        <div
          style={{
            padding: "1rem",
            borderRadius: "6px",
            background: "var(--bg-subtle)",
            border: "1px solid var(--border-subtle)",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 600, fontSize: "0.875rem" }}>Prediction Output</span>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              ID: {prediction.prediction_id} · {prediction.row_count} row(s)
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
            <div>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>
                Predicted Result:
              </span>
              <strong style={{ fontSize: "1.25rem", color: "var(--color-primary, #6366f1)", fontFamily: "monospace" }}>
                {prediction.predictions.length === 1
                  ? String(prediction.predictions[0])
                  : `Batch: ${prediction.predictions.slice(0, 3).join(", ")}... (${prediction.row_count} total)`}
              </strong>
            </div>

            {/* Class Probabilities */}
            {prediction.probabilities && prediction.probabilities.length > 0 && (
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.25rem" }}>
                  Class Probabilities:
                </span>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  {Object.entries(prediction.probabilities[0]).map(([cls, prob]) => (
                    <span key={cls} className="badge badge-info" style={{ fontSize: "0.75rem" }}>
                      {cls}: {(prob * 100).toFixed(1)}%
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
