"use client";

import React, { useState, useRef } from "react";
import { UploadIcon, CheckIcon, CloseIcon, AlertCircleIcon, RefreshIcon } from "@/components/icons";
import { apiClient } from "@/services/api";

interface UploadedDatasetInfo {
  dataset_id: string;
  status: string;
  filename: string;
  format: string;
  file_size_bytes: number;
  duckdb_table_name: string;
}

interface FileDropzoneProps {
  maxSizeMb?: number;
  onUploadSuccess?: (dataset: UploadedDatasetInfo) => void;
  disabled?: boolean;
}

const SUPPORTED_FORMATS = [
  { label: "CSV", ext: ".csv" },
  { label: "XLSX", ext: ".xlsx" },
  { label: "JSON", ext: ".json" },
  { label: "Parquet", ext: ".parquet" },
];

type IngestionPhase = "idle" | "uploading" | "validating" | "storing" | "ingesting" | "ready" | "failed";

export function FileDropzone({
  maxSizeMb = 100,
  onUploadSuccess,
  disabled = false,
}: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<IngestionPhase>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [completedDataset, setCompletedDataset] = useState<UploadedDatasetInfo | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && phase === "idle") setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled || phase !== "idle") return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processAndUpload(e.target.files[0]);
    }
  };

  const processAndUpload = async (file: File) => {
    setCurrentFile(file);
    setErrorMessage(null);

    // Client-side quick size validation
    const maxBytes = maxSizeMb * 1024 * 1024;
    if (file.size > maxBytes) {
      setPhase("failed");
      const fileSizeMb = (file.size / (1024 * 1024)).toFixed(1);
      setErrorMessage(`The uploaded file (${fileSizeMb} MB) exceeds the Free plan limit of ${maxSizeMb} MB. Need to process larger datasets? Upgrade to Pro (500 MB), Team (2 GB), or Enterprise (10 GB+).`);
      return;
    }

    if (file.size === 0) {
      setPhase("failed");
      setErrorMessage("The uploaded file is empty (0 bytes).");
      return;
    }

    // Progression of real backend status transitions
    try {
      setPhase("uploading");

      // Progress animation simulation for multi-phase pipeline steps
      const progressTimer = setTimeout(() => {
        setPhase("validating");
        setTimeout(() => {
          setPhase("storing");
          setTimeout(() => {
            setPhase("ingesting");
          }, 350);
        }, 350);
      }, 400);

      const result = await apiClient.uploadDataset(file);
      clearTimeout(progressTimer);

      setPhase("ready");
      setCompletedDataset(result);
      onUploadSuccess?.(result);

    } catch (err: any) {
      setPhase("failed");
      setErrorMessage(err.message || "Failed to process dataset upload.");
    }
  };

  const handleReset = () => {
    setCurrentFile(null);
    setPhase("idle");
    setErrorMessage(null);
    setCompletedDataset(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const isProcessing = phase === "uploading" || phase === "validating" || phase === "storing" || phase === "ingesting";

  return (
    <div style={{ width: "100%" }}>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx,.json,.parquet"
        onChange={handleFileInput}
        style={{ display: "none" }}
        disabled={disabled || isProcessing}
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => phase === "idle" && fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${
            isDragOver
              ? "var(--accent-primary)"
              : phase === "ready"
              ? "var(--accent-emerald)"
              : phase === "failed"
              ? "var(--accent-rose)"
              : isProcessing
              ? "var(--accent-amber)"
              : "var(--border-subtle)"
          }`,
          backgroundColor: isDragOver
            ? "rgba(99, 102, 241, 0.06)"
            : phase === "ready"
            ? "rgba(16, 185, 129, 0.03)"
            : phase === "failed"
            ? "rgba(244, 63, 94, 0.03)"
            : isProcessing
            ? "rgba(245, 158, 11, 0.03)"
            : "rgba(255, 255, 255, 0.015)",
          borderRadius: "var(--radius-lg)",
          padding: "3.5rem 2rem",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          cursor: phase === "idle" ? "pointer" : "default",
          transition: "all 0.2s ease",
        }}
      >
        {/* ── Ready / Success State ── */}
        {phase === "ready" && completedDataset ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.85rem", maxWidth: "480px" }}>
            <div
              style={{
                width: "52px",
                height: "52px",
                borderRadius: "50%",
                backgroundColor: "rgba(16, 185, 129, 0.12)",
                color: "var(--accent-emerald)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CheckIcon size={26} />
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}>
                <h4 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  {completedDataset.filename}
                </h4>
                <span className="badge badge-emerald" style={{ fontSize: "0.625rem" }}>
                  Ready
                </span>
              </div>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                Format: <strong style={{ color: "var(--text-secondary)" }}>{completedDataset.format.toUpperCase()}</strong> &bull; Size:{" "}
                <strong style={{ color: "var(--text-secondary)" }}>
                  {(completedDataset.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                </strong> &bull; ID:{" "}
                <code style={{ fontFamily: "var(--font-mono)", color: "var(--accent-primary)" }}>
                  {completedDataset.dataset_id}
                </code>
              </p>
            </div>

            <div style={{ display: "flex", gap: "0.6rem", marginTop: "0.5rem" }}>
              <button
                type="button"
                onClick={handleReset}
                className="btn btn-secondary btn-sm"
                style={{ gap: "0.35rem" }}
              >
                <UploadIcon size={14} />
                <span>Upload Another</span>
              </button>
            </div>
          </div>
        ) : phase === "failed" ? (
          /* ── Failed State ── */
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem", maxWidth: "420px" }}>
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "50%",
                backgroundColor: "rgba(244, 63, 94, 0.12)",
                color: "var(--accent-rose)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <AlertCircleIcon size={24} />
            </div>

            <h4 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Ingestion Failed
            </h4>

            <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
              {errorMessage || "Unable to validate or ingest file."}
            </p>

            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center", flexWrap: "wrap", justifyContent: "center" }}>
              <button
                type="button"
                onClick={handleReset}
                className="btn btn-secondary btn-sm"
                style={{ gap: "0.35rem" }}
              >
                <RefreshIcon size={14} />
                <span>Try Again</span>
              </button>
              {errorMessage?.includes("Free plan limit") && (
                <a
                  href="/settings"
                  className="btn btn-primary btn-sm"
                  style={{ gap: "0.35rem", textDecoration: "none" }}
                >
                  <span>See Plans & Upgrade</span>
                </a>
              )}
            </div>
          </div>
        ) : isProcessing ? (
          /* ── Multi-Stage Ingestion Pipeline Progress ── */
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "50%",
                backgroundColor: "rgba(245, 158, 11, 0.12)",
                color: "var(--accent-amber)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                animation: "shimmer 1.4s infinite ease-in-out",
              }}
            >
              <RefreshIcon size={22} />
            </div>

            <div>
              <h4 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", textTransform: "capitalize" }}>
                {phase === "uploading" && "Uploading file to server…"}
                {phase === "validating" && "Validating tabular structure & encoding…"}
                {phase === "storing" && "Preserving immutable raw storage…"}
                {phase === "ingesting" && "Registering DuckDB analytical view…"}
              </h4>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                {currentFile?.name} &bull; {(currentFile ? currentFile.size / (1024 * 1024) : 0).toFixed(2)} MB
              </p>
            </div>

            {/* Stages indicator steps */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem" }}>
              {["uploading", "validating", "storing", "ingesting"].map((p, idx) => {
                const isActive = phase === p;
                const isPassed =
                  (phase === "validating" && idx === 0) ||
                  (phase === "storing" && idx <= 1) ||
                  (phase === "ingesting" && idx <= 2);

                return (
                  <div key={p} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span
                      style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        backgroundColor: isActive
                          ? "var(--accent-amber)"
                          : isPassed
                          ? "var(--accent-emerald)"
                          : "rgba(255, 255, 255, 0.15)",
                      }}
                    />
                    {idx < 3 && (
                      <span
                        style={{
                          width: "20px",
                          height: "1px",
                          backgroundColor: isPassed ? "var(--accent-emerald)" : "rgba(255, 255, 255, 0.1)",
                        }}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          /* ── Default Idle Dropzone ── */
          <>
            <div
              style={{
                width: "54px",
                height: "54px",
                borderRadius: "50%",
                backgroundColor: "rgba(99, 102, 241, 0.1)",
                color: "#818cf8",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "1rem",
              }}
            >
              <UploadIcon size={26} />
            </div>

            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.35rem" }}>
              Upload your dataset
            </h3>

            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "1.25rem", maxWidth: "380px", lineHeight: 1.5 }}>
              Drag and drop your file here, or{" "}
              <span style={{ color: "var(--accent-primary)", fontWeight: 500, textDecoration: "underline" }}>
                browse files
              </span>{" "}
              from your device
            </p>

            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap", justifyContent: "center" }}>
              {SUPPORTED_FORMATS.map((fmt) => (
                <span key={fmt.label} className="badge badge-neutral" style={{ fontSize: "0.6875rem" }}>
                  {fmt.label}
                </span>
              ))}
            </div>

            <div style={{ marginTop: "0.75rem", fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.35rem", flexWrap: "wrap", justifyContent: "center" }}>
              <span>Free plan: up to {maxSizeMb} MB. Need more?</span>
              <a
                href="/settings"
                onClick={(e) => e.stopPropagation()}
                style={{ color: "var(--accent-primary)", fontWeight: 600, textDecoration: "underline" }}
              >
                See plans →
              </a>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
