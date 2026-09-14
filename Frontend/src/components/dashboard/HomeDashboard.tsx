import React, { useEffect, useState, useRef, useMemo } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { useDataset } from "@/context/DatasetContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { apiClient } from "@/services/api";
import { listInsights } from "@/services/copilotApi";
import { workspaceApi } from "@/services/workspaceApi";
import { createDashboard, listDashboards } from "@/services/dashboardApi";
import {
  DatasetProfileResponse,
  DataQualityReportResponse,
  EDAReport,
  EDAFinding,
  ChartSpec,
  Dashboard,
} from "@/types";
import { Insight } from "@/types/copilot";
import { ActivityRecord } from "@/types/workspace";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";
import { STARTER_TEMPLATES } from "@/components/dashboard/templates";
import {
  Sparkles,
  Upload,
  Plus,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  Brain,
  Layers,
  Database,
  ShieldCheck,
  Sigma,
  Clock,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  FlaskConical,
} from "lucide-react";

interface HomeDashboardProps {
  onOpenCustomDashboard?: (dashboardId: string) => void;
}

export function HomeDashboard({ onOpenCustomDashboard }: HomeDashboardProps) {
  const navigate = useNavigate();
  const { activeDataset, refreshDatasets, loadSampleDataset, isLoading: isDatasetLoading } = useDataset();
  const { activeWorkspace, activeProject } = useWorkspace();

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Analytical state (Strictly deterministic — zero fabrication)
  const [profile, setProfile] = useState<DatasetProfileResponse | null>(null);
  const [quality, setQuality] = useState<DataQualityReportResponse | null>(null);
  const [eda, setEda] = useState<EDAReport | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [activities, setActivities] = useState<ActivityRecord[]>([]);
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  // Custom Dashboard Creation Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [dashName, setDashName] = useState("");
  const [dashDesc, setDashDesc] = useState("");
  const [dashTemplate, setDashTemplate] = useState("executive_overview");

  // Load analytics when activeDataset changes
  useEffect(() => {
    if (!activeDataset?.id) {
      setProfile(null);
      setQuality(null);
      setEda(null);
      setInsights([]);
      setActivities([]);
      return;
    }

    let isMounted = true;
    const fetchAnalytics = async () => {
      setIsLoadingAnalytics(true);
      try {
        const datasetId = activeDataset.id;
        const versionId = activeDataset.active_version_id || "v1";

        // Parallel deterministic queries
        const [profRes, qualRes, edaRes] = await Promise.allSettled([
          apiClient.getDatasetProfile(datasetId),
          apiClient.getDatasetQuality(datasetId),
          apiClient.getEdaReport(datasetId, versionId),
        ]);

        if (isMounted) {
          if (profRes.status === "fulfilled") setProfile(profRes.value);
          if (qualRes.status === "fulfilled") setQuality(qualRes.value);
          if (edaRes.status === "fulfilled") setEda(edaRes.value);
        }

        // Fetch proactive insights if workspace exists
        if (activeWorkspace?.workspace_id) {
          try {
            const insRes = await listInsights({
              workspace_id: activeWorkspace.workspace_id,
              project_id: activeProject?.project_id,
              dataset_id: datasetId,
            });
            if (isMounted) setInsights(insRes || []);
          } catch {
            // Ignore proactive insight failure
          }
        }

        // Fetch activities
        if (activeProject?.project_id) {
          try {
            const actList = await workspaceApi.getProjectActivity(activeProject.project_id, 10);
            if (isMounted) setActivities(actList || []);
          } catch {
            // Fallback activity
          }
        }

        // Fetch saved dashboards
        try {
          const dashList = await listDashboards(datasetId);
          if (isMounted) setDashboards(dashList || []);
        } catch {
          // Ignore
        }
      } catch (err) {
        console.warn("Analytics fetch error in HomeDashboard:", err);
      } finally {
        if (isMounted) setIsLoadingAnalytics(false);
      }
    };

    fetchAnalytics();
    return () => {
      isMounted = false;
    };
  }, [activeDataset?.id, activeDataset?.active_version_id, activeWorkspace?.workspace_id, activeProject?.project_id]);

  // Handle direct file upload
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      await apiClient.uploadDataset(file);
      await refreshDatasets();
    } catch (err: any) {
      alert(`Upload failed: ${err.message || "Please check file format."}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Handle dashboard creation
  const handleCreateDashboardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dashName.trim() || !activeDataset) return;

    try {
      const created = await createDashboard({
        name: dashName.trim(),
        description: dashDesc.trim() || undefined,
        dataset_id: activeDataset.id,
        dataset_version_id: activeDataset.active_version_id || "v1",
        template_id: dashTemplate === "blank" ? undefined : dashTemplate,
      });
      setIsCreateModalOpen(false);
      setDashName("");
      setDashDesc("");
      if (onOpenCustomDashboard) {
        onOpenCustomDashboard(created.dashboard_id);
      }
    } catch (err: any) {
      alert(`Could not create dashboard: ${err.message}`);
    }
  };

  // Compute compact overview KPIs
  const formattedRows = useMemo(() => {
    const count = profile?.row_count ?? eda?.overview?.row_count;
    if (count == null) return null;
    if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
    if (count >= 10_000) return `${(count / 1_000).toFixed(1)}K`;
    return count.toLocaleString();
  }, [profile?.row_count, eda?.overview?.row_count]);

  const formattedCols = useMemo(() => {
    const count = profile?.column_count ?? eda?.overview?.column_count;
    return count != null ? count.toString() : null;
  }, [profile?.column_count, eda?.overview?.column_count]);

  const dataQualityScore = useMemo(() => {
    if (quality?.overall_score != null) {
      return Math.round(quality.overall_score);
    }
    return null;
  }, [quality?.overall_score]);

  const latestDataDate = useMemo(() => {
    // Check if datetime analyses exist
    if (eda?.datetime_analyses && eda.datetime_analyses.length > 0) {
      const maxDate = eda.datetime_analyses[0].summary?.max_date;
      if (maxDate) {
        const d = new Date(maxDate);
        if (!isNaN(d.getTime())) {
          return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
        }
      }
    }
    // Fallback to dataset update timestamp
    if (activeDataset?.updated_at || activeDataset?.created_at) {
      const d = new Date(activeDataset.updated_at || activeDataset.created_at);
      if (!isNaN(d.getTime())) {
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      }
    }
    return null;
  }, [eda?.datetime_analyses, activeDataset?.updated_at, activeDataset?.created_at]);

  // Unified deterministic findings & insights
  const importantInsights = useMemo(() => {
    const items: Array<{
      id: string;
      category: string;
      title: string;
      description: string;
      metric?: string;
      actionLabel: string;
      actionLink: string;
    }> = [];

    // From EDA Findings
    if (eda?.findings && eda.findings.length > 0) {
      eda.findings.slice(0, 4).forEach((f: EDAFinding) => {
        let actionLink = "/eda";
        if (f.category?.toUpperCase().includes("TREND")) actionLink = "/visualizations";
        else if (f.category?.toUpperCase().includes("QUALITY")) actionLink = "/quality";
        else if (f.category?.toUpperCase().includes("CORRELATION")) actionLink = "/statistics";

        items.push({
          id: f.id || Math.random().toString(),
          category: (f.category || "Finding").replace(/_/g, " "),
          title: f.title,
          description: f.description || f.message || "Deterministic pattern detected during automated data exploration.",
          metric: f.metric_label && f.metric_value != null ? `${f.metric_label}: ${f.metric_value}` : f.evidence,
          actionLabel: "Explore →",
          actionLink,
        });
      });
    }

    // From Proactive Insights
    if (insights && insights.length > 0 && items.length < 4) {
      insights.slice(0, 4 - items.length).forEach((ins: Insight) => {
        items.push({
          id: ins.insight_id,
          category: ins.insight_type.replace(/_/g, " "),
          title: ins.title,
          description: ins.summary,
          metric: ins.evidence_metric ? `${ins.evidence_metric.name}: ${ins.evidence_metric.value}` : undefined,
          actionLabel: "Explore →",
          actionLink: "/insights",
        });
      });
    }

    return items;
  }, [eda?.findings, insights]);

  // Analytical Overview Charts (from ChartSpec infrastructure)
  const overviewCharts = useMemo<ChartSpec[]>(() => {
    if (!eda?.charts || eda.charts.length === 0) return [];
    // Return up to 2 distinct charts
    return eda.charts.slice(0, 2);
  }, [eda?.charts]);

  // Phase 25 Recommended Next Steps
  const recommendedSteps = useMemo(() => {
    const steps: Array<{
      id: string;
      title: string;
      description: string;
      link: string;
      icon: React.ElementType;
      badge: string;
    }> = [];

    // Quality recommendation
    if (dataQualityScore != null && dataQualityScore < 95) {
      steps.push({
        id: "rec_quality",
        title: "Check data quality",
        description: `Overall quality score is ${dataQualityScore}%. Review missing cells and type inconsistencies.`,
        link: "/quality",
        icon: ShieldCheck,
        badge: "Data Health",
      });
    }

    // Trends recommendation
    if (eda?.datetime_analyses && eda.datetime_analyses.length > 0) {
      steps.push({
        id: "rec_trends",
        title: "Explore important trends",
        description: "Temporal distribution detected. Plot sequential trajectories across key indicators.",
        link: "/visualizations",
        icon: TrendingUp,
        badge: "Time Series",
      });
    }

    // Anomalies
    if (eda?.outliers && Object.keys(eda.outliers).length > 0) {
      steps.push({
        id: "rec_anomalies",
        title: "Investigate anomalies",
        description: "Unusual value clusters isolated in continuous fields. Inspect potential measurement skews.",
        link: "/eda",
        icon: AlertTriangle,
        badge: "Outlier Check",
      });
    }

    // Segments / Correlation
    if ((profile?.numeric_columns_count ?? 0) >= 2) {
      steps.push({
        id: "rec_segments",
        title: "Compare segments & correlations",
        description: "Examine Pearson/Spearman relationship matrix across quantitative dimensions.",
        link: "/statistics",
        icon: Sigma,
        badge: "Relationships",
      });
    }

    // AI Copilot fallback
    steps.push({
      id: "rec_ai",
      title: "Ask AI a question",
      description: "Ask the AI Analyst to synthesize cross-table insights or draft an executive summary.",
      link: "/ai-analyst",
      icon: Brain,
      badge: "AI Copilot",
    });

    return steps.slice(0, 4);
  }, [dataQualityScore, eda?.datetime_analyses, eda?.outliers, profile?.numeric_columns_count]);

  // Combined real activities
  const recentActivities = useMemo(() => {
    const items: Array<{ id: string; title: string; timestamp: string; type: string }> = [];

    if (activities && activities.length > 0) {
      activities.slice(0, 5).forEach((act) => {
        items.push({
          id: act.activity_id,
          title: `${act.actor_name || "User"} ${act.activity_type.replace(/_/g, " ")}: ${act.description || ""}`,
          timestamp: act.created_at,
          type: act.activity_type,
        });
      });
    }

    // If empty, generate real records from dataset lifecycle
    if (items.length === 0 && activeDataset) {
      if (activeDataset.created_at) {
        items.push({
          id: "act_created",
          title: `Dataset "${activeDataset.original_filename || activeDataset.name}" ingested into DuckDB`,
          timestamp: activeDataset.created_at,
          type: "ingestion",
        });
      }
      if (profile?.generated_at) {
        items.push({
          id: "act_profile",
          title: "Statistical schema profiling completed",
          timestamp: profile.generated_at,
          type: "profiling",
        });
      }
      if (quality?.evaluated_at) {
        items.push({
          id: "act_quality",
          title: `Automated data health audit completed (${dataQualityScore ?? 100}%)`,
          timestamp: quality.evaluated_at,
          type: "audit",
        });
      }
      if (eda?.generated_at) {
        items.push({
          id: "act_eda",
          title: "Exploratory data analysis & ChartSpecs generated",
          timestamp: eda.generated_at,
          type: "eda",
        });
      }
    }

    return items;
  }, [activities, activeDataset, profile?.generated_at, quality?.evaluated_at, eda?.generated_at, dataQualityScore]);

  // Relative timestamp formatter
  const formatTimeAgo = (ts: string) => {
    try {
      const date = new Date(ts);
      if (isNaN(date.getTime())) return ts;
      const diffSec = Math.floor((Date.now() - date.getTime()) / 1000);
      if (diffSec < 60) return "just now";
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch {
      return ts;
    }
  };

  // ─────────────────────────────────────────────────────────────
  // 1. EMPTY STATE: No Dataset Selected
  // ─────────────────────────────────────────────────────────────
  if (!activeDataset) {
    return (
      <div style={{ maxWidth: "860px", margin: "3rem auto", padding: "0 1.5rem" }}>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          accept=".csv,.xlsx,.json,.parquet"
          onChange={handleFileChange}
        />

        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "3.5rem 2rem",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "12px",
          }}
        >
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "14px",
              backgroundColor: "rgba(245, 158, 11, 0.1)",
              border: "1px solid rgba(245, 158, 11, 0.25)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1.5rem auto",
            }}
          >
            <Database style={{ width: "28px", height: "28px", color: "var(--color-primary, #f59e0b)" }} />
          </div>

          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", margin: 0, letterSpacing: "-0.02em" }}>
            Welcome to AnalyzaX
          </h1>
          <p style={{ fontSize: "0.9375rem", color: "var(--text-muted)", marginTop: "0.5rem", maxWidth: "460px", margin: "0.5rem auto 2rem auto", lineHeight: 1.5 }}>
            Connect or upload a dataset to start analyzing with automated profiling, leakage-free modeling, and executive insights.
          </p>

          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap", marginBottom: "3rem" }}>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="btn btn-primary"
              style={{ padding: "0.6rem 1.4rem", fontSize: "0.875rem" }}
            >
              <Upload style={{ width: "16px", height: "16px" }} />
              {isUploading ? "Uploading..." : "Upload Dataset"}
            </button>
            <button
              type="button"
              onClick={async () => {
                try {
                  setIsLoadingAnalytics(true);
                  await loadSampleDataset();
                } catch (err: any) {
                  alert(err.message || "Failed to load sample dataset.");
                } finally {
                  setIsLoadingAnalytics(false);
                }
              }}
              disabled={isLoadingAnalytics}
              className="btn btn-secondary"
              style={{ padding: "0.6rem 1.4rem", fontSize: "0.875rem" }}
            >
              <Database style={{ width: "16px", height: "16px" }} />
              Connect Data
            </button>
          </div>

          {/* 5-Step Workflow */}
          <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "2rem" }}>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "1.25rem" }}>
              Analytical Workflow
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "1rem",
                textAlign: "left",
              }}
            >
              {[
                { step: "1", title: "Upload", desc: "CSV, XLSX, or Parquet" },
                { step: "2", title: "Understand", desc: "Automated profile & audit" },
                { step: "3", title: "Explore", desc: "Charts, correlation, EDA" },
                { step: "4", title: "Analyze", desc: "Statistical tests & ML" },
                { step: "5", title: "Decide", desc: "Executive insights" },
              ].map((item, idx) => (
                <div
                  key={item.step}
                  style={{
                    backgroundColor: "var(--bg-elevated)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "8px",
                    padding: "0.85rem",
                    position: "relative",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.35rem" }}>
                    <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--color-primary, #f59e0b)", fontFamily: "monospace" }}>
                      0{item.step}
                    </span>
                    {idx < 4 && (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>→</span>
                    )}
                  </div>
                  <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>{item.title}</div>
                  <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>{item.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // 2. AUTHENTIC DASHBOARD EXPERIENCE
  // ─────────────────────────────────────────────────────────────
  const datasetTitle = activeDataset.name || activeDataset.original_filename || "Active Dataset";
  const versionBadge = activeDataset.active_version_id
    ? activeDataset.active_version_id.toUpperCase()
    : "V1";

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Hidden file input for header upload */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: "none" }}
        accept=".csv,.xlsx,.json,.parquet"
        onChange={handleFileChange}
      />

      {/* ============================================================ */}
      {/* HEADER SECTION                                               */}
      {/* ============================================================ */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "1rem",
          paddingBottom: "1.25rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
            <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
              Dashboard
            </h1>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "0.2rem 0.6rem",
                borderRadius: "4px",
                backgroundColor: "rgba(148, 163, 184, 0.1)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <Database style={{ width: "12px", height: "12px", color: "var(--text-muted)" }} />
              {datasetTitle} · {versionBadge}
            </span>
          </div>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Your analytics workspace
          </p>
        </div>

        {/* Useful Header Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => navigate({ to: "/ai-analyst" })}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.8125rem" }}
          >
            <Brain style={{ width: "14px", height: "14px", color: "#818cf8" }} />
            Ask AI
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.8125rem" }}
          >
            <Upload style={{ width: "14px", height: "14px" }} />
            {isUploading ? "Uploading..." : "Upload Dataset"}
          </button>
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="btn btn-primary btn-sm"
            style={{ fontSize: "0.8125rem" }}
          >
            <Plus style={{ width: "14px", height: "14px" }} />
            Create Dashboard
          </button>
        </div>
      </div>

      {/* ============================================================ */}
      {/* OVERVIEW METRICS (COMPACT KPI ROW)                           */}
      {/* ============================================================ */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
          gap: "0.875rem",
        }}
      >
        {/* KPI 1: Rows */}
        <div className="stat-card" data-tone="cyan" style={{ padding: "1rem" }}>
          <div className="stat-label">Rows</div>
          <div className="stat-value" style={{ fontSize: "1.5rem" }}>
            {formattedRows ?? (isLoadingAnalytics ? "..." : "—")}
          </div>
          <div className="stat-subtext">
            {profile?.row_count != null ? "Verified raw record count" : "Pending profiling"}
          </div>
        </div>

        {/* KPI 2: Columns */}
        <div className="stat-card" data-tone="cyan" style={{ padding: "1rem" }}>
          <div className="stat-label">Columns</div>
          <div className="stat-value" style={{ fontSize: "1.5rem" }}>
            {formattedCols ?? (isLoadingAnalytics ? "..." : "—")}
          </div>
          <div className="stat-subtext">
            {profile?.numeric_columns_count != null
              ? `${profile.numeric_columns_count} num · ${profile.categorical_columns_count} cat`
              : "Feature dimensions"}
          </div>
        </div>

        {/* KPI 3: Data Quality */}
        <div
          className="stat-card"
          data-tone={dataQualityScore != null ? (dataQualityScore >= 85 ? "emerald" : dataQualityScore >= 60 ? "amber" : "rose") : "cyan"}
          style={{ padding: "1rem" }}
        >
          <div className="stat-label">Data Quality</div>
          <div className="stat-value" style={{ fontSize: "1.5rem" }}>
            {dataQualityScore != null ? `${dataQualityScore}%` : (isLoadingAnalytics ? "..." : "—")}
          </div>
          <div className="stat-subtext">
            {quality ? (
              <Link to="/quality" style={{ color: "inherit", textDecoration: "underline" }}>
                {quality.total_issues_count || 0} issues detected
              </Link>
            ) : (
              "Automated health audit"
            )}
          </div>
        </div>

        {/* KPI 4: Latest Data */}
        <div className="stat-card" data-tone="amber" style={{ padding: "1rem" }}>
          <div className="stat-label">Latest Data</div>
          <div className="stat-value" style={{ fontSize: "1.25rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {latestDataDate ?? (isLoadingAnalytics ? "..." : "—")}
          </div>
          <div className="stat-subtext">
            {eda?.datetime_analyses && eda.datetime_analyses.length > 0
              ? "Max temporal timestamp"
              : "Dataset registry timestamp"}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* KEY INSIGHTS (IMPORTANT FINDINGS)                            */}
      {/* ============================================================ */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              Important Insights
            </h2>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              ({importantInsights.length} detected)
            </span>
          </div>
          <Link
            to="/eda"
            style={{ fontSize: "0.75rem", color: "var(--color-primary, #f59e0b)", textDecoration: "none", display: "flex", alignItems: "center", gap: "0.25rem", fontWeight: 500 }}
          >
            All findings <ChevronRight style={{ width: "12px", height: "12px" }} />
          </Link>
        </div>

        {importantInsights.length > 0 ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "0.875rem",
            }}
          >
            {importantInsights.map((item) => (
              <div
                key={item.id}
                className="card"
                style={{
                  padding: "1rem",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  backgroundColor: "var(--bg-surface)",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem", marginBottom: "0.35rem" }}>
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        color: "var(--color-primary, #f59e0b)",
                        backgroundColor: "rgba(245, 158, 11, 0.1)",
                        padding: "0.15rem 0.4rem",
                        borderRadius: "3px",
                      }}
                    >
                      {item.category}
                    </span>
                    {item.metric && (
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontFamily: "monospace",
                          color: "var(--text-secondary)",
                          backgroundColor: "var(--bg-elevated)",
                          padding: "0.1rem 0.35rem",
                          borderRadius: "3px",
                          border: "1px solid var(--border-subtle)",
                        }}
                      >
                        {item.metric}
                      </span>
                    )}
                  </div>
                  <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", margin: "0 0 0.35rem 0", lineHeight: 1.3 }}>
                    {item.title}
                  </h3>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.45, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {item.description}
                  </p>
                </div>

                <div>
                  <Link
                    to={item.actionLink}
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: "var(--color-primary, #f59e0b)",
                      textDecoration: "none",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.25rem",
                    }}
                  >
                    {item.actionLabel}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div
            className="card"
            style={{
              padding: "1.5rem",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: "0.8125rem",
            }}
          >
            {isLoadingAnalytics
              ? "Running deterministic anomaly and trend diagnostics..."
              : "No critical anomalies or severe skew detected in this dataset version. Explore EDA for complete univariate breakdowns."}
          </div>
        )}
      </section>

      {/* ============================================================ */}
      {/* ANALYTICAL OVERVIEW (CHARTSPEC INFRASTRUCTURE)               */}
      {/* ============================================================ */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              Analytical Overview
            </h2>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              (ChartSpec deterministic engine)
            </span>
          </div>
          <Link
            to="/visualizations"
            style={{ fontSize: "0.75rem", color: "var(--color-primary, #f59e0b)", textDecoration: "none", display: "flex", alignItems: "center", gap: "0.25rem", fontWeight: 500 }}
          >
            Visualization Studio <ChevronRight style={{ width: "12px", height: "12px" }} />
          </Link>
        </div>

        {overviewCharts.length > 0 ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
              gap: "1rem",
            }}
          >
            {overviewCharts.map((spec, idx) => (
              <div
                key={spec.chart_id || idx}
                className="card"
                style={{
                  padding: "1rem",
                  backgroundColor: "var(--bg-surface)",
                  overflow: "hidden",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      {spec.title || (spec.type === "line" ? "Trend Analysis" : "Distribution Analysis")}
                    </h3>
                    {spec.subtitle && (
                      <p style={{ margin: "0.15rem 0 0 0", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {spec.subtitle}
                      </p>
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: "0.6875rem",
                      padding: "0.15rem 0.4rem",
                      borderRadius: "4px",
                      backgroundColor: "var(--bg-elevated)",
                      color: "var(--text-muted)",
                      textTransform: "uppercase",
                      fontWeight: 600,
                    }}
                  >
                    {spec.type || "Chart"}
                  </span>
                </div>

                <div style={{ width: "100%", height: "260px" }}>
                  <ChartRenderer spec={spec} height={260} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div
            className="card"
            style={{
              padding: "2rem",
              textAlign: "center",
              backgroundColor: "var(--bg-surface)",
            }}
          >
            <BarChart3 style={{ width: "32px", height: "32px", color: "var(--text-muted)", margin: "0 auto 0.5rem auto" }} />
            <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-primary)", fontWeight: 500 }}>
              {isLoadingAnalytics ? "Synthesizing dataset charts..." : "Analytical charts will appear once the dataset is profiled"}
            </p>
            <p style={{ margin: "0.25rem 0 1rem 0", fontSize: "0.75rem", color: "var(--text-muted)" }}>
              AnalyzaX generates zero synthetic data. Charts are strictly computed from validated columns.
            </p>
            <Link to="/visualizations" className="btn btn-secondary btn-sm" style={{ display: "inline-flex" }}>
              Open Visualization Studio
            </Link>
          </div>
        )}
      </section>

      {/* ============================================================ */}
      {/* TWO COLUMN LOWER SECTION: NEXT STEPS & RECENT ACTIVITY       */}
      {/* ============================================================ */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1rem",
        }}
      >
        {/* Recommended Next Steps (Phase 25) */}
        <section>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              Recommended Next Steps
            </h2>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              (Phase 25 Copilot)
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
            {recommendedSteps.map((step) => {
              const IconComp = step.icon;
              return (
                <Link
                  key={step.id}
                  to={step.link}
                  className="card"
                  style={{
                    padding: "0.875rem 1rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "0.75rem",
                    textDecoration: "none",
                    backgroundColor: "var(--bg-surface)",
                    transition: "transform 0.15s ease, border-color 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <div
                      style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "6px",
                        backgroundColor: "rgba(245, 158, 11, 0.1)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <IconComp style={{ width: "16px", height: "16px", color: "var(--color-primary, #f59e0b)" }} />
                    </div>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                          {step.title}
                        </span>
                        <span
                          style={{
                            fontSize: "0.625rem",
                            padding: "0.1rem 0.35rem",
                            borderRadius: "3px",
                            backgroundColor: "var(--bg-elevated)",
                            color: "var(--text-muted)",
                            fontWeight: 600,
                          }}
                        >
                          {step.badge}
                        </span>
                      </div>
                      <p style={{ margin: "0.15rem 0 0 0", fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.35 }}>
                        {step.description}
                      </p>
                    </div>
                  </div>
                  <ArrowRight style={{ width: "14px", height: "14px", color: "var(--text-muted)", flexShrink: 0 }} />
                </Link>
              );
            })}
          </div>
        </section>

        {/* Recent Activity Feed */}
        <section>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              Recent Activity
            </h2>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Audit lineage
            </span>
          </div>

          <div
            className="card"
            style={{
              padding: "1rem",
              backgroundColor: "var(--bg-surface)",
              display: "flex",
              flexDirection: "column",
              gap: "0.75rem",
            }}
          >
            {recentActivities.length > 0 ? (
              recentActivities.map((act, i) => (
                <div
                  key={act.id || i}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    gap: "0.75rem",
                    paddingBottom: i < recentActivities.length - 1 ? "0.625rem" : "0",
                    borderBottom: i < recentActivities.length - 1 ? "1px solid var(--border-subtle)" : "none",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                    <div
                      style={{
                        width: "6px",
                        height: "6px",
                        borderRadius: "50%",
                        backgroundColor: "var(--color-primary, #f59e0b)",
                        marginTop: "0.45rem",
                        flexShrink: 0,
                      }}
                    />
                    <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                      {act.title}
                    </span>
                  </div>
                  <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", whiteSpace: "nowrap", flexShrink: 0 }}>
                    {formatTimeAgo(act.timestamp)}
                  </span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textAlign: "center", padding: "1rem" }}>
                No recent activity recorded. Operations will stream into this audit feed.
              </div>
            )}
          </div>
        </section>
      </div>

      {/* ============================================================ */}
      {/* SAVED DASHBOARDS ACCORDION / DRAWER                          */}
      {/* ============================================================ */}
      {dashboards.length > 0 && (
        <section style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <h2 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-secondary)", margin: 0 }}>
              Custom Saved Dashboards ({dashboards.length})
            </h2>
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(true)}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
            >
              + New
            </button>
          </div>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            {dashboards.map((d) => (
              <button
                key={d.dashboard_id}
                type="button"
                onClick={() => onOpenCustomDashboard?.(d.dashboard_id)}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "6px",
                  padding: "0.5rem 0.75rem",
                  fontSize: "0.8125rem",
                  color: "var(--text-primary)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <Layers style={{ width: "12px", height: "12px", color: "var(--color-primary, #f59e0b)" }} />
                <span>{d.name}</span>
                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                  ({d.components?.length || 0} widgets)
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* ============================================================ */}
      {/* CREATE DASHBOARD MODAL                                       */}
      {/* ============================================================ */}
      {isCreateModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
          onClick={() => setIsCreateModalOpen(false)}
        >
          <div
            style={{
              backgroundColor: "var(--bg-surface, #0f172a)",
              border: "1px solid var(--border-subtle, #1e293b)",
              borderRadius: "12px",
              padding: "1.75rem",
              maxWidth: "520px",
              width: "100%",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: "0 0 1rem 0", fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Create Custom Dashboard
            </h3>

            <form onSubmit={handleCreateDashboardSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label htmlFor="dash-name-input" style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.35rem" }}>
                  Dashboard Name
                </label>
                <input
                  id="dash-name-input"
                  type="text"
                  placeholder="e.g. Executive Performance Summary"
                  value={dashName}
                  onChange={(e) => setDashName(e.target.value)}
                  className="input"
                  style={{ width: "100%", fontSize: "0.8125rem" }}
                  autoFocus
                  required
                />
              </div>

              <div>
                <label htmlFor="dash-desc-input" style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.35rem" }}>
                  Description (Optional)
                </label>
                <textarea
                  id="dash-desc-input"
                  placeholder="Key metrics and questions addressed..."
                  value={dashDesc}
                  onChange={(e) => setDashDesc(e.target.value)}
                  rows={2}
                  className="input"
                  style={{ width: "100%", fontSize: "0.8125rem" }}
                />
              </div>

              <div>
                <span style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                  Starter Template
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      fontSize: "0.8125rem",
                      color: "var(--text-primary)",
                      cursor: "pointer",
                      padding: "0.5rem",
                      borderRadius: "6px",
                      backgroundColor: dashTemplate === "blank" ? "rgba(245, 158, 11, 0.15)" : "var(--bg-elevated)",
                    }}
                  >
                    <input
                      type="radio"
                      name="template"
                      value="blank"
                      checked={dashTemplate === "blank"}
                      onChange={(e) => setDashTemplate(e.target.value)}
                    />
                    <span><strong>Blank Canvas</strong> — Empty 12-column grid</span>
                  </label>

                  {STARTER_TEMPLATES.map((tmpl) => (
                    <label
                      key={tmpl.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        fontSize: "0.8125rem",
                        color: "var(--text-primary)",
                        cursor: "pointer",
                        padding: "0.5rem",
                        borderRadius: "6px",
                        backgroundColor: dashTemplate === tmpl.id ? "rgba(245, 158, 11, 0.15)" : "var(--bg-elevated)",
                      }}
                    >
                      <input
                        type="radio"
                        name="template"
                        value={tmpl.id}
                        checked={dashTemplate === tmpl.id}
                        onChange={(e) => setDashTemplate(e.target.value)}
                      />
                      <span><strong>{tmpl.name}</strong> — {tmpl.description}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="btn btn-secondary btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Create & Open
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
