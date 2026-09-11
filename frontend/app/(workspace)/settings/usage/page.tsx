"use client";

import React, { useEffect, useState } from "react";
import { SettingsNav } from "@/components/settings/SettingsNav";
import {
  getUsageSummary,
  getUsageHistory,
  getPlanComparisonMatrix,
  changeWorkspacePlan,
  reconcileUsage,
} from "@/services/usageApi";
import {
  MetricUsageDetail,
  PlanComparisonItem,
  PlanComparisonResponse,
  PlanTier,
  UsageHistoryItem,
  UsageReconciliationReport,
  UsageSummaryResponse,
} from "@/types/usage";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Check,
  CheckCircle2,
  Clock,
  Coins,
  Cpu,
  Database,
  Download,
  HardDrive,
  HelpCircle,
  Layers,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Users,
  X,
  Zap,
} from "lucide-react";

export default function UsageStudioPage() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<UsageSummaryResponse | null>(null);
  const [history, setHistory] = useState<UsageHistoryItem[]>([]);
  const [comparison, setComparison] = useState<PlanComparisonItem[]>([]);
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const [reconciling, setReconciling] = useState(false);
  const [reconciliationReport, setReconciliationReport] = useState<UsageReconciliationReport | null>(null);
  const [selectedTier, setSelectedTier] = useState<PlanTier>("PRO");
  const [filterPeriod, setFilterPeriod] = useState<string>("");

  const loadAllData = async () => {
    try {
      setLoading(true);
      const [sumData, histData, compData] = await Promise.all([
        getUsageSummary(),
        getUsageHistory({ limit: 15 }),
        getPlanComparisonMatrix(),
      ]);
      setSummary(sumData);
      setHistory(histData.events || []);
      setComparison(compData.comparisons || []);
    } catch (err: any) {
      console.error("Failed to load usage data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handlePlanChange = async (tier: PlanTier) => {
    try {
      setUpgrading(true);
      const wsId = summary?.workspace_id || "default";
      await changeWorkspacePlan(wsId, tier, "User changed plan in Usage Studio");
      await loadAllData();
      setIsUpgradeModalOpen(false);
    } catch (err: any) {
      alert(`Plan switch error: ${err?.message || "Failed to change plan"}`);
    } finally {
      setUpgrading(false);
    }
  };

  const handleReconcile = async () => {
    try {
      setReconciling(true);
      const report = await reconcileUsage(summary?.workspace_id);
      setReconciliationReport(report);
    } catch (err: any) {
      alert(`Reconciliation failed: ${err?.message || "Error"}`);
    } finally {
      setReconciling(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (!bytes || bytes === 0) return "0 MB";
    const mb = bytes / (1024 * 1024);
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(2)} GB`;
  };

  const getHealthBadgeClass = (status: string) => {
    switch (status) {
      case "NORMAL":
        return "badge-normal";
      case "WARNING":
        return "badge-warning";
      case "CRITICAL":
        return "badge-critical";
      case "EXCEEDED":
        return "badge-exceeded";
      default:
        return "badge-normal";
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage < 70) return "#10b981"; // Emerald green
    if (percentage < 90) return "#f59e0b"; // Amber yellow
    return "#ef4444"; // Rose red
  };

  const hasOverage = summary?.quotas?.some((q) => q.is_exceeded);

  return (
    <div className="usage-page">
      <div className="usage-header-wrap">
        <div>
          <h1 className="page-title">Usage, Quotas & Plan Studio</h1>
          <p className="page-subtitle">
            Authoritative resource accounting, plan entitlements, and continuous quota governance.
          </p>
        </div>
        <div className="header-actions">
          <button
            className="btn-reconcile"
            onClick={handleReconcile}
            disabled={reconciling}
            title="Audit event ledger against rolled up aggregations"
          >
            <RefreshCw size={15} className={reconciling ? "animate-spin" : ""} />
            <span>{reconciling ? "Auditing..." : "Reconcile Ledger"}</span>
          </button>
          <button
            className="btn-upgrade-main"
            onClick={() => setIsUpgradeModalOpen(true)}
          >
            <Sparkles size={16} />
            <span>Change Plan</span>
          </button>
        </div>
      </div>

      <SettingsNav />

      {loading && (
        <div className="loading-state">
          <RefreshCw size={32} className="animate-spin text-primary" />
          <p>Gathering deterministic usage telemetry and plan status...</p>
        </div>
      )}

      {!loading && summary && (
        <>
          {/* Downgrade & Overage Safety Notice */}
          {hasOverage && (
            <div className="overage-banner">
              <div className="overage-icon">
                <AlertTriangle size={20} />
              </div>
              <div className="overage-text">
                <strong>Plan Quota Exceeded Notice</strong>
                <p>
                  Certain analytical capabilities have reached 100% consumption. In accordance with
                  our safety constitution, existing datasets, lineage, and models are permanently preserved.
                  Upgrade your tier to unlock additional analytical quota.
                </p>
              </div>
              <button
                className="btn-overage-upgrade"
                onClick={() => setIsUpgradeModalOpen(true)}
              >
                Upgrade Now
              </button>
            </div>
          )}

          {/* Reconciliation Diagnostic Result */}
          {reconciliationReport && (
            <div className={`reconcile-banner ${reconciliationReport.is_healthy ? "healthy" : "warning"}`}>
              <div className="reconcile-icon">
                {reconciliationReport.is_healthy ? <ShieldCheck size={20} /> : <AlertTriangle size={20} />}
              </div>
              <div className="reconcile-text">
                <strong>
                  Ledger Audit: {reconciliationReport.is_healthy ? "Verified Clean" : "Discrepancy Detected"}
                </strong>
                <p>
                  Audited {reconciliationReport.metrics_audited} metrics against immutable event log for period{" "}
                  <code>{reconciliationReport.period_key}</code>. Discrepancies found:{" "}
                  {reconciliationReport.discrepancies_found}.
                </p>
              </div>
              <button
                className="btn-close-reconcile"
                onClick={() => setReconciliationReport(null)}
              >
                <X size={16} />
              </button>
            </div>
          )}

          {/* Active Plan Overview Card */}
          <div className="active-plan-card">
            <div className="plan-badge-row">
              <div className="plan-title-box">
                <span className="current-plan-chip">{summary.plan_code}</span>
                <h2>{summary.plan.name}</h2>
              </div>
              <div className="period-countdown">
                <Clock size={16} />
                <span>
                  Quota Cycle: <strong>{summary.days_remaining} days remaining</strong> (Resets on{" "}
                  {summary.period_end})
                </span>
              </div>
            </div>
            <p className="plan-description">{summary.plan.description}</p>
          </div>

          {/* Point-in-Time Resources Section */}
          <div className="section-title-wrap">
            <HardDrive size={18} className="section-icon" />
            <h3>Point-in-Time Resources</h3>
            <span className="section-badge">Physical Allocation</span>
          </div>

          <div className="meters-grid">
            {summary.resources?.map((res) => {
              const isStorage = res.metric_key.includes("storage") || res.metric_key.includes("size");
              const usedDisplay = isStorage ? formatBytes(res.used) : res.used.toLocaleString();
              const limitDisplay = res.limit !== null
                ? isStorage
                  ? formatBytes(res.limit)
                  : res.limit.toLocaleString()
                : "Unlimited";

              return (
                <div key={res.metric_key} className="meter-card">
                  <div className="meter-header">
                    <div>
                      <h4 className="meter-name">{res.display_name}</h4>
                      <span className="meter-category">{res.category}</span>
                    </div>
                    <span className={`health-pill ${getHealthBadgeClass(res.status)}`}>
                      {res.status}
                    </span>
                  </div>

                  <div className="meter-figures">
                    <span className="used-figure">{usedDisplay}</span>
                    <span className="limit-figure">/ {limitDisplay}</span>
                  </div>

                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill"
                      style={{
                        width: `${Math.min(res.percentage, 100)}%`,
                        backgroundColor: getProgressColor(res.percentage),
                      }}
                    />
                  </div>

                  <div className="meter-footer">
                    <span>{res.percentage.toFixed(1)}% consumed</span>
                    {res.remaining !== null && (
                      <span>
                        {isStorage ? formatBytes(res.remaining) : res.remaining.toLocaleString()} free
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Monthly Analytical Quotas Section */}
          <div className="section-title-wrap mt-8">
            <Zap size={18} className="section-icon" />
            <h3>Monthly Analytical Quotas</h3>
            <span className="section-badge">Reset Monthly</span>
          </div>

          <div className="meters-grid">
            {summary.quotas?.filter((q) => q.period === "MONTHLY").map((q) => (
              <div key={q.metric_key} className="meter-card">
                <div className="meter-header">
                  <div>
                    <h4 className="meter-name">{q.display_name}</h4>
                    <p className="meter-desc">{q.description}</p>
                  </div>
                  <span className={`health-pill ${getHealthBadgeClass(q.status)}`}>
                    {q.status}
                  </span>
                </div>

                <div className="meter-figures">
                  <span className="used-figure">{q.used.toLocaleString()}</span>
                  <span className="limit-figure">
                    / {q.limit !== null ? q.limit.toLocaleString() : "Unlimited"} {q.unit}
                  </span>
                </div>

                <div className="progress-bar-bg">
                  <div
                    className="progress-bar-fill"
                    style={{
                      width: `${Math.min(q.percentage, 100)}%`,
                      backgroundColor: getProgressColor(q.percentage),
                    }}
                  />
                </div>

                <div className="meter-footer">
                  <span>{q.percentage.toFixed(1)}% utilized</span>
                  <span>
                    {q.remaining !== null ? `${q.remaining.toLocaleString()} remaining` : "Uncapped"}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Plan Comparison Matrix Table */}
          <div className="section-title-wrap mt-8">
            <Layers size={18} className="section-icon" />
            <h3>Plan Entitlements Comparison Matrix</h3>
            <span className="section-badge">All Tiers</span>
          </div>

          <div className="matrix-table-card">
            <table className="matrix-table">
              <thead>
                <tr>
                  <th>Feature Capability</th>
                  <th>Category</th>
                  <th className={summary.plan_code === "FREE" ? "current-col" : ""}>
                    FREE {summary.plan_code === "FREE" && "(Current)"}
                  </th>
                  <th className={summary.plan_code === "PRO" ? "current-col" : ""}>
                    PRO {summary.plan_code === "PRO" && "(Current)"}
                  </th>
                  <th className={summary.plan_code === "TEAM" ? "current-col" : ""}>
                    TEAM {summary.plan_code === "TEAM" && "(Current)"}
                  </th>
                  <th className={summary.plan_code === "ENTERPRISE" ? "current-col" : ""}>
                    ENTERPRISE {summary.plan_code === "ENTERPRISE" && "(Current)"}
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((item) => (
                  <tr key={item.feature_key}>
                    <td className="font-semibold text-white">{item.display_name}</td>
                    <td className="text-muted text-xs uppercase tracking-wider">{item.category}</td>
                    <td className={summary.plan_code === "FREE" ? "current-col" : ""}>{item.free_value}</td>
                    <td className={summary.plan_code === "PRO" ? "current-col" : ""}>{item.pro_value}</td>
                    <td className={summary.plan_code === "TEAM" ? "current-col" : ""}>{item.team_value}</td>
                    <td className={summary.plan_code === "ENTERPRISE" ? "current-col" : ""}>
                      {item.enterprise_value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Usage Audit Log / Event History */}
          <div className="section-title-wrap mt-8">
            <Activity size={18} className="section-icon" />
            <h3>Append-Only Usage Audit Log</h3>
            <span className="section-badge">Immutable Ledger</span>
          </div>

          <div className="history-table-card">
            {history.length === 0 ? (
              <div className="empty-history">
                <Activity size={24} className="text-muted mb-2" />
                <p>No recorded analytical events in this billing cycle yet.</p>
              </div>
            ) : (
              <table className="matrix-table history-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Metric</th>
                    <th>Consumed Quantity</th>
                    <th>Operation Type</th>
                    <th>User ID</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((evt) => (
                    <tr key={evt.usage_event_id}>
                      <td className="text-xs text-muted">
                        {new Date(evt.occurred_at).toLocaleString()}
                      </td>
                      <td className="font-mono text-xs text-primary font-medium">
                        {evt.metric_key}
                      </td>
                      <td className="font-bold">
                        +{evt.quantity} {evt.unit}
                      </td>
                      <td>
                        <span className="op-tag">{evt.operation_type}</span>
                      </td>
                      <td className="text-xs text-muted font-mono">{evt.user_id || "system"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* Upgrade / Plan Mutation Modal */}
      {isUpgradeModalOpen && (
        <div className="upgrade-modal-backdrop" onClick={() => setIsUpgradeModalOpen(false)}>
          <div className="upgrade-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="upgrade-modal-header">
              <div className="modal-title-wrap">
                <Sparkles size={22} className="text-primary" />
                <h3>Change Workspace Plan</h3>
              </div>
              <button
                className="btn-close-modal"
                onClick={() => setIsUpgradeModalOpen(false)}
              >
                <X size={20} />
              </button>
            </div>
            <p className="modal-subtitle">
              Instant activation. Your analytical data, models, and history are preserved without interruption.
            </p>

            <div className="tiers-selection-grid">
              {(["FREE", "PRO", "TEAM", "ENTERPRISE"] as PlanTier[]).map((tier) => {
                const isCurrent = summary?.plan_code === tier;
                return (
                  <div
                    key={tier}
                    className={`tier-pick-card ${tier === "PRO" ? "featured" : ""} ${isCurrent ? "current" : ""}`}
                  >
                    <div className="tier-header-inner">
                      <span className="tier-pill">{tier}</span>
                      {isCurrent && <span className="current-badge">Active</span>}
                    </div>
                    <h4>{tier === "FREE" ? "Free" : tier === "PRO" ? "Pro" : tier === "TEAM" ? "Team" : "Enterprise"}</h4>
                    <p className="tier-pricing">
                      {tier === "FREE" ? "$0" : tier === "PRO" ? "$29" : tier === "TEAM" ? "$99" : "Custom"}
                      <span className="period-span">/month</span>
                    </p>
                    <ul className="tier-bullets">
                      {tier === "FREE" && (
                        <>
                          <li><Check size={14} /> 100 AI Analyst queries</li>
                          <li><Check size={14} /> 1 GB Dataset storage</li>
                          <li><Check size={14} /> 3 Active projects</li>
                        </>
                      )}
                      {tier === "PRO" && (
                        <>
                          <li><Check size={14} /> 1,000 AI Analyst queries</li>
                          <li><Check size={14} /> 20 GB Dataset storage</li>
                          <li><Check size={14} /> 200 ML Experiments & Forecasts</li>
                          <li><Check size={14} /> Unlimited SQL Analytics</li>
                        </>
                      )}
                      {tier === "TEAM" && (
                        <>
                          <li><Check size={14} /> 5,000 AI Analyst queries</li>
                          <li><Check size={14} /> 100 GB Dataset storage</li>
                          <li><Check size={14} /> 1,000 ML Experiments</li>
                          <li><Check size={14} /> 25 Team members</li>
                        </>
                      )}
                      {tier === "ENTERPRISE" && (
                        <>
                          <li><Check size={14} /> Uncapped AI inquiries</li>
                          <li><Check size={14} /> 1 TB High-speed storage</li>
                          <li><Check size={14} /> Custom quotas & limits</li>
                          <li><Check size={14} /> Dedicated support</li>
                        </>
                      )}
                    </ul>

                    <button
                      className={`btn-select-tier ${isCurrent ? "btn-disabled" : tier === "PRO" ? "btn-glow" : ""}`}
                      disabled={isCurrent || upgrading}
                      onClick={() => handlePlanChange(tier)}
                    >
                      {isCurrent ? "Current Plan" : upgrading ? "Switching..." : `Select ${tier}`}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .usage-page {
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem 1.5rem 4rem;
        }
        .usage-header-wrap {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 1.5rem;
          gap: 1.5rem;
        }
        .page-title {
          font-size: 1.75rem;
          font-weight: 700;
          color: #f8fafc;
          margin: 0 0 0.4rem 0;
        }
        .page-subtitle {
          font-size: 0.925rem;
          color: #94a3b8;
          margin: 0;
        }
        .header-actions {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .btn-reconcile {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.55rem 0.9rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 8px;
          color: #cbd5e1;
          font-size: 0.825rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.15s;
        }
        .btn-reconcile:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
          color: #ffffff;
        }
        .btn-upgrade-main {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.55rem 1.1rem;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border: none;
          border-radius: 8px;
          color: #ffffff;
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s, transform 0.15s;
        }
        .btn-upgrade-main:hover {
          opacity: 0.92;
          transform: translateY(-1px);
        }
        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 4rem 2rem;
          gap: 1rem;
          color: #94a3b8;
        }

        /* Banners */
        .overage-banner {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1rem 1.25rem;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 10px;
          margin-bottom: 1.5rem;
        }
        .overage-icon {
          color: #ef4444;
          flex-shrink: 0;
        }
        .overage-text {
          flex: 1;
        }
        .overage-text strong {
          color: #f87171;
          display: block;
          margin-bottom: 0.2rem;
        }
        .overage-text p {
          margin: 0;
          font-size: 0.85rem;
          color: #cbd5e1;
        }
        .btn-overage-upgrade {
          padding: 0.45rem 0.9rem;
          background: #ef4444;
          color: #ffffff;
          border: none;
          border-radius: 6px;
          font-size: 0.825rem;
          font-weight: 600;
          cursor: pointer;
        }

        .reconcile-banner {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.85rem 1.25rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
        }
        .reconcile-banner.healthy {
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.25);
        }
        .reconcile-banner.warning {
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.25);
        }
        .reconcile-text {
          flex: 1;
        }
        .reconcile-text strong {
          font-size: 0.9rem;
          color: #f8fafc;
        }
        .reconcile-text p {
          margin: 0;
          font-size: 0.825rem;
          color: #94a3b8;
        }
        .btn-close-reconcile {
          background: transparent;
          border: none;
          color: #64748b;
          cursor: pointer;
        }

        /* Active Plan Card */
        .active-plan-card {
          background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 1.5rem;
          margin-bottom: 2rem;
        }
        .plan-badge-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }
        .plan-title-box {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .current-plan-chip {
          display: inline-block;
          padding: 0.25rem 0.6rem;
          background: #6366f1;
          color: #ffffff;
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.05em;
          border-radius: 6px;
        }
        .plan-title-box h2 {
          margin: 0;
          font-size: 1.35rem;
          color: #f8fafc;
        }
        .period-countdown {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.85rem;
          color: #94a3b8;
        }
        .plan-description {
          margin: 0;
          font-size: 0.9rem;
          color: #94a3b8;
          max-width: 700px;
        }

        /* Section Headings */
        .section-title-wrap {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          margin-bottom: 1rem;
        }
        .section-icon {
          color: #818cf8;
        }
        .section-title-wrap h3 {
          margin: 0;
          font-size: 1.1rem;
          color: #f8fafc;
        }
        .section-badge {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          padding: 0.2rem 0.5rem;
          background: rgba(255, 255, 255, 0.06);
          color: #94a3b8;
          border-radius: 4px;
        }
        .mt-8 {
          margin-top: 2.5rem;
        }

        /* Meters Grid */
        .meters-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 1.25rem;
        }
        .meter-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 10px;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
        }
        .meter-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 0.75rem;
        }
        .meter-name {
          margin: 0 0 0.2rem 0;
          font-size: 0.95rem;
          font-weight: 600;
          color: #f8fafc;
        }
        .meter-category {
          font-size: 0.75rem;
          color: #64748b;
          text-transform: uppercase;
        }
        .meter-desc {
          margin: 0;
          font-size: 0.75rem;
          color: #94a3b8;
        }
        .health-pill {
          font-size: 0.7rem;
          font-weight: 700;
          padding: 0.15rem 0.5rem;
          border-radius: 4px;
          text-transform: uppercase;
        }
        .badge-normal {
          background: rgba(16, 185, 129, 0.15);
          color: #34d399;
        }
        .badge-warning {
          background: rgba(245, 158, 11, 0.15);
          color: #fbbf24;
        }
        .badge-critical {
          background: rgba(249, 115, 22, 0.15);
          color: #fb923c;
        }
        .badge-exceeded {
          background: rgba(239, 68, 68, 0.2);
          color: #f87171;
        }
        .meter-figures {
          margin-bottom: 0.5rem;
        }
        .used-figure {
          font-size: 1.35rem;
          font-weight: 700;
          color: #f8fafc;
        }
        .limit-figure {
          font-size: 0.85rem;
          color: #94a3b8;
          margin-left: 0.35rem;
        }
        .progress-bar-bg {
          height: 7px;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 0.5rem;
        }
        .progress-bar-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }
        .meter-footer {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        /* Matrix Table */
        .matrix-table-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 10px;
          overflow-x: auto;
        }
        .matrix-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.85rem;
          text-align: left;
        }
        .matrix-table th {
          padding: 0.85rem 1rem;
          background: rgba(15, 23, 42, 0.8);
          color: #cbd5e1;
          font-weight: 600;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .matrix-table td {
          padding: 0.75rem 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          color: #cbd5e1;
        }
        .current-col {
          background: rgba(99, 102, 241, 0.06);
          color: #a5b4fc !important;
          font-weight: 600;
        }
        .history-table td {
          padding: 0.65rem 1rem;
        }
        .op-tag {
          font-size: 0.75rem;
          padding: 0.15rem 0.45rem;
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.06);
          color: #94a3b8;
        }
        .empty-history {
          padding: 3rem;
          text-align: center;
          color: #64748b;
        }

        /* Modal */
        .upgrade-modal-backdrop {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.75);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          padding: 1rem;
        }
        .upgrade-modal-card {
          background: #0f172a;
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 16px;
          width: 100%;
          max-width: 900px;
          padding: 2rem;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
        }
        .upgrade-modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.4rem;
        }
        .modal-title-wrap {
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }
        .modal-title-wrap h3 {
          margin: 0;
          font-size: 1.35rem;
          color: #f8fafc;
        }
        .btn-close-modal {
          background: transparent;
          border: none;
          color: #64748b;
          cursor: pointer;
        }
        .btn-close-modal:hover {
          color: #ffffff;
        }
        .modal-subtitle {
          font-size: 0.875rem;
          color: #94a3b8;
          margin: 0 0 1.75rem 0;
        }
        .tiers-selection-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
        }
        .tier-pick-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
        }
        .tier-pick-card.featured {
          border-color: rgba(99, 102, 241, 0.5);
          background: rgba(30, 41, 59, 0.8);
        }
        .tier-pick-card.current {
          border-color: rgba(16, 185, 129, 0.4);
        }
        .tier-header-inner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }
        .tier-pill {
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 0.05em;
          padding: 0.15rem 0.45rem;
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.1);
          color: #cbd5e1;
        }
        .current-badge {
          font-size: 0.65rem;
          font-weight: 700;
          color: #34d399;
          background: rgba(16, 185, 129, 0.15);
          padding: 0.15rem 0.45rem;
          border-radius: 4px;
        }
        .tier-pick-card h4 {
          margin: 0 0 0.35rem 0;
          font-size: 1.1rem;
          color: #f8fafc;
        }
        .tier-pricing {
          font-size: 1.5rem;
          font-weight: 700;
          color: #f8fafc;
          margin: 0 0 1rem 0;
        }
        .period-span {
          font-size: 0.8rem;
          font-weight: 400;
          color: #94a3b8;
          margin-left: 0.2rem;
        }
        .tier-bullets {
          list-style: none;
          padding: 0;
          margin: 0 0 1.25rem 0;
          flex: 1;
        }
        .tier-bullets li {
          display: flex;
          align-items: flex-start;
          gap: 0.4rem;
          font-size: 0.775rem;
          color: #cbd5e1;
          margin-bottom: 0.45rem;
          line-height: 1.4;
        }
        .btn-select-tier {
          padding: 0.55rem;
          border-radius: 6px;
          border: 1px solid rgba(255, 255, 255, 0.15);
          background: rgba(255, 255, 255, 0.06);
          color: #ffffff;
          font-size: 0.825rem;
          font-weight: 600;
          cursor: pointer;
        }
        .btn-glow {
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border: none;
        }
        .btn-disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
