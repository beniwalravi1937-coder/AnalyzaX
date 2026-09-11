import { createFileRoute } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "../components/layout/PageHeader";
import { notificationApi } from "../services/notificationApi";
import {
  Notification,
  NotificationCategory,
  NotificationPriority,
  NotificationStatus,
} from "../types/notifications";
import {
  Bell,
  Check,
  CheckCheck,
  Search,
  Settings,
  Trash2,
  ExternalLink,
  Filter,
  RefreshCw,
  Inbox,
  ShieldAlert,
  Layers,
  Database,
  BarChart2,
  FileText,
  Share2,
  Users,
  Archive,
  AlertTriangle,
  Info,
} from "lucide-react";

export const Route = createFileRoute("/notifications")({
  head: () => ({
    meta: [
      { title: "Notification Center — AnalyzaX" },
      {
        name: "description",
        content:
          "Unified enterprise communications, collaboration alerts, and analytical job milestones.",
      },
    ],
  }),
  component: NotificationsPage,
});

function getCategoryIcon(cat: NotificationCategory) {
  switch (cat) {
    case NotificationCategory.SECURITY:
      return <ShieldAlert className="w-4 h-4 text-rose-400" />;
    case NotificationCategory.COLLABORATION:
      return <Share2 className="w-4 h-4 text-cyan-400" />;
    case NotificationCategory.PROJECT:
      return <Users className="w-4 h-4 text-blue-400" />;
    case NotificationCategory.DATA:
      return <Database className="w-4 h-4 text-emerald-400" />;
    case NotificationCategory.ANALYSIS:
      return <BarChart2 className="w-4 h-4 text-indigo-400" />;
    case NotificationCategory.EXPORT:
    case NotificationCategory.REPORT:
      return <FileText className="w-4 h-4 text-amber-400" />;
    case NotificationCategory.SYSTEM:
    default:
      return <Info className="w-4 h-4 text-slate-400" />;
  }
}

function getPriorityBadge(priority: NotificationPriority) {
  switch (priority) {
    case NotificationPriority.CRITICAL:
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
          <AlertTriangle className="w-2.5 h-2.5" />
          CRITICAL
        </span>
      );
    case NotificationPriority.HIGH:
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
          HIGH
        </span>
      );
    case NotificationPriority.NORMAL:
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-500/15 text-slate-300 border border-slate-500/20">
          NORMAL
        </span>
      );
    case NotificationPriority.LOW:
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-500/10 text-slate-400">
          LOW
        </span>
      );
  }
}

