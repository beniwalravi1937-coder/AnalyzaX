import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { useDataset } from "@/context/DatasetContext";
import { apiClient, ApiError } from "@/services/api";
import {
  DataQualityReportResponse,
  QualityDimension,
  QualitySeverity,
} from "@/types";
import { EmptyState } from "@/components/ui/EmptyState";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import { RefreshIcon, AlertCircleIcon } from "@/components/icons";
import { QualityScoreCard } from "@/components/quality/QualityScoreCard";
import { DimensionCards } from "@/components/quality/DimensionCards";
import { IssueSummaryBar } from "@/components/quality/IssueSummaryBar";
import { QualityIssuesTable } from "@/components/quality/QualityIssuesTable";
import { ColumnQualityTable } from "@/components/quality/ColumnQualityTable";
import { AnalyticalWorkspaceHeader } from "@/components/layout/AnalyticalWorkspaceHeader";
import { SecondaryInfoPanel } from "@/components/layout/SecondaryInfoPanel";
import { Button } from "@/components/ui/button";
import { ShieldAlert, Sparkles, RefreshCw, Wand2, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/quality")({
  head: () => ({
    meta: [
      { title: "Data Quality Health Check — AnalyzaX" },
      {
        name: "description",
        content:
          "Audit completeness, validity, uniqueness, and consistency across dataset versions.",
      },
      { property: "og:title", content: "Data Quality Health Check — AnalyzaX" },
    ],
  }),
  component: DataQualityPage,
});

export function DataQualityPage() {
  const { activeDataset, isLoading: isDatasetLoading } = useDataset();

  const [report, setReport] = useState<DataQualityReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"beginner" | "power">("beginner");

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

  const workflowSteps = [
    { id: "score", label: "Health Score", status: report ? ("completed" as const) : ("current" as const) },
    { id: "dimensions", label: "Dimensions", status: report?.dimension_scores ? ("completed" as const) : ("pending" as const) },
    { id: "issues", label: "Issues Catalog", status: report?.issues?.length ? ("completed" as const) : ("pending" as const) },
    { id: "columns", label: "Column Health", status: report?.column_summaries?.length ? ("completed" as const) : ("pending" as const) },
  ];

  return (
    <div className="flex flex-col min-h-[calc(100vh-100px)]">
      <AnalyticalWorkspaceHeader
        title="Data Quality"
        description="Audit completeness, validity, uniqueness, and consistency across dataset versions."
        badgeText="Deterministic Rule Engine"
        steps={workflowSteps}
        currentStepId={report ? "issues" : "score"}
        status={isLoading ? "loading" : isRefreshing ? "running" : report ? "success" : "idle"}
        durationMs={report?.execution_time_ms}
        rowCount={report?.total_rows}
        mode={mode === "beginner" ? "beginner" : "advanced"}
        onModeChange={(m) => setMode(m === "beginner" ? "beginner" : "power")}
        primaryAction={
          <Button
            size="sm"
            onClick={() => fetchQualityReport(true)}
            disabled={!activeDataset || isLoading || isRefreshing}
            className="h-9 px-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>{isRefreshing ? "Auditing Rules..." : "Run Quality Audit"}</span>
          </Button>
        }
        secondaryActions={
          report && (
            <Link to="/cleaning">
              <Button
                variant="outline"
                size="sm"
                className="h-9 px-2.5 text-xs border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 gap-1.5"
              >
                <Wand2 className="w-3.5 h-3.5" />
                <span>Auto-Fix in Cleaning</span>
              </Button>
            </Link>
          )
        }
        onRefresh={() => fetchQualityReport(true)}
        isRefreshing={isRefreshing || isLoading}
      />

      {/* State 1: No Dataset Connected */}
      {!activeDataset && !isDatasetLoading && (
        <GuidedOnboarding
          title="Automated Data Quality Health Check"
          description="Spot missing cells, duplicate records, outliers, and type mismatches instantly. Get an objective health score and actionable recommendations before running analyses."
          badgeText="Data Health Audit"
          features={[
            "6-dimension data quality scoring & health breakdown",
            "Automatic anomaly and duplicate record identification",
            "Actionable fix recommendations with 1-click cleaning links",
          ]}
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

      {/* Secondary Information */}
      <SecondaryInfoPanel
        metadata={{
          datasetName: activeDataset?.name || "No dataset selected",
          versionName: activeDataset?.version_id ? `v${activeDataset.version_id}` : "v1",
          rowCount: report?.total_rows,
          columnCount: report?.total_columns,
          engine: "DuckDB Vectorized Rule Engine",
          executionTimeMs: report?.execution_time_ms,
          customFields: {
            "Overall Score": report?.overall_score !== undefined ? `${Math.round(report.overall_score)}/100` : "N/A",
            "Total Issues": report?.total_issues ?? 0,
            "Critical Issues": report?.critical_issues ?? 0,
            "High Issues": report?.high_issues ?? 0,
          },
        }}
        recommendations={[
          ...(report && (report.critical_issues > 0 || report.high_issues > 0)
            ? [
                {
                  id: "fix-issues",
                  title: "Fix Detected Quality Issues in Cleaning Studio",
                  description: `Found ${report.critical_issues + report.high_issues} high-priority issues that can be auto-resolved with reproducible cleaning operations.`,
                  actionLabel: "Open Cleaning Studio",
                  onAction: () => { window.location.href = "/cleaning"; },
                  impact: "high" as const,
                },
              ]
            : []),
          {
            id: "eda-inspect",
            title: "Inspect Column Distributions",
            description: "Analyze skewness, missingness maps, and outliers visually in the EDA workspace.",
            actionLabel: "Launch EDA",
            onAction: () => { window.location.href = "/eda"; },
            impact: "medium" as const,
          },
          {
            id: "sql-verify",
            title: "Verify Anomaly Records via SQL",
            description: "Write read-only queries against anomaly flags in DuckDB SQL Workbench.",
            actionLabel: "Open SQL",
            onAction: () => { window.location.href = "/sql"; },
            impact: "low" as const,
          },
        ]}
        detailsContent={
          <div className="space-y-3 text-xs text-slate-300">
            <p>
              Auditing methodology executes deterministic DuckDB SQL checks across six mathematical data quality dimensions.
            </p>
            {report?.dimension_scores && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2">
                {Object.entries(report.dimension_scores).map(([dim, score]) => (
                  <div key={dim} className="p-2.5 rounded-lg bg-slate-900/60 border border-white/5">
                    <span className="text-slate-400 block text-[10px] uppercase">{dim}</span>
                    <span className="font-semibold text-slate-200">{Math.round(score)}/100</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        }
      />
    </div>
  );
}

