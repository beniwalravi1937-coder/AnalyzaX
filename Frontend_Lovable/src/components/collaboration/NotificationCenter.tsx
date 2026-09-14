"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { notificationApi } from "@/services/notificationApi";
import { Notification, NotificationStatus, NotificationPriority } from "@/types/notifications";
import { Bell, Check, CheckCheck, Settings, ExternalLink, ShieldAlert } from "lucide-react";

export function NotificationCenter() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const count = await notificationApi.getUnreadCount();
      setUnreadCount(count);
    } catch {
      // ignore
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const [res, count] = await Promise.all([
        notificationApi.listNotifications({ limit: 10 }),
        notificationApi.getUnreadCount(),
      ]);
      setNotifications(res.items);
      setUnreadCount(count);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000); // Heartbeat count check every 30s
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, fetchNotifications]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllAsRead();
      setNotifications((prev) =>
        prev.map((n) => ({
          ...n,
          status: NotificationStatus.READ,
          read_at: new Date().toISOString(),
        }))
      );
      setUnreadCount(0);
    } catch {
      // ignore
    }
  };

  const handleItemClick = async (n: Notification) => {
    if (n.status === NotificationStatus.UNREAD) {
      try {
        await notificationApi.markAsRead(n.notification_id);
        setNotifications((prev) =>
          prev.map((item) =>
            item.notification_id === n.notification_id
              ? { ...item, status: NotificationStatus.READ, read_at: new Date().toISOString() }
              : item
          )
        );
        setUnreadCount((c) => Math.max(0, c - 1));
      } catch {
        // ignore
      }
    }

    if (n.deep_link) {
      setIsOpen(false);
      router.push(n.deep_link);
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="relative p-1.5 rounded-lg text-foreground-muted hover:text-foreground hover:bg-surface-muted transition-colors"
        title="Notifications"
        aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ""}`}
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-brand text-white text-[10px] font-bold rounded-full flex items-center justify-center shadow-xs animate-pulse">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-84 sm:w-96 bg-surface-elevated border border-border rounded-xl shadow-2xl z-50 overflow-hidden text-xs">
          {/* Popover Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface-muted/40">
            <div className="flex items-center gap-2">
              <span className="font-bold text-foreground text-sm">Notifications</span>
              {unreadCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full bg-brand/20 text-brand font-semibold text-[10px]">
                  {unreadCount} new
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllRead}
                  className="text-brand hover:underline font-medium text-[11px] flex items-center gap-1"
                >
                  <CheckCheck className="w-3 h-3" />
                  <span>Mark all read</span>
                </button>
              )}
              <Link
                href="/settings/notifications"
                onClick={() => setIsOpen(false)}
                className="text-foreground-muted hover:text-foreground p-1"
                title="Notification Preferences"
              >
                <Settings className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* List items */}
          <div className="max-h-88 overflow-y-auto divide-y divide-border">
            {isLoading && notifications.length === 0 ? (
              <div className="p-8 text-center text-foreground-muted text-xs">
                Loading notifications...
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-foreground-muted text-xs flex flex-col items-center gap-2">
                <Bell className="w-6 h-6 text-foreground-muted/40" />
                <span>All caught up! No notifications right now.</span>
              </div>
            ) : (
              notifications.map((n) => {
                const isUnread = n.status === NotificationStatus.UNREAD;
                const isCritical = n.priority === NotificationPriority.CRITICAL;

                return (
                  <div
                    key={n.notification_id}
                    onClick={() => handleItemClick(n)}
                    className={`p-3.5 transition-colors cursor-pointer hover:bg-surface flex items-start justify-between gap-3 ${
                      isUnread
                        ? isCritical
                          ? "bg-rose-500/5 hover:bg-rose-500/10 font-medium"
                          : "bg-brand/5 hover:bg-brand/10 font-medium"
                        : "text-foreground-muted hover:text-foreground"
                    }`}
                  >
                    <div className="space-y-1 flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {isCritical && (
                          <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        )}
                        <span className="font-semibold text-foreground truncate block">
                          {n.title}
                        </span>
                        {isUnread && (
                          <span className="w-2 h-2 rounded-full bg-brand shrink-0" />
                        )}
                      </div>

                      <p className="text-[11px] text-foreground-muted line-clamp-2 leading-relaxed">
                        {n.message}
                      </p>

                      <div className="flex items-center gap-2 pt-0.5 text-[10px] text-foreground-muted/70">
                        <span className="px-1.5 py-0.2 rounded bg-surface border border-border text-[9px] uppercase font-mono">
                          {n.category}
                        </span>
                        <span>
                          {new Date(n.created_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                        {n.deep_link && (
                          <span className="text-indigo-400 flex items-center gap-0.5 ml-auto">
                            <span>Open</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Popover Footer */}
          <div className="p-2.5 border-t border-border bg-surface-muted/30 text-center">
            <Link
              href="/notifications"
              onClick={() => setIsOpen(false)}
              className="text-brand hover:underline font-semibold text-xs block py-1"
            >
              View all in Notification Center &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
