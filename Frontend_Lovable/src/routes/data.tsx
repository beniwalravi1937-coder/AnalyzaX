import { createFileRoute } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { Link } from "@/lib/next-compat";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { FileDropzone } from "@/components/ui/FileDropzone";
import { useDataset } from "@/context/DatasetContext";
import { DatasetResponse, DatasetProfileResponse } from "@/types";
import { apiClient } from "@/services/api";
import { DatasetIntelligence } from "@/components/profiling/DatasetIntelligence";
import { ColumnInspectionTable } from "@/components/profiling/ColumnInspectionTable";
import { TargetCandidatesCard } from "@/components/profiling/TargetCandidatesCard";
import {
  DatasetIcon,
  CheckIcon,
  TrashIcon,
  SQLIcon,
  DataQualityIcon,
  RefreshIcon,
  AlertCircleIcon,
} from "@/components/icons";
import { GitCommit, Archive } from "lucide-react";
import { DatasetVersionBrowser } from "@/components/workspace/DatasetVersionBrowser";
import { workspaceApi } from "@/services/workspaceApi";

export const Route = createFileRoute("/data")({
  head: () => ({
    meta: [
      { title: "Data Sources & Intelligence — AnalyzaX" },
      {
        name: "description",
        content:
          "Ingest, validate, and catalog datasets with automated deterministic DuckDB structural profiling and semantic understanding.",
      },
      { property: "og:title", content: "Data Sources & Intelligence — AnalyzaX" },
      {
        property: "og:description",
        content: "Automated deterministic DuckDB structural profiling and semantic understanding.",
      },
    ],
  }),
  component: DataPage,
});