function formatTimestamp(isoString: string): string {
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

function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [activeTab, setActiveTab] = useState<"ALL" | "UNREAD" | "ARCHIVED">("ALL");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState<boolean>(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const loadNotifications = useCallback(
    async (cursor?: string, append = false) => {
      if (!append) setIsLoading(true);
      setError(null);

      try {
        let statusParam: NotificationStatus | undefined = undefined;
        let unreadOnly = false;
        if (activeTab === "UNREAD") {
          unreadOnly = true;
          statusParam = NotificationStatus.UNREAD;
        } else if (activeTab === "ARCHIVED") {
          statusParam = NotificationStatus.ARCHIVED;
        }

        const categoryParam =
          selectedCategory !== "ALL" ? (selectedCategory as NotificationCategory) : undefined;

        const [res, unread] = await Promise.all([
          notificationApi.listNotifications({
            category: categoryParam,
            status: statusParam,
            unread_only: unreadOnly,
            search: debouncedSearch || undefined,
            limit: 30,
            cursor,
          }),
          notificationApi.getUnreadCount(),
        ]);

        setNotifications((prev) => (append ? [...prev, ...res.items] : res.items));
        setTotalCount(res.total || res.total_count || res.items.length);
        setUnreadCount(unread);
        setNextCursor(res.next_cursor || null);
        setHasMore(res.has_more);
      } catch (err: any) {
        setError(err.message || "Failed to load notifications.");
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [activeTab, selectedCategory, debouncedSearch]
  );

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadNotifications();
  };

  const handleMarkAsRead = async (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      const updated = await notificationApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? updated : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleMarkAsUnread = async (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      const updated = await notificationApi.markAsUnread(id);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? updated : n))
      );
      setUnreadCount((c) => c + 1);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleArchive = async (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      const updated = await notificationApi.archiveNotification(id);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? updated : n))
      );
      if (activeTab !== "ARCHIVED") {
        setNotifications((prev) => prev.filter((n) => n.notification_id !== id));
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllAsRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, status: NotificationStatus.READ, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
    } catch (err: any) {
      alert(err.message || "Failed to mark all as read.");
    }
  };

  const handleCleanup = async () => {
    if (!confirm("Run retention cleanup to remove expired and surplus notifications?")) return;
    try {
      const res = await notificationApi.runCleanup();
      alert(`Cleaned up ${res.cleaned_count} expired/surplus notification(s).`);
      await loadNotifications();
    } catch (err: any) {
      alert(err.message || "Cleanup failed.");
    }
  };

  const handleNavigate = (n: Notification) => {
    if (n.status === NotificationStatus.UNREAD) {
      handleMarkAsRead(n.notification_id);
    }
    if (n.deep_link) {
      router.push(n.deep_link);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notification Center"
        description="Unified enterprise communications, collaboration alerts, and analytical job milestones."
        badge={
          unreadCount > 0
            ? { text: `${unreadCount} unread`, variant: "amber" }
            : { text: "All caught up", variant: "emerald" }
        }
        actions={
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="btn btn-secondary btn-sm flex items-center gap-1.5"
              >
                <CheckCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Mark All as Read</span>
              </button>
            )}

            <button
              type="button"
              onClick={handleCleanup}
              className="btn btn-secondary btn-sm flex items-center gap-1.5"
              title="Clean up expired notifications"
            >
              <Trash2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Retention Cleanup</span>
            </button>

            <Link
              href="/settings"
              className="btn btn-secondary btn-sm flex items-center gap-1.5"
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Preferences</span>
            </Link>

            <button
              type="button"
              onClick={handleRefresh}
              disabled={isRefreshing || isLoading}
              className="btn btn-secondary btn-sm p-2"
              title="Refresh"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            </button>
          </div>
        }
      />

      <div className="bg-surface-elevated border border-border rounded-xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-1 bg-surface p-1 rounded-lg border border-border w-fit text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab("ALL")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "ALL"
                ? "bg-brand text-white font-semibold shadow-xs"
                : "text-foreground-muted hover:text-foreground"
            }`}
          >
            All
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("UNREAD")}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === "UNREAD"
                ? "bg-brand text-white font-semibold shadow-xs"
                : "text-foreground-muted hover:text-foreground"
            }`}
          >
            <span>Unread</span>
            {unreadCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("ARCHIVED")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "ARCHIVED"
                ? "bg-brand text-white font-semibold shadow-xs"
                : "text-foreground-muted hover:text-foreground"
            }`}
          >
            Archived
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1 bg-surface border border-border rounded-lg px-2.5 py-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-foreground-muted" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-transparent text-foreground text-xs focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Categories</option>
              <option value={NotificationCategory.COLLABORATION}>Collaboration</option>
              <option value={NotificationCategory.PROJECT}>Projects</option>
              <option value={NotificationCategory.DATA}>Data & Datasets</option>
              <option value={NotificationCategory.ANALYSIS}>Analysis & ML</option>
              <option value={NotificationCategory.EXPORT}>Exports</option>
              <option value={NotificationCategory.REPORT}>Reports</option>
              <option value={NotificationCategory.SECURITY}>Security</option>
              <option value={NotificationCategory.SYSTEM}>System</option>
            </select>
          </div>

          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-foreground-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search notifications..."
              className="w-full bg-surface border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-foreground-muted focus:outline-none focus:border-brand transition-colors"
            />
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {isLoading && notifications.length === 0 ? (
          <div className="py-16 text-center text-foreground-muted text-xs flex flex-col items-center gap-2 bg-surface-elevated border border-border rounded-xl">
            <RefreshCw className="w-6 h-6 animate-spin text-brand" />
            <span>Loading notifications...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs text-center">
            {error}
          </div>
        ) : notifications.length === 0 ? (
          <div className="py-16 text-center text-foreground-muted text-xs flex flex-col items-center gap-3 bg-surface-elevated border border-border rounded-xl">
            <Inbox className="w-10 h-10 text-foreground-muted/30" />
            <div className="space-y-1">
              <p className="font-semibold text-foreground text-sm">No notifications found</p>
              <p className="text-foreground-muted">
                {activeTab === "UNREAD"
                  ? "You have zero unread notifications. All caught up!"
                  : "No notifications match your current filter criteria."}
              </p>
            </div>
          </div>
        ) : (
          notifications.map((n) => {
            const isUnread = n.status === NotificationStatus.UNREAD;
            const isCritical = n.priority === NotificationPriority.CRITICAL;

            return (
              <div
                key={n.notification_id}
                onClick={() => handleNavigate(n)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  isUnread
                    ? isCritical
                      ? "bg-rose-500/5 border-rose-500/30 hover:border-rose-500/50 shadow-xs"
                      : "bg-surface-elevated border-brand/40 hover:border-brand shadow-xs"
                    : "bg-surface/50 border-border hover:bg-surface-elevated/70"
                }`}
              >
                <div className="flex items-start gap-3.5">
                  <div
                    className={`p-2.5 rounded-lg shrink-0 ${
                      isCritical
                        ? "bg-rose-500/10 border border-rose-500/20"
                        : "bg-surface border border-border"
                    }`}
                  >
                    {getCategoryIcon(n.category)}
                  </div>

                  <div className="space-y-1 text-xs">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-foreground text-sm">
                        {n.title}
                      </span>
                      {isUnread && (
                        <span className="w-2 h-2 rounded-full bg-brand shrink-0" />
                      )}
                      {getPriorityBadge(n.priority)}
                      <span className="px-1.5 py-0.2 rounded bg-surface border border-border text-[10px] uppercase font-mono text-foreground-muted">
                        {n.category}
                      </span>
                    </div>

                    <p className="text-foreground-muted leading-relaxed max-w-3xl">
                      {n.message}
                    </p>

                    <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-foreground-muted/70">
                      <span>{formatTimestamp(n.created_at)}</span>

                      {n.resource_type && n.resource_id && (
                        <span className="flex items-center gap-1 font-mono text-[10px] text-foreground-muted">
                          <Layers className="w-3 h-3 text-indigo-400" />
                          {n.resource_type}: {n.resource_id.substring(0, 12)}...
                        </span>
                      )}

                      {n.read_at && (
                        <span className="text-emerald-500/80 flex items-center gap-0.5">
                          <Check className="w-3 h-3" /> Read
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                  {n.deep_link && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNavigate(n);
                      }}
                      className="px-2.5 py-1.5 rounded-lg border border-border bg-surface hover:bg-surface-elevated text-indigo-400 hover:text-indigo-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
                      title="Open target resource"
                    >
                      <span>Open</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  )}

                  {isUnread ? (
                    <button
                      type="button"
                      onClick={(e) => handleMarkAsRead(n.notification_id, e)}
                      className="p-1.5 rounded-lg border border-border text-foreground-muted hover:text-foreground hover:bg-surface transition-colors"
                      title="Mark as read"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={(e) => handleMarkAsUnread(n.notification_id, e)}
                      className="p-1.5 rounded-lg border border-border text-foreground-muted hover:text-foreground hover:bg-surface transition-colors"
                      title="Mark as unread"
                    >
                      <Bell className="w-3.5 h-3.5" />
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={(e) => handleArchive(n.notification_id, e)}
                    className="p-1.5 rounded-lg border border-border text-foreground-muted hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                    title="Archive notification"
                  >
                    <Archive className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}

        {hasMore && (
          <div className="pt-4 text-center">
            <button
              type="button"
              onClick={() => nextCursor && loadNotifications(nextCursor, true)}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl border border-border bg-surface-elevated hover:bg-surface text-foreground text-xs font-medium transition-colors shadow-xs"
            >
              {isLoading ? "Loading older notifications..." : "Load More Notifications"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
