import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { useDataset } from "@/context/DatasetContext";
import { apiClient, ApiError } from "@/services/api";
import {
  DataQualityReportResponse,
  QualityDimension,
  QualitySeverity,
} from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { DataQualityIcon, UploadIcon, RefreshIcon, AlertCircleIcon } from "@/components/icons";
import { QualityScoreCard } from "@/components/quality/QualityScoreCard";
import { DimensionCards } from "@/components/quality/DimensionCards";
import { IssueSummaryBar } from "@/components/quality/IssueSummaryBar";
import { QualityIssuesTable } from "@/components/quality/QualityIssuesTable";
import { ColumnQualityTable } from "@/components/quality/ColumnQualityTable";

export const Route = createFileRoute("/quality")({
  head: () => ({
    meta: [
      { title: "Data Quality Assessment — AnalyzaX" },
      {
        name: "description",
        content:
          "Deterministic auditing of completeness, uniqueness, domain validity, category consistency, and anomaly risk.",
      },
      { property: "og:title", content: "Data Quality Assessment — AnalyzaX" },
      {
        property: "og:description",
        content: "Deterministic 6-dimension data quality auditing powered by DuckDB.",
      },
    ],
  }),
  component: DataQualityPage,
});

function DataQualityPage() {
  const { activeDataset, isLoading: isDatasetLoading } = useDataset();

  const [report, setReport] = useState<DataQualityReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters for issues table
  const [selectedSeverity, setSelectedSeverity] = useState<QualitySeverity | null>(null);
  const [selectedDimension, setSelectedDimension] = useState<QualityDimension | null>(null);

  const fetchQualityReport = useCallback(
    async (forceRefresh = false) => {
      if (!activeDataset) {
        setReport(null);
        return;
      }

      if (forceRefresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      try {
        const data = forceRefresh
          ? await apiClient.refreshDatasetQuality(activeDataset.id)
          : await apiClient.getDatasetQuality(activeDataset.id);
        setReport(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("An unexpected error occurred while auditing data quality.");
        }
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [activeDataset],
  );

  useEffect(() => {
    if (activeDataset) {
      fetchQualityReport(false);
    } else {
      setReport(null);
      setError(null);
    }
  }, [activeDataset, fetchQualityReport]);

  const handleSelectColumn = (colName: string) => {
    const issuesElement = document.getElementById("quality-issues-section");
    if (issuesElement) {
      issuesElement.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="ax-stack">
      <PageHeader
        title="Data Quality Assessment"
        description="Deterministic auditing of completeness, uniqueness, domain validity, category consistency, and anomaly risk."
        badge={{
          text: activeDataset ? activeDataset.name : "Awaiting Dataset",
          variant: activeDataset ? "emerald" : "neutral",
        }}
        actions={
          activeDataset && report ? (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => fetchQualityReport(true)}
              disabled={isRefreshing || isLoading}
            >
              <RefreshIcon
                size={14}
                style={{
                  animation: isRefreshing ? "spin 1s linear infinite" : "none",
                }}
              />
              <span>{isRefreshing ? "Auditing..." : "Re-audit"}</span>
            </button>
          ) : undefined
        }
      />

      {/* State 1: No Dataset Connected */}
      {!activeDataset && !isDatasetLoading && (
        <EmptyState
          icon={<DataQualityIcon size={28} />}
          title="No dataset connected"
          description="Upload or connect a dataset to run the automated 6-dimension Data Quality audit."
          action={
            <Link to="/data" className="btn btn-primary">
              <UploadIcon size={15} />
              <span>Connect Dataset</span>
            </Link>
          }
        />
      )}

      {/* State 2: Loading Analysis */}
      {isLoading && activeDataset && (
        <div
          style={{
            padding: "4rem 2rem",
            textAlign: "center",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            marginBottom: "2rem",
          }}
        >
          <div
            style={{
              width: "42px",
              height: "42px",
              border: "3px solid rgba(99, 102, 241, 0.2)",
              borderTopColor: "var(--primary, #6366f1)",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 1.25rem",
            }}
          />
          <h3
            style={{
              fontSize: "1.125rem",
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "0.5rem",
            }}
          >
            Analyzing Dataset Quality...
          </h3>
          <p
            style={{
              fontSize: "0.8125rem",
              color: "var(--text-muted)",
              maxWidth: "480px",
              margin: "0 auto",
              lineHeight: 1.5,
            }}
          >
            Executing vectorized DuckDB rules across Completeness, Uniqueness,
            Validity, Consistency, Integrity, and Anomaly Risk.
          </p>
        </div>
      )}

      {/* State 3: Error Boundary */}
      {error && !isLoading && (
        <div
          style={{
            padding: "1.5rem",
            backgroundColor: "rgba(244, 63, 94, 0.08)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "var(--radius-md)",
            marginBottom: "2rem",
            display: "flex",
            alignItems: "flex-start",
            gap: "1rem",
          }}
        >
          <AlertCircleIcon size={20} style={{ color: "#f43f5e", marginTop: "2px" }} />
          <div style={{ flex: 1 }}>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "#f43f5e", margin: "0 0 0.25rem" }}>
              Quality Audit Failed
            </h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: "0 0 1rem" }}>
              {error}
            </p>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => fetchQualityReport(false)}
            >
              Retry Audit
            </button>
          </div>
        </div>
      )}

      {/* State 4: Real Quality Report Loaded */}
      {report && !isLoading && activeDataset && (
        <div>
          {/* Overall Health Score Card */}
          <div style={{ marginBottom: "1.5rem" }}>
            <QualityScoreCard
              report={report}
              datasetName={activeDataset.name}
              onRefresh={() => fetchQualityReport(true)}
              isRefreshing={isRefreshing}
            />
          </div>

          {/* 6 Dimension Scorecards */}
          <DimensionCards
            dimensions={report.dimension_scores}
            selectedDimension={selectedDimension}
            onSelectDimension={setSelectedDimension}
          />

          {/* Severity Breakdown Bar & Filters */}
          <div id="quality-issues-section">
            <IssueSummaryBar
              critical={report.critical_issues}
              high={report.high_issues}
              medium={report.medium_issues}
              low={report.low_issues}
              info={report.info_issues}
              total={report.total_issues}
              selectedSeverity={selectedSeverity}
              onSelectSeverity={setSelectedSeverity}
            />

            {/* Quality Issues Table */}
            <QualityIssuesTable
              issues={report.issues}
              selectedSeverity={selectedSeverity}
              selectedDimension={selectedDimension}
              onSelectSeverity={setSelectedSeverity}
              onSelectDimension={setSelectedDimension}
            />
          </div>

          {/* Column-by-Column Quality Scorecard */}
          <div style={{ marginBottom: "2rem" }}>
            <ColumnQualityTable
              columns={report.column_summaries}
              onSelectColumn={handleSelectColumn}
            />
          </div>
        </div>
      )}
    </div>
  );
}
