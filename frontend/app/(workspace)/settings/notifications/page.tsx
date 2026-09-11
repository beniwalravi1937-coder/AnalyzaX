"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { SettingsNav } from "@/components/settings/SettingsNav";
import { notificationApi } from "@/services/notificationApi";
import {
  NotificationCategory,
  NotificationChannel,
  NotificationPreference,
} from "@/types/notifications";
import {
  Bell,
  ShieldCheck,
  Lock,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Share2,
  Users,
  Database,
  BarChart2,
  FileText,
  Layers,
  Info,
  Mail,
  Smartphone,
} from "lucide-react";

interface CategoryMeta {
  category: NotificationCategory;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  isSecurity?: boolean;
}

const CATEGORIES: CategoryMeta[] = [
  {
    category: NotificationCategory.SECURITY,
    name: "Security & Account Safety",
    description: "Critical security notices, login alerts, session revocations, and password modifications.",
    icon: ShieldCheck,
    isSecurity: true,
  },
  {
    category: NotificationCategory.COLLABORATION,
    name: "Sharing & Collaboration",
    description: "Direct asset shares, shared link creation, workspace invitations, and team permissions.",
    icon: Share2,
  },
  {
    category: NotificationCategory.PROJECT,
    name: "Project Milestones",
    description: "Project creations, member additions, role changes, and project archival events.",
    icon: Users,
  },
  {
    category: NotificationCategory.DATA,
    name: "Datasets & Lineage",
    description: "Dataset uploads, transformation versions, data quality alerts, and cleaning completions.",
    icon: Database,
  },
  {
    category: NotificationCategory.ANALYSIS,
    name: "Analytics & ML Models",
    description: "Automated profiling finishes, ML model training runs, and time-series forecast completions.",
    icon: BarChart2,
  },
  {
    category: NotificationCategory.EXPORT,
    name: "Exports & Downloads",
    description: "Completed dataset downloads, parquet bundles, chart exports, and notebook generations.",
    icon: FileText,
  },
  {
    category: NotificationCategory.REPORT,
    name: "Reports & Summaries",
    description: "Automated executive report generation, PDF exports, and executive dashboard builds.",
    icon: Layers,
  },
  {
    category: NotificationCategory.SYSTEM,
    name: "System Announcements",
    description: "Platform maintenance windows, scheduled engine upgrades, and system advisory notices.",
    icon: Info,
  },
];

