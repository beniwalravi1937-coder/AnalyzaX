"use client";

import React, { useEffect, useState } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import {
  AggregationType,
  MetricDefinition,
  MetricStatus,
  MetricVersionRecord,
} from "@/types/copilot";
import {
  createGovernedMetric,
  deleteGovernedMetric,
  getMetricVersions,
  listGovernedMetrics,
  updateGovernedMetric,
  validateMetricFormula,
} from "@/services/copilotApi";
import {
  AlertCircle,
  Calculator,
  CheckCircle2,
  Clock,
  History,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Tag,
  Trash2,
} from "lucide-react";

export default function MetricsPage() {
  const { activeWorkspace, activeProject } = useWorkspace();

  const [metrics, setMetrics] = useState<MetricDefinition[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create / Edit modal state
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingMetric, setEditingMetric] = useState<MetricDefinition | null>(null);
  const [formName, setFormName] = useState<string>("");
  const [formDescription, setFormDescription] = useState<string>("");
  const [formExpression, setFormExpression] = useState<string>("");
  const [formAggregation, setFormAggregation] = useState<AggregationType>("SUM");
  const [formUnit, setFormUnit] = useState<string>("");
  const [formSynonyms, setFormSynonyms] = useState<string>("");
  const [validationResult, setValidationResult] = useState<{ is_valid: boolean; error_message?: string } | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);

  // Version history modal state
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [selectedMetricHistory, setSelectedMetricHistory] = useState<MetricVersionRecord[]>([]);
  const [historyMetricName, setHistoryMetricName] = useState<string>("");

  const fetchMetrics = async () => {
    if (!activeWorkspace?.workspace_id) return;
    try {
      setLoading(true);
      const data = await listGovernedMetrics({
        workspace_id: activeWorkspace.workspace_id,
        project_id: activeProject?.project_id,
        status: statusFilter !== "ALL" ? (statusFilter as MetricStatus) : undefined,
      });
      setMetrics(data);
    } catch (err) {
      console.error("Failed to load metrics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [activeWorkspace?.workspace_id, activeProject?.project_id, statusFilter]);

  const handleValidateExpression = async (expr: string) => {
    setFormExpression(expr);
    if (!expr.trim()) {
      setValidationResult(null);
      return;
    }
    try {
      setIsValidating(true);
      const res = await validateMetricFormula(expr);
      setValidationResult(res);
    } catch (err) {
      setValidationResult({ is_valid: false, error_message: "Validation request failed" });
    } finally {
      setIsValidating(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingMetric(null);
    setFormName("");
    setFormDescription("");
    setFormExpression("");
    setFormAggregation("SUM");
    setFormUnit("");
    setFormSynonyms("");
    setValidationResult(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (m: MetricDefinition) => {
    setEditingMetric(m);
    setFormName(m.name);
    setFormDescription(m.description);
    setFormExpression(m.expression);
    setFormAggregation(m.aggregation);
    setFormUnit(m.unit || "");
    setFormSynonyms(m.synonyms.join(", "));
    setValidationResult({ is_valid: true });
    setIsModalOpen(true);
  };

  const handleSaveMetric = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace?.workspace_id) return;
    if (validationResult && !validationResult.is_valid) return;

    try {
      const synList = formSynonyms.split(",").map((s) => s.trim()).filter(Boolean);

      if (editingMetric) {
        await updateGovernedMetric(editingMetric.metric_id, {
          name: formName,
          description: formDescription,
          expression: formExpression,
          unit: formUnit || null,
          synonyms: synList,
          change_summary: `Updated expression/metadata via governance UI`,
        });
      } else {
        await createGovernedMetric({
          workspace_id: activeWorkspace.workspace_id,
          project_id: activeProject?.project_id,
          name: formName,
          description: formDescription,
          expression: formExpression,
          aggregation: formAggregation,
          unit: formUnit || null,
          synonyms: synList,
        });
      }
      setIsModalOpen(false);
      fetchMetrics();
    } catch (err: any) {
      alert(err.message || "Failed to save metric definition.");
    }
  };

  const handleDelete = async (metricId: string) => {
    if (!confirm("Are you sure you want to delete this governed metric? Historical records will be removed.")) return;
    try {
      await deleteGovernedMetric(metricId);
      setMetrics((prev) => prev.filter((m) => m.metric_id !== metricId));
    } catch (err: any) {
      alert(err.message || "Failed to delete metric.");
    }
  };

  const handleViewHistory = async (metric: MetricDefinition) => {
    try {
      const versions = await getMetricVersions(metric.metric_id);
      setSelectedMetricHistory(versions);
      setHistoryMetricName(metric.name);
      setIsHistoryOpen(true);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  };

  const filteredMetrics = metrics.filter((m) =>
    m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.expression.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full overflow-hidden p-6 space-y-6 text-zinc-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2.5">
            <Calculator className="w-6 h-6 text-blue-400" />
            Governed Semantic Metrics
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Standardized business definitions with AST formula validation, version history, and cycle detection.
          </p>
        </div>

        <button
          onClick={handleOpenCreate}
          className="flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-lg shadow-blue-900/20"
        >
          <Plus className="w-4 h-4" />
          Define Metric
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-zinc-500" />
            <input
              type="text"
              placeholder="Search metrics, formulas, synonyms..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-zinc-200 outline-none w-64 focus:border-blue-500/50"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="DRAFT">Draft</option>
            <option value="DEPRECATED">Deprecated</option>
          </select>
        </div>

        <div className="text-xs text-zinc-400">
          Showing <span className="text-zinc-200 font-semibold">{filteredMetrics.length}</span> governed metrics
        </div>
      </div>

      {/* Metrics Table */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
        {loading ? (
          <div className="flex items-center justify-center p-12 text-zinc-500">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
            Loading governed metrics...
          </div>
        ) : filteredMetrics.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-center text-zinc-500">
            <Calculator className="w-10 h-10 text-zinc-600 mb-3" />
            <p className="font-medium text-zinc-300">No governed metrics found</p>
            <p className="text-xs text-zinc-500 mt-1">
              Click &quot;Define Metric&quot; to establish your workspace&apos;s first standardized business metric.
            </p>
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-950/40 text-zinc-400">
                <th className="p-3.5 font-medium">Metric Name</th>
                <th className="p-3.5 font-medium">Safe Formula / Expression</th>
                <th className="p-3.5 font-medium">Aggregation</th>
                <th className="p-3.5 font-medium">Unit</th>
                <th className="p-3.5 font-medium">Version</th>
                <th className="p-3.5 font-medium">Status</th>
                <th className="p-3.5 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {filteredMetrics.map((m) => (
                <tr key={m.metric_id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="p-3.5">
                    <div className="font-semibold text-zinc-100">{m.name}</div>
                    {m.description && <div className="text-[11px] text-zinc-400 mt-0.5">{m.description}</div>}
                    {m.synonyms.length > 0 && (
                      <div className="flex items-center gap-1 mt-1 text-[10px] text-zinc-500">
                        <Tag className="w-3 h-3" />
                        <span>{m.synonyms.join(", ")}</span>
                      </div>
                    )}
                  </td>
                  <td className="p-3.5 font-mono text-zinc-300">
                    <code className="bg-zinc-950/70 px-2 py-1 rounded border border-zinc-800 text-purple-300">
                      {m.expression}
                    </code>
                  </td>
                  <td className="p-3.5 font-mono text-zinc-400">{m.aggregation}</td>
                  <td className="p-3.5 text-zinc-400">{m.unit || "—"}</td>
                  <td className="p-3.5">
                    <button
                      onClick={() => handleViewHistory(m)}
                      className="flex items-center gap-1 font-mono text-blue-400 hover:text-blue-300"
                    >
                      <History className="w-3 h-3" />
                      v{m.version}
                    </button>
                  </td>
                  <td className="p-3.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        m.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : m.status === "DRAFT"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-zinc-500/10 text-zinc-400 border-zinc-500/20"
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="p-3.5 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleOpenEdit(m)}
                        title="Edit Metric"
                        className="p-1.5 text-zinc-400 hover:text-zinc-200 rounded hover:bg-zinc-800 transition-colors"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(m.metric_id)}
                        title="Delete Metric"
                        className="p-1.5 text-zinc-500 hover:text-red-400 rounded hover:bg-zinc-800 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create / Edit Metric Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="font-bold text-lg text-zinc-100">
              {editingMetric ? "Edit Governed Metric" : "Define New Metric"}
            </h3>

            <form onSubmit={handleSaveMetric} className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Metric Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Net Revenue, Gross Margin, Churn Rate"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-zinc-200 outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">
                  Safe Formula Expression * (AST Validated)
                </label>
                <textarea
                  required
                  rows={2}
                  placeholder="e.g. SUM(revenue) - SUM(discounts) OR conversions / sessions"
                  value={formExpression}
                  onChange={(e) => handleValidateExpression(e.target.value)}
                  className="w-full font-mono bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-zinc-200 outline-none focus:border-blue-500"
                />
                {isValidating && <div className="text-zinc-500 text-[10px] mt-1">Validating AST syntax...</div>}
                {validationResult && (
                  <div
                    className={`flex items-center gap-1.5 mt-1 text-[11px] ${
                      validationResult.is_valid ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {validationResult.is_valid ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Valid mathematical expression</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>{validationResult.error_message}</span>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Aggregation</label>
                  <select
                    value={formAggregation}
                    onChange={(e) => setFormAggregation(e.target.value as AggregationType)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-zinc-200 outline-none"
                  >
                    <option value="SUM">SUM</option>
                    <option value="AVG">AVG</option>
                    <option value="COUNT">COUNT</option>
                    <option value="MIN">MIN</option>
                    <option value="MAX">MAX</option>
                    <option value="CUSTOM">CUSTOM</option>
                  </select>
                </div>

                <div>
                  <label className="block text-zinc-400 font-medium mb-1">Unit</label>
                  <input
                    type="text"
                    placeholder="e.g. USD, %, count, ms"
                    value={formUnit}
                    onChange={(e) => setFormUnit(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-zinc-200 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">Synonyms (Comma-separated)</label>
                <input
                  type="text"
                  placeholder="e.g. sales, turnover, gross revenue"
                  value={formSynonyms}
                  onChange={(e) => setFormSynonyms(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-zinc-200 outline-none"
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">Description / Business Context</label>
                <input
                  type="text"
                  placeholder="Brief context for AI Analyst and team..."
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-zinc-200 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={validationResult !== null && !validationResult.is_valid}
                  className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-50"
                >
                  Save Metric
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {isHistoryOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-zinc-100">
                Version History: {historyMetricName}
              </h3>
              <button
                onClick={() => setIsHistoryOpen(false)}
                className="text-zinc-500 hover:text-zinc-300 text-xs"
              >
                Close
              </button>
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {selectedMetricHistory.length === 0 ? (
                <p className="text-xs text-zinc-500">No version records recorded.</p>
              ) : (
                selectedMetricHistory.map((vh) => (
                  <div key={vh.version} className="p-3 rounded-lg bg-zinc-950/70 border border-zinc-800 text-xs space-y-1">
                    <div className="flex items-center justify-between text-zinc-400">
                      <span className="font-mono text-blue-400 font-semibold">Version {vh.version}</span>
                      <span className="text-[10px] text-zinc-500">{vh.created_at?.slice(0, 19)}</span>
                    </div>
                    <div className="font-mono text-[11px] text-purple-300 bg-zinc-900 px-2 py-1 rounded">
                      {vh.expression}
                    </div>
                    <div className="text-zinc-400 text-[11px] pt-1">
                      By {vh.changed_by}: <span className="italic text-zinc-300">{vh.change_summary}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
