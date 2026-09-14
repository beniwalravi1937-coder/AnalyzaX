"use client";

import React from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import {
  DashboardIcon,
  DatasetIcon,
  DataQualityIcon,
  CleanIcon,
  EDAIcon,
  SQLIcon,
  BarChartIcon,
  StatisticsIcon,
  MLIcon,
  ForecastingIcon,
  AIAnalystIcon,
  ExportsIcon,
  SettingsIcon,
  HelpIcon,
  CloseIcon,
} from "@/components/icons";
import { Folder, Sparkles, Calculator } from "lucide-react";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  { label: "Projects", href: "/projects", icon: Folder },
  { label: "Dashboard", href: "/dashboard", icon: DashboardIcon },
  { label: "Insights", href: "/insights", icon: Sparkles },
  { label: "Metrics", href: "/metrics", icon: Calculator },
  { label: "Dataset", href: "/dataset", icon: DatasetIcon },
  { label: "Data Quality", href: "/data-quality", icon: DataQualityIcon },
  { label: "Clean & Transform", href: "/cleaning", icon: CleanIcon },
  { label: "EDA", href: "/eda", icon: EDAIcon },
  { label: "SQL", href: "/sql", icon: SQLIcon },
  { label: "Visualizations", href: "/visualizations", icon: BarChartIcon },
  { label: "Statistics", href: "/statistics", icon: StatisticsIcon },
  { label: "Machine Learning", href: "/ml", icon: MLIcon },
  { label: "Forecasting", href: "/forecasting", icon: ForecastingIcon },
  { label: "AI Analyst", href: "/ai-analyst", icon: AIAnalystIcon },
  { label: "Exports", href: "/exports", icon: ExportsIcon },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside className={`sidebar ${isOpen ? "open" : ""}`}>
        {/* Header / Brand */}
        <div className="sidebar-header">
          <Link
            to="/dashboard"
            onClick={onClose}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.65rem",
              textDecoration: "none",
            }}
          >
            <img
              src="/logo.png"
              alt="AnalyzaX Logo"
              width={30}
              height={30}
              style={{
                objectFit: "contain",
                filter: "drop-shadow(0 2px 8px rgba(59, 130, 246, 0.45))",
              }}
            />
            <span
              style={{
                fontSize: "1.125rem",
                fontWeight: 700,
                color: "#ffffff",
                letterSpacing: "-0.02em",
              }}
            >
              Analyza<span style={{ background: "linear-gradient(135deg, #60a5fa 0%, #a855f7 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>X</span>
            </span>
          </Link>

          {/* Close button on mobile */}
          <button
            onClick={onClose}
            className="btn btn-secondary btn-sm"
            style={{ display: "none", padding: "0.25rem" }}
            aria-label="Close sidebar"
            id="mobile-close-sidebar"
          >
            <CloseIcon size={16} />
          </button>
        </div>

        {/* Navigation Section */}
        <nav className="sidebar-nav" aria-label="Main Navigation">
          <span className="nav-section-title">Analytics Workspace</span>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");

            return (
              <Link
                key={item.href}
                to={item.href}
                onClick={onClose}
                className={`nav-item ${isActive ? "active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom / Settings & Help */}
        <div className="sidebar-footer">
          <Link
            to="/settings"
            onClick={onClose}
            className={`nav-item ${pathname === "/settings" ? "active" : ""}`}
          >
            <SettingsIcon size={18} />
            <span>Settings</span>
          </Link>

          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-item"
            style={{ color: "var(--text-muted)" }}
          >
            <HelpIcon size={18} />
            <span>Documentation & Help</span>
          </a>

          <div
            style={{
              padding: "0.5rem 0.75rem",
              fontSize: "0.6875rem",
              color: "var(--text-faint)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>AnalyzaX Platform</span>
            <span>v0.1.0</span>
          </div>
        </div>
      </aside>
    </>
  );
}