export default function NotificationPreferencesPage() {
  const [preferences, setPreferences] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    setIsLoading(true);
    try {
      const list = await notificationApi.getPreferences();
      const map: Record<string, boolean> = {};
      list.forEach((p) => {
        map[p.category] = p.enabled;
      });
      setPreferences(map);
    } catch (err: any) {
      setNotice({
        type: "error",
        text: err.message || "Failed to load notification preferences.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (catMeta: CategoryMeta) => {
    if (catMeta.isSecurity) {
      setNotice({
        type: "error",
        text: "Security-critical notifications cannot be disabled and are mandatory for account safety.",
      });
      return;
    }

    const currentVal = preferences[catMeta.category] ?? true;
    const nextVal = !currentVal;

    // Optimistic update
    setPreferences((prev) => ({ ...prev, [catMeta.category]: nextVal }));
    setIsSaving(catMeta.category);
    setNotice(null);

    try {
      await notificationApi.updatePreference({
        category: catMeta.category,
        channel: NotificationChannel.IN_APP,
        enabled: nextVal,
      });
      setNotice({
        type: "success",
        text: `Updated preference for "${catMeta.name}".`,
      });
    } catch (err: any) {
      // Rollback
      setPreferences((prev) => ({ ...prev, [catMeta.category]: currentVal }));
      setNotice({
        type: "error",
        text: err.message || "Failed to update preference.",
      });
    } finally {
      setIsSaving(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Notification Preferences"
        description="Fine-tune your communication subscriptions, active delivery channels, and milestone notices."
        badge={{ text: "Real-time sync", variant: "emerald" }}
      />

      <SettingsNav />

      {/* Security Mandatory Notice Banner */}
      <div className="mb-6 p-4 rounded-xl border border-indigo-500/20 bg-indigo-500/5 flex items-start gap-3.5 text-xs text-indigo-300/90 leading-relaxed">
        <Lock className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-white block mb-0.5">
            Security Guarantees & Non-Suppressible Alerts
          </span>
          To protect enterprise data and detect suspicious activity, security-critical notices
          (password modifications, multi-factor changes, credential revocations, and unauthorized
          access attempts) are mandatory and cannot be disabled.
        </div>
      </div>

      {notice && (
        <div
          className={`mb-6 p-3.5 rounded-xl border text-xs flex items-center justify-between gap-3 ${
            notice.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : "bg-rose-500/10 border-rose-500/20 text-rose-400"
          }`}
        >
          <div className="flex items-center gap-2">
            {notice.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{notice.text}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotice(null)}
            className="text-[11px] hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* In-App Delivery Channel Preferences */}
      <SectionCard
        title="In-App Notification Categories"
        subtitle="Manage which system and collaboration events appear in your notification feed and unread badge"
      >
        {isLoading ? (
          <div className="py-10 text-center text-foreground-muted text-xs flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-brand" />
            <span>Loading preferences...</span>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              const isEnabled = cat.isSecurity ? true : preferences[cat.category] ?? true;
              const isSavingThis = isSaving === cat.category;

              return (
                <div
                  key={cat.category}
                  className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 first:pt-0 last:pb-0"
                >
                  <div className="flex items-start gap-3.5">
                    <div className="p-2 rounded-lg bg-surface border border-border shrink-0 mt-0.5">
                      <Icon className="w-4 h-4 text-brand" />
                    </div>

                    <div className="space-y-0.5 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground text-sm">
                          {cat.name}
                        </span>
                        {cat.isSecurity && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/25">
                            <Lock className="w-2.5 h-2.5" />
                            MANDATORY
                          </span>
                        )}
                      </div>
                      <p className="text-foreground-muted max-w-xl leading-relaxed">
                        {cat.description}
                      </p>
                    </div>
                  </div>

                  {/* Toggle */}
                  <div className="flex items-center gap-3 self-end sm:self-center">
                    {isSavingThis && (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-brand" />
                    )}

                    <button
                      type="button"
                      disabled={cat.isSecurity || isSavingThis}
                      onClick={() => handleToggle(cat)}
                      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        cat.isSecurity
                          ? "bg-indigo-600/70 opacity-80 cursor-not-allowed"
                          : isEnabled
                          ? "bg-brand"
                          : "bg-surface-muted"
                      }`}
                      aria-pressed={isEnabled}
                      title={
                        cat.isSecurity
                          ? "Security notifications cannot be disabled"
                          : isEnabled
                          ? "Click to disable"
                          : "Click to enable"
                      }
                    >
                      <span
                        aria-hidden="true"
                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                          isEnabled ? "translate-x-5" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </SectionCard>

      {/* Multi-Channel Enterprise Delivery (Roadmap) */}
      <div className="mt-6">
        <SectionCard
          title="Additional Delivery Channels (Enterprise Hybrid)"
          subtitle="Support for external delivery channels architected in NotificationChannel"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-border bg-surface/40 flex items-start gap-3 text-xs">
              <div className="p-2 rounded-lg bg-surface border border-border text-foreground-muted">
                <Mail className="w-4 h-4" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">Email Notifications</span>
                  <span className="px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px]">
                    Phase 20+
                  </span>
                </div>
                <p className="text-foreground-muted">
                  Digest emails and instant dispatch for high-priority security alerts and team invitations.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface/40 flex items-start gap-3 text-xs">
              <div className="p-2 rounded-lg bg-surface border border-border text-foreground-muted">
                <Smartphone className="w-4 h-4" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">Mobile & Web Push</span>
                  <span className="px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px]">
                    Phase 20+
                  </span>
                </div>
                <p className="text-foreground-muted">
                  Browser push notifications for long-running batch job completions and dataset imports.
                </p>
              </div>
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
