"use client";

import React, { useEffect, useState } from "react";
import { getCurrentPlan, getUsageSummary, changeWorkspacePlan } from "@/services/usageApi";
import { PlanTier, UsageSummaryResponse, WorkspacePlanAssignment } from "@/types/usage";
import { Sparkles, ShieldAlert, ArrowUpRight, CheckCircle2, X } from "lucide-react";

interface FeatureGateProps {
  featureKey: string;
  metricKey?: string;
  workspaceId?: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradeBanner?: boolean;
}

export const FeatureGate: React.FC<FeatureGateProps> = ({
  featureKey,
  metricKey,
  workspaceId,
  children,
  fallback,
  showUpgradeBanner = true,
}) => {
  const [loading, setLoading] = useState(true);
  const [hasAccess, setHasAccess] = useState(true);
  const [reason, setReason] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<string>("FREE");
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function evaluateAccess() {
      try {
        setLoading(true);
        const planData: WorkspacePlanAssignment = await getCurrentPlan(workspaceId);
        if (!isMounted) return;
        setCurrentPlan(planData.plan_code);

        const ent =
          planData.entitlements[featureKey] ||
          planData.entitlements[featureKey.toLowerCase()] ||
          planData.entitlements[featureKey.toUpperCase()];

        if (!ent || !ent.enabled) {
          setHasAccess(false);
          setReason(`This capability requires a higher tier than your current ${planData.plan_code} plan.`);
          return;
        }

        // If a specific metric key is provided, check quota usage
        if (metricKey) {
          const summary: UsageSummaryResponse = await getUsageSummary(workspaceId);
          if (!isMounted) return;
          const quota = summary.quotas.find(
            (q) => q.metric_key.toLowerCase() === metricKey.toLowerCase()
          );
          if (quota && quota.is_exceeded) {
            setHasAccess(false);
            setReason(`You have reached 100% of your monthly quota for ${quota.display_name}.`);
            return;
          }
        }

        setHasAccess(true);
      } catch (err) {
        // Fail open or log error quietly so development continues gracefully
        console.warn("FeatureGate evaluation fallback:", err);
        setHasAccess(true);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    evaluateAccess();
    return () => {
      isMounted = false;
    };
  }, [featureKey, metricKey, workspaceId]);

  const handleQuickUpgrade = async (targetTier: PlanTier) => {
    try {
      setUpgrading(true);
      const targetWs = workspaceId || "default";
      await changeWorkspacePlan(targetWs, targetTier, "Upgraded via FeatureGate modal");
      setCurrentPlan(targetTier);
      setHasAccess(true);
      setIsUpgradeModalOpen(false);
    } catch (err: any) {
      alert(`Upgrade failed: ${err?.message || "Unknown error"}`);
    } finally {
      setUpgrading(false);
    }
  };

  if (loading) {
    return <>{children}</>;
  }

  if (hasAccess) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  if (!showUpgradeBanner) {
    return null;
  }

  return (
    <div className="feature-gate-container">
      <div className="feature-gate-card">
        <div className="feature-gate-icon">
          <Sparkles size={24} className="sparkle-icon" />
        </div>
        <div className="feature-gate-content">
          <h4 className="feature-gate-title">Premium Feature Locked</h4>
          <p className="feature-gate-description">
            {reason || `Unlock advanced capabilities with a Pro or Team workspace subscription.`}
          </p>
          <div className="feature-gate-actions">
            <button
              className="btn-upgrade-primary"
              onClick={() => setIsUpgradeModalOpen(true)}
            >
              <span>Upgrade Plan</span>
              <ArrowUpRight size={16} />
            </button>
            <a href="/settings/usage" className="btn-view-usage">
              View Usage Studio
            </a>
          </div>
        </div>
      </div>

      {isUpgradeModalOpen && (
        <div className="upgrade-modal-backdrop" onClick={() => setIsUpgradeModalOpen(false)}>
          <div className="upgrade-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="upgrade-modal-header">
              <div className="modal-title-wrap">
                <Sparkles size={20} className="text-primary" />
                <h3>Upgrade Workspace Tier</h3>
              </div>
              <button
                className="btn-close-modal"
                onClick={() => setIsUpgradeModalOpen(false)}
              >
                <X size={18} />
              </button>
            </div>
            <p className="modal-subtitle">
              Instant activation. Your analytical data and models are permanently preserved.
            </p>

            <div className="tiers-grid">
              <div className={`tier-card ${currentPlan === "PRO" ? "active-tier" : ""}`}>
                <div className="tier-header">
                  <span className="tier-badge">PRO</span>
                  <h4>Professional</h4>
                  <p className="tier-desc">Ideal for individual power researchers & data analysts.</p>
                </div>
                <ul className="tier-features">
                  <li><CheckCircle2 size={14} /> 1,000 AI Analyst Queries / mo</li>
                  <li><CheckCircle2 size={14} /> 20 GB Storage Capacity</li>
                  <li><CheckCircle2 size={14} /> 200 ML Experiments & Forecasts</li>
                  <li><CheckCircle2 size={14} /> Unlimited SQL Analytics</li>
                </ul>
                <button
                  className="btn-tier-select"
                  disabled={upgrading || currentPlan === "PRO"}
                  onClick={() => handleQuickUpgrade("PRO")}
                >
                  {currentPlan === "PRO" ? "Current Plan" : upgrading ? "Upgrading..." : "Switch to Pro"}
                </button>
              </div>

              <div className={`tier-card highlight-tier ${currentPlan === "TEAM" ? "active-tier" : ""}`}>
                <div className="tier-header">
                  <span className="tier-badge popular">TEAM</span>
                  <h4>Team Collaboration</h4>
                  <p className="tier-desc">Multi-user analytics with shared lineage and notebooks.</p>
                </div>
                <ul className="tier-features">
                  <li><CheckCircle2 size={14} /> 5,000 AI Analyst Queries / mo</li>
                  <li><CheckCircle2 size={14} /> 100 GB High-Throughput Storage</li>
                  <li><CheckCircle2 size={14} /> 1,000 ML Experiments / mo</li>
                  <li><CheckCircle2 size={14} /> 25 Team Workspace Members</li>
                </ul>
                <button
                  className="btn-tier-select btn-primary"
                  disabled={upgrading || currentPlan === "TEAM"}
                  onClick={() => handleQuickUpgrade("TEAM")}
                >
                  {currentPlan === "TEAM" ? "Current Plan" : upgrading ? "Upgrading..." : "Switch to Team"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .feature-gate-container {
          padding: 1.5rem;
          width: 100%;
        }
        .feature-gate-card {
          display: flex;
          align-items: flex-start;
          gap: 1.25rem;
          padding: 1.5rem;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(168, 85, 247, 0.04) 100%);
          border: 1px solid rgba(99, 102, 241, 0.25);
          border-radius: 12px;
          backdrop-filter: blur(8px);
        }
        .feature-gate-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background: rgba(99, 102, 241, 0.15);
          color: #818cf8;
          flex-shrink: 0;
        }
        .feature-gate-content {
          flex: 1;
        }
        .feature-gate-title {
          font-size: 1rem;
          font-weight: 600;
          color: #f8fafc;
          margin: 0 0 0.35rem 0;
        }
        .feature-gate-description {
          font-size: 0.875rem;
          color: #94a3b8;
          margin: 0 0 1rem 0;
          line-height: 1.5;
        }
        .feature-gate-actions {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .btn-upgrade-primary {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.55rem 1.1rem;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          color: #ffffff;
          border: none;
          border-radius: 8px;
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s, transform 0.15s;
        }
        .btn-upgrade-primary:hover {
          opacity: 0.92;
          transform: translateY(-1px);
        }
        .btn-view-usage {
          padding: 0.55rem 1rem;
          color: #cbd5e1;
          font-size: 0.85rem;
          text-decoration: none;
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 8px;
          transition: background 0.15s;
        }
        .btn-view-usage:hover {
          background: rgba(255, 255, 255, 0.05);
          color: #ffffff;
        }

        /* Upgrade Modal */
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
          max-width: 680px;
          padding: 1.75rem;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .upgrade-modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }
        .modal-title-wrap {
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }
        .modal-title-wrap h3 {
          margin: 0;
          font-size: 1.25rem;
          color: #f8fafc;
        }
        .btn-close-modal {
          background: transparent;
          border: none;
          color: #64748b;
          cursor: pointer;
        }
        .btn-close-modal:hover {
          color: #f8fafc;
        }
        .modal-subtitle {
          font-size: 0.875rem;
          color: #94a3b8;
          margin: 0 0 1.5rem 0;
        }
        .tiers-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.25rem;
        }
        .tier-card {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
        }
        .tier-card.highlight-tier {
          border-color: rgba(99, 102, 241, 0.4);
          background: rgba(30, 41, 59, 0.85);
        }
        .tier-header h4 {
          margin: 0.4rem 0 0.25rem 0;
          font-size: 1.1rem;
          color: #f8fafc;
        }
        .tier-badge {
          display: inline-block;
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 0.05em;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          background: rgba(148, 163, 184, 0.15);
          color: #cbd5e1;
        }
        .tier-badge.popular {
          background: rgba(99, 102, 241, 0.2);
          color: #818cf8;
        }
        .tier-desc {
          font-size: 0.8rem;
          color: #94a3b8;
          margin: 0 0 1rem 0;
        }
        .tier-features {
          list-style: none;
          padding: 0;
          margin: 0 0 1.25rem 0;
          flex: 1;
        }
        .tier-features li {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.8rem;
          color: #cbd5e1;
          margin-bottom: 0.5rem;
        }
        .btn-tier-select {
          padding: 0.6rem;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.15);
          background: rgba(255, 255, 255, 0.05);
          color: #ffffff;
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
        }
        .btn-tier-select.btn-primary {
          background: #6366f1;
          border-color: #6366f1;
        }
        .btn-tier-select:hover:not(:disabled) {
          opacity: 0.9;
        }
        .btn-tier-select:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};
