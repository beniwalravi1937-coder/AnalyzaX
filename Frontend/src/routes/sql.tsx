import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import {
  SQLIcon,
  UploadIcon,
  RefreshIcon,
  DatabaseIcon,
  BarChartIcon,
  EyeIcon,
  HistoryIcon,
  SaveIcon,
} from "@/components/icons";
import { apiClient } from "@/services/api";
import { sqlApi } from "@/services/sqlApi";
import {
  DatasetResponse,
  DatasetVersion,
  QueryHistoryItem,
  SavedQuery,
  SchemaTableInfo,
  SQLExplainResult,
  SQLQueryResponse,
  SQLTemplate,
  SQLValidationResult,
} from "@/types";
import { SchemaExplorer } from "@/components/sql/SchemaExplorer";
import { SQLEditor } from "@/components/sql/SQLEditor";
import { ResultPanel } from "@/components/sql/ResultPanel";
import { SQLVisualizer } from "@/components/sql/SQLVisualizer";
import { SQLExplainPanel } from "@/components/sql/SQLExplainPanel";
import { QueryHistoryPanel } from "@/components/sql/QueryHistoryPanel";
import { SavedQueriesPanel } from "@/components/sql/SavedQueriesPanel";
import { AnalyticalWorkspaceHeader } from "@/components/layout/AnalyticalWorkspaceHeader";
import { SecondaryInfoPanel } from "@/components/layout/SecondaryInfoPanel";
import { DatasetSelector } from "@/components/ui/DatasetSelector";
import { VersionSelector } from "@/components/ui/VersionSelector";
import { Button } from "@/components/ui/button";
import { Plus, Database, Sparkles, SlidersHorizontal } from "lucide-react";

export const Route = createFileRoute("/sql")({
  head: () => ({
    meta: [
      { title: "SQL Query Workbench — AnalyzaX" },
      {
        name: "description",
        content:
          "Query any dataset instantly with fast SQL. Filter, group, and summarize records with instant chart previews and AI-assisted query writing.",
      },
      { property: "og:title", content: "SQL Query Workbench — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Query any dataset instantly with fast SQL, instant chart previews, and AI query assistance.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-sql.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-sql.png" },
    ],
  }),
  component: SQLPage,
});

interface QueryTab {
  id: string;
  title: string;
  sql: string;
}