function formatBytes(bytes: number): string {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

function formatDate(dateStr: string): string {
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

function DataPage() {
  const {
    datasets,
    activeDataset,
    isLoading: isDatasetsLoading,
    selectDataset,
    refreshDatasets,
    deleteDataset,
  } = useDataset();

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [showVersionBrowser, setShowVersionBrowser] = useState<boolean>(false);

  const handleArchive = async (datasetId: string) => {
    if (
      !confirm(
        "Are you sure you want to archive this dataset? Historical dashboards and reports referring to it will remain preserved."
      )
    )
      return;
    try {
      await workspaceApi.archiveDataset(datasetId);
      await refreshDatasets();
    } catch (err: any) {
      alert(`Failed to archive dataset: ${err.message}`);
    }
  };

  // Profile state
  const [profile, setProfile] = useState<DatasetProfileResponse | null>(null);
  const [isProfileLoading, setIsProfileLoading] = useState<boolean>(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  const fetchProfile = useCallback(
    async (datasetId: string, force: boolean = false) => {
      setIsProfileLoading(true);
      setProfileError(null);
      try {
        const res = force
          ? await apiClient.refreshDatasetProfile(datasetId)
          : await apiClient.getDatasetProfile(datasetId);
        setProfile(res);
      } catch (err: any) {
        console.warn("Could not load dataset profile:", err);
        setProfileError(err?.message || "Profiling could not be completed.");
        setProfile(null);
      } finally {
        setIsProfileLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (activeDataset && activeDataset.status === "READY") {
      fetchProfile(activeDataset.id, false);
    } else {
      setProfile(null);
      setProfileError(null);
    }
  }, [activeDataset, fetchProfile]);

  const handleDelete = async (datasetId: string, name: string) => {
    if (
      !confirm(
        `Are you sure you want to remove '${name}' from your workspace catalog?`
      )
    ) {
      return;
    }
    setDeletingId(datasetId);
    setDeleteError(null);
    try {
      await deleteDataset(datasetId);
      if (activeDataset?.id === datasetId) {
        setProfile(null);
      }
    } catch (err: any) {
      setDeleteError(err?.message || "Failed to delete dataset.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      <PageHeader
        title="Dataset Management & Intelligence"
        description="Ingest, validate, and catalog datasets with automated deterministic DuckDB structural profiling and semantic understanding."
        badge={{ text: "Phase 4 — Automated Profiling", variant: "emerald" }}
        actions={
          <button
            type="button"
            onClick={() => refreshDatasets()}
            className="btn btn-secondary btn-sm"
            style={{ gap: "0.4rem" }}
            title="Refresh dataset list"
          >
            <RefreshIcon size={14} />
            <span>Refresh</span>
          </button>
        }
      />

      {/* Active Dataset Banner */}
      {activeDataset && (
        <div
          style={{
            padding: "1.25rem 1.5rem",
            background:
              "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(15, 23, 42, 0.6) 100%)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "var(--radius-lg)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "var(--radius-md)",
                backgroundColor: "rgba(16, 185, 129, 0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--accent-emerald)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
              }}
            >
              <DatasetIcon size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <h3
                  style={{
                    margin: 0,
                    fontSize: "1.05rem",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                  }}
                >
                  {activeDataset.original_filename}
                </h3>
                <span
                  className="badge badge-emerald"
                  style={{ fontSize: "0.6875rem" }}
                >
                  Active Dataset
                </span>
                <span
                  className="badge badge-neutral"
                  style={{ fontSize: "0.6875rem", textTransform: "uppercase" }}
                >
                  {activeDataset.format}
                </span>
              </div>
              <div
                style={{
                  display: "flex",
                  gap: "1.2rem",
                  marginTop: "0.3rem",
                  fontSize: "0.8125rem",
                  color: "var(--text-secondary)",
                  flexWrap: "wrap",
                }}
              >
                <span>
                  Size:{" "}
                  <strong style={{ color: "var(--text-primary)" }}>
                    {formatBytes(activeDataset.file_size_bytes)}
                  </strong>
                </span>
                <span>
                  DuckDB View:{" "}
                  <code
                    style={{
                      color: "var(--accent-indigo)",
                      background: "rgba(99, 102, 241, 0.1)",
                      padding: "0.1rem 0.35rem",
                      borderRadius: "4px",
                    }}
                  >
                    {activeDataset.duckdb_table_name}
                  </code>
                </span>
                {activeDataset.sheet_name && (
                  <span>
                    Worksheet:{" "}
                    <strong style={{ color: "var(--text-primary)" }}>
                      {activeDataset.sheet_name}
                    </strong>
                  </span>
                )}
                <span>Uploaded: {formatDate(activeDataset.created_at)}</span>
              </div>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              gap: "0.75rem",
              alignItems: "center",
              flexWrap: "wrap",
            }}
          >
            <button
              type="button"
              onClick={() => setShowVersionBrowser(true)}
              className="btn btn-secondary btn-sm"
              style={{ gap: "0.4rem" }}
            >
              <GitCommit size={14} />
              <span>Versions</span>
            </button>
            <button
              type="button"
              onClick={() => handleArchive(activeDataset.id)}
              className="btn btn-secondary btn-sm"
              style={{ gap: "0.4rem" }}
              title="Archive this dataset"
            >
              <Archive size={14} />
              <span>Archive</span>
            </button>
            <Link
              to="/quality"
              className="btn btn-secondary btn-sm"
              style={{ gap: "0.4rem" }}
            >
              <DataQualityIcon size={14} />
              <span>Data Quality</span>
            </Link>
            <Link
              to="/sql"
              className="btn btn-primary btn-sm"
              style={{ gap: "0.4rem" }}
            >
              <SQLIcon size={14} />
              <span>Query in DuckDB</span>
            </Link>
          </div>
        </div>
      )}

      {/* ── DATASET INTELLIGENCE & PROFILING VIEW ── */}
      {activeDataset && (
        <>
          {/* Profile Loading State */}
          {isProfileLoading && (
            <SectionCard
              title="Automated Dataset Profiling"
              subtitle="Executing out-of-core DuckDB statistical scans and inferring semantic taxonomies..."
            >
              <div style={{ padding: "2.5rem 1rem", textAlign: "center" }}>
                <div
                  style={{
                    display: "inline-block",
                    width: "28px",
                    height: "28px",
                    border: "3px solid rgba(99, 102, 241, 0.2)",
                    borderTopColor: "var(--accent-indigo)",
                    borderRadius: "50%",
                    animation: "spin 0.8s linear infinite",
                    marginBottom: "1rem",
                  }}
                />
                <p
                  style={{
                    margin: 0,
                    fontSize: "0.9375rem",
                    fontWeight: 500,
                    color: "var(--text-primary)",
                  }}
                >
                  Analyzing schema, calculating distributions, and detecting semantic
                  types...
                </p>
                <p
                  style={{
                    margin: "0.35rem 0 0",
                    fontSize: "0.8125rem",
                    color: "var(--text-muted)",
                  }}
                >
                  Stage: Computing quantiles, IQR, variance, and target candidates
                  via DuckDB engine.
                </p>
              </div>
            </SectionCard>
          )}

          {/* Profile Error State */}
          {profileError && !isProfileLoading && (
            <div
              style={{
                padding: "1.25rem 1.5rem",
                borderRadius: "var(--radius-lg)",
                backgroundColor: "rgba(244, 63, 94, 0.08)",
                border: "1px solid rgba(244, 63, 94, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "1rem",
                flexWrap: "wrap",
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
              >
                <AlertCircleIcon size={20} className="text-rose" />
                <div>
                  <h4
                    style={{
                      margin: 0,
                      fontSize: "0.9375rem",
                      fontWeight: 600,
                      color: "var(--accent-rose)",
                    }}
                  >
                    Profiling could not be completed
                  </h4>
                  <p
                    style={{
                      margin: "0.2rem 0 0",
                      fontSize: "0.8125rem",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {profileError}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => fetchProfile(activeDataset.id, true)}
                className="btn btn-secondary btn-sm"
                style={{ gap: "0.4rem" }}
              >
                <RefreshIcon size={14} />
                <span>Retry Profiling</span>
              </button>
            </div>
          )}

          {/* Profile Ready Display */}
          {profile && !isProfileLoading && (
            <>
              {/* High-level Intelligence KPIs */}
              <DatasetIntelligence profile={profile} />

              {/* ML Target Variable Recommendations */}
              {profile.target_candidates.length > 0 && (
                <TargetCandidatesCard candidates={profile.target_candidates} />
              )}

              {/* Column Structural & Statistical Inspector */}
              <SectionCard
                title="Column Structural & Statistical Intelligence"
                subtitle="Inferred semantic roles, exact missingness, continuous quantiles, and category distributions"
                actions={
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.75rem",
                    }}
                  >
                    <span
                      style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}
                    >
                      Engine: {profile.profiling_version}
                    </span>
                    <button
                      type="button"
                      onClick={() => fetchProfile(activeDataset.id, true)}
                      className="btn btn-secondary btn-sm"
                      style={{ gap: "0.35rem", fontSize: "0.75rem" }}
                      title="Force re-scan DuckDB view"
                    >
                      <RefreshIcon size={13} />
                      <span>Refresh Profile</span>
                    </button>
                  </div>
                }
              >
                <ColumnInspectionTable columns={profile.columns} />
              </SectionCard>
            </>
          )}
        </>
      )}

      {/* Upload Zone */}
      <SectionCard
        title="Upload Dataset"
        subtitle="Support for Columnar Parquet, Delimited CSV, Structured JSON, and Excel Spreadsheets (up to 100 MB)."
      >
        <FileDropzone
          maxSizeMb={100}
          onUploadSuccess={(res) => {
            refreshDatasets();
            selectDataset(res.dataset_id);
          }}
        />
      </SectionCard>

      {/* Catalog & Ingestion History */}
      <SectionCard
        title="Workspace Dataset Catalog"
        subtitle="Chronological register of validated and ingested analytical datasets"
        actions={
          <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            {datasets.length} registered{" "}
            {datasets.length === 1 ? "dataset" : "datasets"}
          </span>
        }
      >
        {deleteError && (
          <div
            style={{
              padding: "0.75rem 1rem",
              marginBottom: "1rem",
              backgroundColor: "rgba(244, 63, 94, 0.1)",
              border: "1px solid rgba(244, 63, 94, 0.3)",
              borderRadius: "var(--radius-md)",
              color: "var(--accent-rose)",
              fontSize: "0.875rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <AlertCircleIcon size={16} />
            <span>{deleteError}</span>
          </div>
        )}

        {isDatasetsLoading ? (
          <div
            style={{
              padding: "2.5rem 1rem",
              textAlign: "center",
              color: "var(--text-muted)",
            }}
          >
            Loading dataset catalog...
          </div>
        ) : datasets.length === 0 ? (
          <div style={{ padding: "3rem 1rem", textAlign: "center" }}>
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "50%",
                backgroundColor: "rgba(255, 255, 255, 0.04)",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-muted)",
                marginBottom: "0.75rem",
              }}
            >
              <DatasetIcon size={24} />
            </div>
            <p
              style={{
                margin: 0,
                fontSize: "0.9375rem",
                color: "var(--text-secondary)",
                fontWeight: 500,
              }}
            >
              No datasets registered yet
            </p>
            <p
              style={{
                margin: "0.35rem 0 0",
                fontSize: "0.8125rem",
                color: "var(--text-muted)",
              }}
            >
              Drag and drop a CSV, Parquet, JSON, or Excel file above to begin.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              className="analyzax-table"
              style={{ width: "100%", borderCollapse: "collapse" }}
            >
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>
                    Dataset Name
                  </th>
                  <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>
                    Format
                  </th>
                  <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>
                    File Size
                  </th>
                  <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>
                    DuckDB Identifier
                  </th>
                  <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>
                    Status
                  </th>
                  <th style={{ textAlign: "left", padding: "0.75rem 1rem" }}>
                    Uploaded
                  </th>
                  <th style={{ textAlign: "right", padding: "0.75rem 1rem" }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((ds: DatasetResponse) => {
                  const isActive = activeDataset?.id === ds.id;
                  const isDeleting = deletingId === ds.id;

                  return (
                    <tr
                      key={ds.id}
                      style={{
                        backgroundColor: isActive
                          ? "rgba(16, 185, 129, 0.04)"
                          : "transparent",
                        borderBottom: "1px solid var(--border-subtle)",
                        transition: "background 0.15s ease",
                      }}
                    >
                      <td style={{ padding: "0.85rem 1rem" }}>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "0.6rem",
                          }}
                        >
                          <span
                            style={{
                              fontWeight: 500,
                              color: "var(--text-primary)",
                            }}
                          >
                            {ds.original_filename}
                          </span>
                          {isActive && (
                            <span
                              className="badge badge-emerald"
                              style={{ fontSize: "0.6875rem" }}
                            >
                              Active
                            </span>
                          )}
                        </div>
                        <div
                          style={{
                            fontSize: "0.6875rem",
                            color: "var(--text-muted)",
                            marginTop: "0.15rem",
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {ds.id}
                        </div>
                      </td>
                      <td style={{ padding: "0.85rem 1rem" }}>
                        <span
                          className="badge badge-neutral"
                          style={{
                            fontSize: "0.75rem",
                            textTransform: "uppercase",
                            letterSpacing: "0.03em",
                          }}
                        >
                          {ds.format}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "0.85rem 1rem",
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.8125rem",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {formatBytes(ds.file_size_bytes)}
                      </td>
                      <td style={{ padding: "0.85rem 1rem" }}>
                        <code
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--accent-indigo)",
                            background: "rgba(99, 102, 241, 0.1)",
                            padding: "0.15rem 0.4rem",
                            borderRadius: "4px",
                          }}
                        >
                          {ds.duckdb_table_name}
                        </code>
                      </td>
                      <td style={{ padding: "0.85rem 1rem" }}>
                        <span
                          className={
                            ds.status === "READY"
                              ? "badge badge-emerald"
                              : ds.status === "FAILED"
                              ? "badge badge-rose"
                              : "badge badge-amber"
                          }
                          style={{ fontSize: "0.75rem" }}
                        >
                          {ds.status}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "0.85rem 1rem",
                          fontSize: "0.8125rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        {formatDate(ds.created_at)}
                      </td>
                      <td style={{ padding: "0.85rem 1rem", textAlign: "right" }}>
                        <div
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.5rem",
                          }}
                        >
                          {!isActive ? (
                            <button
                              type="button"
                              onClick={() => selectDataset(ds.id)}
                              className="btn btn-secondary btn-sm"
                              style={{
                                fontSize: "0.75rem",
                                padding: "0.25rem 0.6rem",
                              }}
                            >
                              Select
                            </button>
                          ) : (
                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.25rem",
                                fontSize: "0.75rem",
                                color: "var(--accent-emerald)",
                                fontWeight: 500,
                                padding: "0.25rem 0.5rem",
                              }}
                            >
                              <CheckIcon size={13} />
                              Current
                            </span>
                          )}
                          <button
                            type="button"
                            disabled={isDeleting}
                            onClick={() =>
                              handleDelete(ds.id, ds.original_filename)
                            }
                            className="btn btn-secondary btn-sm"
                            style={{
                              fontSize: "0.75rem",
                              padding: "0.3rem",
                              color: "var(--accent-rose)",
                              borderColor: "transparent",
                            }}
                            title="Delete dataset"
                            aria-label="Delete dataset"
                          >
                            <TrashIcon size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      {activeDataset && (
        <DatasetVersionBrowser
          datasetId={activeDataset.id}
          datasetName={activeDataset.original_filename}
          isOpen={showVersionBrowser}
          onClose={() => setShowVersionBrowser(false)}
        />
      )}
    </div>
  );
}
