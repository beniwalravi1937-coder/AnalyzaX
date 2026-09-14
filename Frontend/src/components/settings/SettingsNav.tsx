"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export const SettingsNav: React.FC = () => {
  const pathname = usePathname();
  const { currentRole } = useAuth();

  const tabs = [
    { label: "User Profile", href: "/settings/profile" },
    { label: "Usage & Plan", href: "/settings/usage" },
    { label: "Billing & Plans", href: "/settings/billing" },
    { label: "Notification Preferences", href: "/settings/notifications" },
    { label: "Security & Sessions", href: "/settings/security" },
    { label: "Workspace Members", href: "/settings/members" },
    { label: "System Diagnostics", href: "/settings" },
  ];

  return (
    <div className="settings-nav-tabs">
      {tabs.map((tab) => {
        const isActive = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`settings-nav-tab ${isActive ? "active" : ""}`}
          >
            {tab.label}
          </Link>
        );
      })}
      <style jsx>{`
        .settings-nav-tabs {
          display: flex;
          gap: 0.5rem;
          border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
          margin-bottom: 1.5rem;
          overflow-x: auto;
        }
        .settings-nav-tab {
          padding: 0.65rem 1.125rem;
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--text-muted, #94a3b8);
          text-decoration: none;
          border-bottom: 2px solid transparent;
          transition: all 0.15s;
          white-space: nowrap;
        }
        .settings-nav-tab:hover {
          color: var(--text-primary, #f8fafc);
        }
        .settings-nav-tab.active {
          color: var(--primary-color, #6366f1);
          border-bottom-color: var(--primary-color, #6366f1);
        }
      `}</style>
    </div>
  );
};
