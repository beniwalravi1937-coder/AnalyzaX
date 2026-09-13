import React, { useRef, useState } from "react";
import { useDataset } from "@/context/DatasetContext";
import { apiClient } from "@/services/api";
import { Upload, Sparkles, Database, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";

export interface GuidedOnboardingProps {
  title: string;
  description: string;
  badgeText?: string;
  features?: string[];
  icon?: React.ReactNode;
  onUploadSuccess?: () => void;
  compact?: boolean;
}

export function GuidedOnboarding({
  title,
  description,
  badgeText = "Guided Onboarding",
  features = [
    "Instant data preparation & type detection",
    "Deep automated profiling & relationships",
    "Interactive charts & board-ready exports",
  ],
  icon,
  onUploadSuccess,
  compact = false,
}: GuidedOnboardingProps) {
  const { datasets, activeDataset, selectDataset, refreshDatasets, loadSampleDataset } = useDataset();
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingSample, setIsLoadingSample] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      setErrorMessage(null);
      setStatusMessage(`Analyzing & processing ${file.name}...`);
      await apiClient.uploadDataset(file);
      await refreshDatasets();
      setStatusMessage("Dataset loaded successfully!");
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (err: any) {
      console.error("Upload error:", err);
      setErrorMessage(err?.message || "Failed to upload file. Please try a valid CSV, Parquet, or Excel file.");
    } finally {
      setIsUploading(false);
      setTimeout(() => setStatusMessage(null), 3000);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleLoadSample = async () => {
    try {
      setIsLoadingSample(true);
      setErrorMessage(null);
      setStatusMessage("Loading retail analytics sample dataset...");
      const loaded = await loadSampleDataset();
      if (loaded) {
        setStatusMessage("Sample dataset ready! Exploring data...");
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      }
    } catch (err: any) {
      console.error("Failed to load demo:", err);
      setErrorMessage(err?.message || "Could not load sample dataset.");
    } finally {
      setIsLoadingSample(false);
      setTimeout(() => setStatusMessage(null), 3000);
    }
  };

  return (
    <div
      style={{
        width: "100%",
        maxWidth: compact ? "680px" : "860px",
        margin: "0 auto",
        padding: compact ? "1.75rem" : "2.75rem 2rem",
        background: "radial-gradient(ellipse at 50% -20%, rgba(99, 102, 241, 0.15), rgba(15, 23, 42, 0.6) 70%), var(--bg-surface, #0f172a)",
        borderRadius: "16px",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        boxShadow: "0 20px 40px -15px rgba(0, 0, 0, 0.5), 0 0 30px -10px rgba(99, 102, 241, 0.2)",
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Hidden file input for one-click upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.tsv,.parquet,.json,.xlsx"
        style={{ display: "none" }}
        onChange={handleFileChange}
      />

      {/* Decorative top badge */}
      <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.25rem 0.85rem", borderRadius: "9999px", background: "rgba(99, 102, 241, 0.15)", border: "1px solid rgba(99, 102, 241, 0.35)", color: "#a5b4fc", fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "1.25rem" }}>
        <Sparkles style={{ width: "13px", height: "13px" }} />
        {badgeText}
      </div>

      {/* Main icon badge */}
      <div
        style={{
          width: "64px",
          height: "64px",
          borderRadius: "16px",
          background: "linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(168, 85, 247, 0.2))",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 1.25rem auto",
          color: "#818cf8",
          boxShadow: "0 8px 24px -6px rgba(99, 102, 241, 0.4)",
        }}
      >
        {icon || <Database style={{ width: "28px", height: "28px" }} />}
      </div>

      {/* Heading & Benefit Description */}
      <h2
        style={{
          fontSize: compact ? "1.35rem" : "1.75rem",
          fontWeight: 700,
          color: "var(--text-main, #f8fafc)",
          letterSpacing: "-0.02em",
          marginBottom: "0.75rem",
        }}
      >
        {title}
      </h2>
      <p
        style={{
          fontSize: compact ? "0.9rem" : "1rem",
          color: "var(--text-muted, #94a3b8)",
          maxWidth: "600px",
          margin: "0 auto 1.75rem auto",
          lineHeight: 1.6,
        }}
      >
        {description}
      </p>

      {/* 3 Key Feature Pills */}
      {features && features.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "0.75rem",
            marginBottom: "2rem",
          }}
        >
          {features.map((feat, idx) => (
            <div
              key={idx}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.4rem 0.85rem",
                borderRadius: "8px",
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                fontSize: "0.8rem",
                color: "#cbd5e1",
              }}
            >
              <CheckCircle2 style={{ width: "14px", height: "14px", color: "#34d399" }} />
              <span>{feat}</span>
            </div>
          ))}
        </div>
      )}

      {/* Status or Error feedback */}
      {statusMessage && (
        <div
          style={{
            padding: "0.5rem 1rem",
            marginBottom: "1.25rem",
            borderRadius: "8px",
            background: "rgba(52, 211, 153, 0.15)",
            border: "1px solid rgba(52, 211, 153, 0.3)",
            color: "#6ee7b7",
            fontSize: "0.85rem",
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <Loader2 className="animate-spin" style={{ width: "14px", height: "14px" }} />
          {statusMessage}
        </div>
      )}

      {errorMessage && (
        <div
          style={{
            padding: "0.5rem 1rem",
            marginBottom: "1.25rem",
            borderRadius: "8px",
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "#fca5a5",
            fontSize: "0.85rem",
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <AlertCircle style={{ width: "14px", height: "14px" }} />
          {errorMessage}
        </div>
      )}

      {/* Action Buttons: Primary & Secondary */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading || isLoadingSample}
          className="btn btn-primary"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.75rem 1.6rem",
            fontSize: "0.925rem",
            fontWeight: 600,
            borderRadius: "10px",
            background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
            color: "#ffffff",
            border: "none",
            boxShadow: "0 4px 14px rgba(99, 102, 241, 0.4)",
            cursor: isUploading || isLoadingSample ? "not-allowed" : "pointer",
          }}
        >
          {isUploading ? (
            <>
              <Loader2 className="animate-spin" style={{ width: "16px", height: "16px" }} />
              Uploading...
            </>
          ) : (
            <>
              <Upload style={{ width: "16px", height: "16px" }} />
              Upload your first dataset
            </>
          )}
        </button>

        <button
          type="button"
          onClick={handleLoadSample}
          disabled={isUploading || isLoadingSample}
          className="btn btn-secondary"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.75rem 1.4rem",
            fontSize: "0.925rem",
            fontWeight: 500,
            borderRadius: "10px",
            background: "rgba(255, 255, 255, 0.06)",
            color: "#e2e8f0",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            cursor: isUploading || isLoadingSample ? "not-allowed" : "pointer",
          }}
        >
          {isLoadingSample ? (
            <>
              <Loader2 className="animate-spin" style={{ width: "16px", height: "16px" }} />
              Loading demo data...
            </>
          ) : (
            <>
              <Sparkles style={{ width: "16px", height: "16px", color: "#fbbf24" }} />
              Explore with sample dataset
            </>
          )}
        </button>
      </div>

      {/* Alternative: If datasets already exist in account, offer 1-click selection */}
      {datasets && datasets.length > 0 && !activeDataset && (
        <div
          style={{
            marginTop: "1.75rem",
            paddingTop: "1.5rem",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexWrap: "wrap",
            gap: "0.75rem",
            fontSize: "0.85rem",
            color: "var(--text-muted, #94a3b8)",
          }}
        >
          <span>Already uploaded a file?</span>
          <select
            defaultValue=""
            onChange={(e) => {
              if (e.target.value) {
                selectDataset(e.target.value);
                if (onUploadSuccess) onUploadSuccess();
              }
            }}
            className="input input-sm"
            style={{ minWidth: "190px", fontSize: "0.85rem" }}
          >
            <option value="" disabled>
              Select existing dataset...
            </option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name || d.original_filename} ({(d.row_count || 0).toLocaleString()} rows)
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
