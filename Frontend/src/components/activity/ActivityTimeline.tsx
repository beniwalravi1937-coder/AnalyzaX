"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { notificationApi } from "@/services/notificationApi";
import {
  ActivityFeedItem,
  ApplicationEventType,
} from "@/types/notifications";
import {
  Clock,
  User,
  Activity,
  Filter,
  RefreshCw,
  ExternalLink,
  Layers,
  Database,
  BarChart2,
  FileText,
  Share2,
  Users,
  Shield,
  Sparkles,
} from "lucide-react";

interface ActivityTimelineProps {
  projectId?: string;
  workspaceId?: string;
  title?: string;
  subtitle?: string;
  maxItems?: number;
}

function getEventIcon(action: string) {
  if (action.includes("DATASET")) return <Database className="w-4 h-4 text-emerald-400" />;
  if (action.includes("ANALYSIS") || action.includes("ML") || action.includes("FORECAST"))
    return <BarChart2 className="w-4 h-4 text-indigo-400" />;
  if (action.includes("EXPORT") || action.includes("REPORT"))
    return <FileText className="w-4 h-4 text-amber-400" />;
  if (action.includes("SHARE") || action.includes("LINK"))
    return <Share2 className="w-4 h-4 text-cyan-400" />;
  if (action.includes("MEMBER") || action.includes("INVITATION"))
    return <Users className="w-4 h-4 text-blue-400" />;
  if (action.includes("SECURITY") || action.includes("PASSWORD"))
    return <Shield className="w-4 h-4 text-rose-400" />;
  return <Activity className="w-4 h-4 text-slate-400" />;
}

function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSec < 60) return "just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;

    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

export function ActivityTimeline({
  projectId,
  workspaceId,
  title = "Collaborative Activity",
  subtitle = "Recent events and team milestones across this context",
  maxItems = 25,
}: ActivityTimelineProps) {
  const [items, setItems] = useState<ActivityFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchActivity = useCallback(
    async (cursor?: string, append = false) => {
      if (!projectId && !workspaceId) return;

      if (!append) setIsLoading(true);
      setError(null);

      try {
        const eventTypeParam =
          selectedType !== "ALL" ? (selectedType as ApplicationEventType) : undefined;

        let res;
        if (projectId) {
          res = await notificationApi.getProjectActivity(projectId, {
            limit: maxItems,
            cursor,
            eventType: eventTypeParam,
          });
        } else if (workspaceId) {
          res = await notificationApi.getWorkspaceActivity(workspaceId, {
            limit: maxItems,
            cursor,
            eventType: eventTypeParam,
          });
        }

        if (res) {
          setItems((prev) => (append ? [...prev, ...res.items] : res.items));
          setNextCursor(res.next_cursor || null);
          setHasMore(res.has_more);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load activity feed.");
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [projectId, workspaceId, selectedType, maxItems]
  );

  useEffect(() => {
    fetchActivity();
  }, [fetchActivity]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchActivity();
  };

  const handleLoadMore = async () => {
    if (nextCursor && !isLoading) {
      await fetchActivity(nextCursor, true);
    }
  };

  return (
    <div className="bg-surface-elevated border border-border rounded-xl p-5 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            <h3 className="font-semibold text-foreground text-sm tracking-tight">{title}</h3>
          </div>
          {subtitle && (
            <p className="text-xs text-foreground-muted mt-0.5">{subtitle}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Filter */}
          <div className="flex items-center gap-1.5 bg-surface border border-border rounded-lg px-2 py-1 text-xs">
            <Filter className="w-3.5 h-3.5 text-foreground-muted" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-transparent text-foreground text-xs focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Events</option>
              <option value="DATASET_CREATED">Dataset Uploads</option>
              <option value="DATASET_VERSION_CREATED">Dataset Transforms</option>
              <option value="ANALYSIS_COMPLETED">Analyses</option>
              <option value="ML_EXPERIMENT_COMPLETED">ML Models</option>
              <option value="EXPORT_COMPLETED">Exports</option>
              <option value="MEMBER_ADDED">Team Members</option>
              <option value="RESOURCE_SHARED">Shares</option>
            </select>
          </div>

          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing || isLoading}
            className="p-1.5 rounded-lg border border-border text-foreground-muted hover:text-foreground hover:bg-surface transition-colors"
            title="Refresh activity"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="mt-4">
        {isLoading && items.length === 0 ? (
          <div className="py-10 text-center text-foreground-muted text-xs flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
            <span>Loading collaborative activity...</span>
          </div>
        ) : error ? (
          <div className="py-6 text-center text-rose-400 text-xs bg-rose-500/10 rounded-lg border border-rose-500/20 p-3">
            {error}
          </div>
        ) : items.length === 0 ? (
          <div className="py-10 text-center text-foreground-muted text-xs flex flex-col items-center gap-2">
            <Clock className="w-6 h-6 text-foreground-muted/40" />
            <span>No activity recorded yet for this context.</span>
          </div>
        ) : (
          <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
            {items.map((item) => (
              <div key={item.activity_id} className="relative group">
                {/* Timeline node icon */}
                <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-surface-elevated border border-border flex items-center justify-center shadow-xs">
                  {getEventIcon(item.action)}
                </div>

                <div className="text-xs">
                  <div className="flex flex-wrap items-center gap-2 text-foreground-muted">
                    <span className="font-semibold text-foreground flex items-center gap-1">
                      <User className="w-3 h-3 text-indigo-400/80 inline" />
                      {item.actor_name}
                    </span>
                    <span className="text-foreground-muted/50">&bull;</span>
                    <span className="px-1.5 py-0.5 rounded bg-surface border border-border text-[10px] font-mono uppercase tracking-wider text-foreground-muted">
                      {item.action.replace(/_/g, " ")}
                    </span>
                    <span className="text-foreground-muted/50">&bull;</span>
                    <span className="text-[11px] text-foreground-muted/70">
                      {formatRelativeTime(item.timestamp)}
                    </span>
                  </div>

                  <p className="mt-1 text-foreground/90 font-normal leading-relaxed">
                    {item.description}
                  </p>

                  {/* Resource details or deep link */}
                  {(item.resource_name || item.deep_link) && (
                    <div className="mt-2 flex items-center gap-2">
                      {item.resource_name && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[11px]">
                          <Layers className="w-3 h-3" />
                          {item.resource_name}
                        </span>
                      )}

                      {item.deep_link && (
                        <Link
                          href={item.deep_link}
                          className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 hover:underline font-medium"
                        >
                          <span>Open Resource</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {hasMore && (
              <div className="pt-3 text-center">
                <button
                  type="button"
                  onClick={handleLoadMore}
                  disabled={isLoading}
                  className="px-3 py-1.5 rounded-lg border border-border bg-surface hover:bg-surface-elevated text-foreground text-xs font-medium transition-colors"
                >
                  {isLoading ? "Loading..." : "Load Older Activity"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
