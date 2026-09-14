"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ExportJob,
  SOURCE_TYPE_LABELS,
  FORMAT_LABELS,
} from "@/types/exports";
import { listExports, deleteExport, downloadExport } from "@/services/exportApi";

interface ExportHistoryTableProps {
  datasetId?: string;
  onJobDeleted?: () => void;
  refreshTrigger?: number;
}

function formatBytes(bytes?: number): string {
  if (!bytes || bytes <= 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export function ExportHistoryTable({
  datasetId,
  onJobDeleted,
  refreshTrigger = 0,
}: ExportHistoryTableProps) {
  const [jobs, setJobs] = useState<ExportJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listExports(datasetId);
      setJobs(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load export history";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs, refreshTrigger]);

  const handleDelete = async (jobId: string) => {
    if (!confirm("Are you sure you want to delete this export artifact?")) return;
    setDeletingId(jobId);
    try {
      await deleteExport(jobId);
      setJobs((prev) => prev.filter((j) => j.job_id !== jobId));
      if (onJobDeleted) onJobDeleted();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownload = async (jobId: string) => {
    setDownloadingId(jobId);
    try {
      await downloadExport(jobId);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloadingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span
            style={{
              padding: "0.2rem 0.5rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              background: "rgba(16, 185, 129, 0.15)",
              color: "#10b981",
            }}
          >
            ✓ Completed
          </span>
        );
      case "FAILED":
        return (
          <span
            style={{
              padding: "0.2rem 0.5rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              background: "rgba(239, 68, 68, 0.15)",
              color: "#ef4444",
            }}
          >
            ✕ Failed
          </span>
        );
      case "PROCESSING":
      case "PENDING":
        return (
          <span
            style={{
              padding: "0.2rem 0.5rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              background: "rgba(59, 130, 246, 0.15)",
              color: "#3b82f6",
            }}
          >
            ⏳ {status}
          </span>
        );
      case "EXPIRED":
        return (
          <span
            style={{
              padding: "0.2rem 0.5rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              background: "rgba(107, 114, 128, 0.15)",
              color: "#9ca3af",
            }}
          >
            ⌛ Expired
          </span>
        );
      default:
        return <span>{status}</span>;
    }
  };

  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        padding: "1.25rem",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Export History & Generated Artifacts
          </h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            Auditable log of generated reports, tabular extracts, and analytical artifacts.
          </p>
        </div>
        <button
          onClick={fetchJobs}
          disabled={loading}
          className="btn btn-secondary btn-sm"
          style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}
        >
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: "0.75rem",
            marginBottom: "1rem",
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "0.375rem",
            color: "#ef4444",
            fontSize: "0.8125rem",
          }}
        >
          {error}
        </div>
      )}

      {loading && jobs.length === 0 ? (
        <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
          Loading export history...
        </div>
      ) : jobs.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "3rem 1rem",
            border: "1px dashed var(--border-subtle)",
            borderRadius: "0.375rem",
          }}
        >
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📦</div>
          <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
            No exports generated yet
          </div>
          <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            Use the Quick Export or Report Builder above to generate your first artifact.
          </div>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "0.8125rem",
              textAlign: "left",
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid var(--border-subtle)",
                  color: "var(--text-secondary)",
                }}
              >
                <th style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>File Name</th>
                <th style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>Source</th>
                <th style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>Format</th>
                <th style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>Size / Rows</th>
                <th style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>Status</th>
                <th style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>Created</th>
                <th style={{ padding: "0.6rem 0.75rem", fontWeight: 600, textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr
                  key={job.job_id}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    transition: "background 0.15s ease",
                  }}
                >
                  <td style={{ padding: "0.6rem 0.75rem", color: "var(--text-primary)", fontWeight: 500 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <span>{job.file_name || job.job_id.slice(0, 12)}</span>
                      {job.provenance?.is_stale && (
                        <span
                          title={`Stale: ${job.provenance.stale_reason || "Dataset modified since export"}`}
                          style={{
                            cursor: "help",
                            fontSize: "0.7rem",
                            padding: "0.1rem 0.35rem",
                            borderRadius: "4px",
                            background: "rgba(245, 158, 11, 0.15)",
                            color: "#f59e0b",
                            fontWeight: 600,
                          }}
                        >
                          ⚠️ STALE
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: "0.6rem 0.75rem", color: "var(--text-secondary)" }}>
                    {SOURCE_TYPE_LABELS[job.source_type] || job.source_type}
                  </td>
                  <td style={{ padding: "0.6rem 0.75rem" }}>
                    <span
                      style={{
                        padding: "0.15rem 0.4rem",
                        borderRadius: "4px",
                        fontSize: "0.725rem",
                        fontWeight: 600,
                        background: "rgba(99, 102, 241, 0.12)",
                        color: "var(--brand-primary, #6366f1)",
                      }}
                    >
                      {FORMAT_LABELS[job.format] || job.format}
                    </span>
                  </td>
                  <td style={{ padding: "0.6rem 0.75rem", color: "var(--text-secondary)" }}>
                    {formatBytes(job.file_size_bytes)}
                    {job.row_count != null && ` • ${job.row_count.toLocaleString()} rows`}
                  </td>
                  <td style={{ padding: "0.6rem 0.75rem" }}>{getStatusBadge(job.status)}</td>
                  <td style={{ padding: "0.6rem 0.75rem", color: "var(--text-secondary)" }}>
                    {formatDate(job.created_at)}
                  </td>
                  <td style={{ padding: "0.6rem 0.75rem", textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "0.4rem" }}>
                      {job.status === "COMPLETED" && (
                        <button
                          onClick={() => handleDownload(job.job_id)}
                          disabled={downloadingId === job.job_id}
                          className="btn btn-primary btn-sm"
                          style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
                          title="Download file"
                        >
                          {downloadingId === job.job_id ? "..." : "⬇ Download"}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(job.job_id)}
                        disabled={deletingId === job.job_id}
                        className="btn btn-ghost btn-sm"
                        style={{
                          padding: "0.25rem 0.5rem",
                          fontSize: "0.75rem",
                          color: "var(--text-secondary)",
                        }}
                        title="Delete export job"
                      >
                        {deletingId === job.job_id ? "..." : "🗑"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