function SQLPage() {
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");

  // Editor Tabs
  const [tabs, setTabs] = useState<QueryTab[]>([
    { id: "tab-1", title: "Query 1", sql: "SELECT * FROM dataset LIMIT 25;" },
  ]);
  const [activeTabId, setActiveTabId] = useState("tab-1");

  // Schema & Templates State
  const [schema, setSchema] = useState<SchemaTableInfo | null>(null);
  const [templates, setTemplates] = useState<SQLTemplate[]>([]);
  const [schemaLoading, setSchemaLoading] = useState(false);

  // Execution State
  const [queryResult, setQueryResult] = useState<SQLQueryResponse | null>(null);
  const [validationResult, setValidationResult] = useState<SQLValidationResult | null>(null);
  const [explainPlan, setExplainPlan] = useState<SQLExplainResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);

  // History & Saved Queries State
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [savedLoading, setSavedLoading] = useState(false);

  // Output View Mode
  const [outputTab, setOutputTab] = useState<"results" | "visualizer" | "explain" | "history" | "saved">("results");
  const [isExplorerOpen, setIsExplorerOpen] = useState(true);

  // 1. Fetch datasets on mount
  useEffect(() => {
    async function loadDatasets() {
      try {
        const res = await apiClient.listDatasets();
        const list = res.datasets || [];
        setDatasets(list);
        if (list.length > 0) {
          const first = list[0];
          setSelectedDatasetId(first.id);
          setSelectedVersionId(first.active_version_id || first.current_version_id || "v1");
        }
      } catch (err) {
        console.error("Failed to load datasets:", err);
      }
    }
    loadDatasets();
  }, []);

  // 2. Fetch versions when dataset changes
  useEffect(() => {
    if (!selectedDatasetId) return;
    async function loadVersions() {
      try {
        const vList = await apiClient.getDatasetVersions(selectedDatasetId);
        setVersions(vList);
        if (vList.length > 0 && !selectedVersionId) {
          setSelectedVersionId(vList[0].version_id);
        }
      } catch (err) {
        console.error("Failed to load versions:", err);
      }
    }
    loadVersions();
  }, [selectedDatasetId, selectedVersionId]);

  // 3. Introspect Schema and load templates
  const loadSchema = useCallback(async () => {
    if (!selectedDatasetId) return;
    setSchemaLoading(true);
    try {
      const [sInfo, tmpls] = await Promise.all([
        sqlApi.getSchema(selectedDatasetId, selectedVersionId || null),
        sqlApi.getTemplates(selectedDatasetId, selectedVersionId || null),
      ]);
      setSchema(sInfo);
      setTemplates(tmpls);
    } catch (err) {
      console.error("Failed to introspect schema:", err);
    } finally {
      setSchemaLoading(false);
    }
  }, [selectedDatasetId, selectedVersionId]);

  useEffect(() => {
    loadSchema();
  }, [loadSchema]);

  // 4. Load History & Saved Queries
  const loadHistory = useCallback(async () => {
    if (!selectedDatasetId) return;
    setHistoryLoading(true);
    try {
      const hist = await sqlApi.getHistory({ dataset_id: selectedDatasetId });
      setHistory(hist);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setHistoryLoading(false);
    }
  }, [selectedDatasetId]);

  const loadSaved = useCallback(async () => {
    if (!selectedDatasetId) return;
    setSavedLoading(true);
    try {
      const sq = await sqlApi.getSavedQueries(selectedDatasetId);
      setSavedQueries(sq);
    } catch (err) {
      console.error("Failed to load saved queries:", err);
    } finally {
      setSavedLoading(false);
    }
  }, [selectedDatasetId]);

  useEffect(() => {
    loadHistory();
    loadSaved();
  }, [loadHistory, loadSaved]);

  // Active SQL text
  const currentTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
  const currentSql = currentTab ? currentTab.sql : "";

  // Tab management
  const handleSelectTab = (tabId: string) => setActiveTabId(tabId);

  const handleAddTab = () => {
    const newId = `tab-${Date.now()}`;
    const newTabNum = tabs.length + 1;
    const newTab: QueryTab = {
      id: newId,
      title: `Query ${newTabNum}`,
      sql: `SELECT * FROM ${schema?.table_alias || "dataset"} LIMIT 25;`,
    };
    setTabs([...tabs, newTab]);
    setActiveTabId(newId);
  };

  const handleCloseTab = (tabId: string) => {
    if (tabs.length <= 1) return;
    const remaining = tabs.filter((t) => t.id !== tabId);
    setTabs(remaining);
    if (activeTabId === tabId) {
      setActiveTabId(remaining[0].id);
    }
  };

  const handleChangeQuery = (newSql: string) => {
    setTabs(tabs.map((t) => (t.id === activeTabId ? { ...t, sql: newSql } : t)));
    if (validationResult) setValidationResult(null);
  };

  const handleInsertText = (text: string) => {
    handleChangeQuery(currentSql + " " + text);
  };

  const handleSelectTemplate = (sqlText: string) => {
    handleChangeQuery(sqlText);
  };

  // SQL Formatter (deterministic formatting)
  const handleFormatQuery = () => {
    if (!currentSql) return;
    const keywords = [
      "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
      "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "CROSS JOIN", "ON",
      "AS", "AND", "OR", "NOT", "IN", "IS NULL", "IS NOT NULL", "WITH",
      "UNION ALL", "UNION", "OVER", "PARTITION BY", "CASE", "WHEN", "THEN", "ELSE", "END"
    ];
    let formatted = currentSql;
    keywords.forEach((kw) => {
      const regex = new RegExp(`\\b${kw}\\b`, "gi");
      formatted = formatted.replace(regex, kw);
    });
    handleChangeQuery(formatted.trim());
  };

  // Run Query
  const handleRunQuery = async () => {
    if (!selectedDatasetId || !currentSql.trim() || isRunning) return;
    setIsRunning(true);
    setOutputTab("results");

    try {
      const res = await sqlApi.executeQuery({
        dataset_id: selectedDatasetId,
        version_id: selectedVersionId || null,
        sql: currentSql,
        max_rows: 10000,
        timeout_seconds: 30.0,
      });
      setQueryResult(res);
      loadHistory();
    } catch (err: any) {
      setQueryResult({
        query_id: "",
        dataset_id: selectedDatasetId,
        version_id: selectedVersionId,
        status: "FAILED",
        columns: [],
        rows: [],
        row_count: 0,
        execution_time_ms: 0,
        is_truncated: false,
        query_hash: "",
        cached: false,
        error_message: err.message || "Failed to execute query.",
        suggested_charts: [],
      });
    } finally {
      setIsRunning(false);
    }
  };

  // Cancel Query
  const handleCancelQuery = async () => {
    if (queryResult?.query_id) {
      await sqlApi.cancelQuery(queryResult.query_id);
    }
    setIsRunning(false);
  };

  // Validate Query
  const handleValidateQuery = async () => {
    if (!selectedDatasetId || !currentSql.trim()) return;
    try {
      const res = await sqlApi.validateQuery({
        dataset_id: selectedDatasetId,
        version_id: selectedVersionId || null,
        sql: currentSql,
      });
      setValidationResult(res);
    } catch (err: any) {
      console.error("Validation error:", err);
    }
  };

  // Explain Query
  const handleExplainQuery = async () => {
    if (!selectedDatasetId || !currentSql.trim() || isExplaining) return;
    setIsExplaining(true);
    setOutputTab("explain");

    try {
      const res = await sqlApi.explainQuery({
        dataset_id: selectedDatasetId,
        version_id: selectedVersionId || null,
        sql: currentSql,
      });
      setExplainPlan(res);
    } catch (err: any) {
      setExplainPlan({
        query_id: "",
        dataset_id: selectedDatasetId,
        version_id: selectedVersionId,
        plan_text: `Error generating plan: ${err.message}`,
        execution_time_ms: 0,
      });
    } finally {
      setIsExplaining(false);
    }
  };

  // Save Query
  const handleSaveQuery = async (data: {
    name: string;
    description?: string;
    sql: string;
    tags?: string[];
  }) => {
    if (!selectedDatasetId) return;
    try {
      await sqlApi.createSavedQuery({
        name: data.name,
        description: data.description,
        dataset_id: selectedDatasetId,
        version_scope: selectedVersionId || "active",
        sql: data.sql,
        tags: data.tags,
      });
      loadSaved();
      setOutputTab("saved");
    } catch (err) {
      console.error("Failed to save query:", err);
    }
  };

  const handleUpdateSavedQuery = async (id: string, data: Partial<SavedQuery>) => {
    try {
      await sqlApi.updateSavedQuery(id, data);
      loadSaved();
    } catch (err) {
      console.error("Failed to update query:", err);
    }
  };

  const handleDeleteSavedQuery = async (id: string) => {
    try {
      await sqlApi.deleteSavedQuery(id);
      loadSaved();
    } catch (err) {
      console.error("Failed to delete query:", err);
    }
  };

  const handleClearHistory = async () => {
    if (!selectedDatasetId) return;
    try {
      await sqlApi.clearHistory(selectedDatasetId);
      setHistory([]);
    } catch (err) {
      console.error("Failed to clear history:", err);
    }
  };

  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");

  const currentDataset = datasets.find((d) => d.id === selectedDatasetId);

  const workflowSteps = [
    {
      id: "schema",
      label: "Schema",
      status: (isExplorerOpen ? "completed" : "pending") as const,
      onClick: () => setIsExplorerOpen(!isExplorerOpen),
    },
    {
      id: "editor",
      label: "Editor",
      status: (currentSql.trim().length > 0 ? "completed" : "current") as const,
    },
    {
      id: "results",
      label: "Results",
      status: (queryResult ? "completed" : "pending") as const,
      onClick: () => setOutputTab("results"),
    },
  ];

  const secondaryRecommendations = [
    {
      id: "rec-limit",
      title: "Add LIMIT clause for interactive exploration",
      description: "Default query limits preserve client memory and return sub-20ms results.",
      actionLabel: "Add LIMIT 50",
      onAction: () => {
        if (!currentSql.toUpperCase().includes("LIMIT")) {
          handleChangeQuery(currentSql.replace(/;?\s*$/, "") + " LIMIT 50;");
        }
      },
      impact: "low" as const,
    },
    {
      id: "rec-explain",
      title: "Inspect AST execution plan",
      description: "Review query plan operators to verify filter pushdown and scan performance.",
      actionLabel: "Explain Query",
      onAction: () => handleExplainQuery(),
      impact: "medium" as const,
    },
  ];

  return (
    <div className="flex flex-col min-h-[calc(100vh-100px)]">
      <AnalyticalWorkspaceHeader
        title="SQL Workbench"
        description="Query your data using governed, read-only SQL."
        badgeText="Governed Read-Only"
        steps={workflowSteps}
        currentStepId={outputTab === "results" ? "results" : "editor"}
        mode={mode}
        onToggleMode={setMode}
        status={isRunning ? "running" : queryResult ? "success" : "idle"}
        durationMs={queryResult?.execution_time_ms}
        rowCount={queryResult?.row_count}
        primaryAction={
          <Button
            size="sm"
            onClick={handleAddTab}
            className="h-9 px-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs gap-1.5 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Query</span>
          </Button>
        }
        secondaryActions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExplorerOpen(!isExplorerOpen)}
            className="h-9 px-2.5 text-xs border-white/10 bg-slate-900/60 hover:bg-slate-850 hover:border-white/20 text-slate-300 gap-1.5"
          >
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span>{isExplorerOpen ? "Hide Schema" : "Show Schema"}</span>
          </Button>
        }
        customDatasetSelector={
          <div className="flex items-center gap-1.5 bg-slate-900/60 p-1 rounded-lg border border-white/10">
            <span className="text-[11px] font-medium text-slate-400 pl-2 pr-0.5 uppercase tracking-wider hidden sm:inline">
              Dataset:
            </span>
            <DatasetSelector
              datasets={datasets.map((d) => ({
                id: d.id,
                name: d.name,
                rowCount: (d as any).row_count,
                versionName: (d as any).current_version_name || "V1",
              }))}
              activeDatasetId={selectedDatasetId}
              onSelectDataset={(id) => {
                setSelectedDatasetId(id);
                setSelectedVersionId("");
              }}
              size="sm"
            />
            {versions.length > 0 && (
              <VersionSelector
                versions={versions.map((v) => ({
                  id: v.version_id,
                  version_number: parseInt(v.version_id.replace(/\D/g, "") || "1"),
                  row_count: v.row_count,
                  is_current: v.version_id === selectedVersionId,
                }))}
                activeVersionId={selectedVersionId || versions[0]?.version_id}
                onSelectVersion={(vid) => setSelectedVersionId(vid)}
                size="sm"
              />
            )}
          </div>
        }
        onRefresh={loadSchema}
        isRefreshing={schemaLoading}
      />

      {datasets.length === 0 ? (
        <GuidedOnboarding
          title="SQL Query Workbench"
          description="Filter, group, aggregate, and analyze your data using standard SQL syntax. Get instant query result tables, query plan breakdowns, and AI-assisted SQL query writing."
          badgeText="SQL Studio"
          features={[
            "Fast in-memory SQL execution over all your datasets",
            "Auto-complete table schemas, column names, and syntax highlighting",
            "Instant conversion of SQL result sets into interactive charts",
          ]}
        />
      ) : (
        /* Master Studio Workspace (Split View) */
        <div
          style={{
            flex: 1,
            display: "grid",
            gridTemplateColumns: isExplorerOpen ? "260px 1fr" : "1fr",
            gap: "0.75rem",
            overflow: "hidden",
            minHeight: 0,
          }}
        >
          {/* Left Panel: Schema Explorer */}
          {isExplorerOpen && (
            <div
              className="card"
              style={{
                height: "100%",
                overflow: "hidden",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
              }}
            >
              <SchemaExplorer
                schema={schema}
                templates={templates}
                loading={schemaLoading}
                onInsertText={handleInsertText}
                onSelectTemplate={handleSelectTemplate}
              />
            </div>
          )}

          {/* Right Panel: Editor & Output Split */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              height: "100%",
              overflow: "hidden",
              gap: "0.75rem",
              minHeight: 0,
            }}
          >
            {/* Top: SQL Editor */}
            <div style={{ flexShrink: 0 }}>
              <SQLEditor
                tabs={tabs}
                activeTabId={activeTabId}
                onSelectTab={handleSelectTab}
                onAddTab={handleAddTab}
                onCloseTab={handleCloseTab}
                onChangeQuery={handleChangeQuery}
                onRunQuery={handleRunQuery}
                onCancelQuery={handleCancelQuery}
                onValidateQuery={handleValidateQuery}
                onExplainQuery={handleExplainQuery}
                onSaveQuery={() => setOutputTab("saved")}
                onFormatQuery={handleFormatQuery}
                isRunning={isRunning}
                validationResult={validationResult}
                schema={schema}
              />
            </div>

            {/* Bottom: Tabbed Output Panel */}
            <div
              className="card"
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--bg-surface)",
                minHeight: 0,
              }}
            >
              {/* Output Tabs Header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  backgroundColor: "var(--bg-surface)",
                  borderBottom: "1px solid var(--border-subtle)",
                  padding: "0.25rem 0.75rem 0 0.75rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <button
                    type="button"
                    onClick={() => setOutputTab("results")}
                    className={`btn btn-sm ${outputTab === "results" ? "btn-primary" : "btn-secondary"}`}
                    style={{ fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "var(--radius-sm) var(--radius-sm) 0 0" }}
                  >
                    Results ({queryResult?.row_count ?? 0})
                  </button>

                  <button
                    type="button"
                    onClick={() => setOutputTab("visualizer")}
                    className={`btn btn-sm ${outputTab === "visualizer" ? "btn-primary" : "btn-secondary"}`}
                    style={{ fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "var(--radius-sm) var(--radius-sm) 0 0" }}
                  >
                    <BarChartIcon size={12} />
                    Visualizer ({queryResult?.suggested_charts?.length ?? 0})
                  </button>

                  <button
                    type="button"
                    onClick={() => setOutputTab("explain")}
                    className={`btn btn-sm ${outputTab === "explain" ? "btn-primary" : "btn-secondary"}`}
                    style={{ fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "var(--radius-sm) var(--radius-sm) 0 0" }}
                  >
                    <EyeIcon size={12} />
                    Execution Plan
                  </button>

                  <button
                    type="button"
                    onClick={() => setOutputTab("history")}
                    className={`btn btn-sm ${outputTab === "history" ? "btn-primary" : "btn-secondary"}`}
                    style={{ fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "var(--radius-sm) var(--radius-sm) 0 0" }}
                  >
                    <HistoryIcon size={12} />
                    History ({history.length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setOutputTab("saved")}
                    className={`btn btn-sm ${outputTab === "saved" ? "btn-primary" : "btn-secondary"}`}
                    style={{ fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "var(--radius-sm) var(--radius-sm) 0 0" }}
                  >
                    <SaveIcon size={12} />
                    Saved Queries ({savedQueries.length})
                  </button>
                </div>
              </div>

              {/* Output Tab Body */}
              <div style={{ flex: 1, overflow: "hidden", minHeight: 0 }}>
                {outputTab === "results" && (
                  <ResultPanel result={queryResult} loading={isRunning} />
                )}

                {outputTab === "visualizer" && (
                  <SQLVisualizer result={queryResult} />
                )}

                {outputTab === "explain" && (
                  <SQLExplainPanel plan={explainPlan} loading={isExplaining} />
                )}

                {outputTab === "history" && (
                  <QueryHistoryPanel
                    history={history}
                    onLoadQuery={handleChangeQuery}
                    onClearHistory={handleClearHistory}
                    loading={historyLoading}
                  />
                )}

                {outputTab === "saved" && (
                  <SavedQueriesPanel
                    queries={savedQueries}
                    onLoadQuery={handleChangeQuery}
                    onSaveQuery={handleSaveQuery}
                    onUpdateQuery={handleUpdateSavedQuery}
                    onDeleteQuery={handleDeleteSavedQuery}
                    currentSql={currentSql}
                    loading={savedLoading}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Secondary Information: History, Details, Metadata, Recommendations */}
      <SecondaryInfoPanel
        metadata={{
          datasetName: currentDataset?.name || "Active Dataset",
          versionName: selectedVersionId || "V1",
          rowCount: queryResult?.row_count ?? (currentDataset as any)?.row_count,
          columnCount: schema?.columns?.length,
          engine: "DuckDB (Governed Read-Only)",
          executionTimeMs: queryResult?.execution_time_ms,
          customFields: {
            "Table Alias": schema?.table_alias || "dataset",
            "Active Queries": tabs.length,
            "Saved Queries": savedQueries.length,
          },
        }}
        historyEntries={history.map((h) => ({
          id: h.query_id || String(h.executed_at),
          title: h.sql.slice(0, 45) + (h.sql.length > 45 ? "..." : ""),
          timestamp: h.executed_at,
          status: h.status === "SUCCESS" ? ("success" as const) : ("error" as const),
          durationMs: h.execution_time_ms,
          queryOrCommand: h.sql,
          summary: `${h.row_count ?? 0} rows returned`,
        }))}
        onSelectHistoryEntry={(entry) => {
          if (entry.queryOrCommand) handleChangeQuery(entry.queryOrCommand);
        }}
        onRerunHistoryEntry={(entry) => {
          if (entry.queryOrCommand) {
            handleChangeQuery(entry.queryOrCommand);
            handleRunQuery();
          }
        }}
        recommendations={secondaryRecommendations}
      />
    </div>
  );
}
