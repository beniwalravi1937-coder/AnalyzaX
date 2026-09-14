"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useBackendHealth } from "@/hooks/useBackendHealth";
import { useDataset } from "@/context/DatasetContext";
import { useAuth } from "@/context/AuthContext";
import { MenuIcon, UploadIcon, RefreshIcon } from "@/components/icons";
import { ProjectSwitcher } from "@/components/workspace/ProjectSwitcher";
import { GlobalSearchModal } from "@/components/workspace/GlobalSearchModal";
import { Search } from "lucide-react";

import { NotificationCenter } from "@/components/collaboration/NotificationCenter";

interface TopBarProps {
  onToggleSidebar: () => void;
  datasetName?: string | null;
}

export function TopBar({ onToggleSidebar, datasetName = null }: TopBarProps) {
  const { user, currentRole, logout } = useAuth();
  const { connection, health, refetch } = useBackendHealth();
  const { activeDataset } = useDataset();
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const currentDatasetName = activeDataset?.original_filename || activeDataset?.name || datasetName;

  const isConnected = connection === "connected";
  const isConnecting = connection === "connecting";

  // Ctrl+K / Cmd+K global shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <header className="topbar">
        {/* Left: Mobile hamburger & Project Switcher & Dataset Context */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button
            type="button"
            onClick={onToggleSidebar}
            className="btn btn-secondary btn-sm"
            style={{ padding: "0.4rem", display: "inline-flex" }}
            aria-label="Toggle Navigation Menu"
          >
            <MenuIcon size={18} />
          </button>

          {/* Project Switcher */}
          <ProjectSwitcher />

          {/* Search Trigger Button */}
          <button
            type="button"
            onClick={() => setIsSearchOpen(true)}
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-700/60 bg-slate-900/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs transition-colors"
            title="Search Assets (Ctrl+K)"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Search assets...</span>
            <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono">
              Ctrl+K
            </kbd>
          </button>

          {/* Dataset Context Indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Dataset:
            </span>

            {currentDatasetName ? (
              <span className="badge badge-emerald" title="Active analytical dataset">
                {currentDatasetName}
              </span>
            ) : (
              <span className="badge badge-neutral">No dataset selected</span>
            )}

            <Link
              href="/dataset"
              className="btn btn-secondary btn-sm"
              style={{
                fontSize: "0.75rem",
                padding: "0.2rem 0.6rem",
                gap: "0.35rem",
              }}
            >
              <UploadIcon size={13} />
              <span>Connect</span>
            </Link>
          </div>
        </div>

      {/* Right: Actions & System Status */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
        {/* Live Backend Connection Indicator */}
        <div
          title={`Backend API: ${connection} | DuckDB: ${health?.duckdb ?? "unknown"}`}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.45rem",
            padding: "0.3rem 0.65rem",
            backgroundColor: "rgba(255, 255, 255, 0.03)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "9999px",
            fontSize: "0.75rem",
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              backgroundColor: isConnected ? "var(--accent-emerald)" : isConnecting ? "var(--accent-amber)" : "var(--accent-rose)",
              boxShadow: isConnected ? "0 0 6px rgba(16, 185, 129, 0.8)" : "none",
            }}
          />
          <span style={{ color: "var(--text-secondary)", fontWeight: 500 }}>
            {isConnecting ? "Connecting" : isConnected ? "Core Online" : "Offline"}
          </span>
          <button
            onClick={() => refetch()}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "var(--text-muted)",
              display: "flex",
              alignItems: "center",
              padding: "0 2px",
            }}
            aria-label="Refresh Backend Health"
            title="Refresh Health"
          >
            <RefreshIcon size={12} />
          </button>
        </div>

        {/* User Profile & Role Indicator */}
        {user && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <NotificationCenter />
            <Link
              href="/settings/profile"
              title={`Signed in as ${user.display_name} (${user.email})`}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                textDecoration: "none",
                padding: "0.25rem 0.6rem",
                borderRadius: "9999px",
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div
                style={{
                  width: "24px",
                  height: "24px",
                  borderRadius: "50%",
                  background: "var(--primary-color, #6366f1)",
                  color: "#fff",
                  fontSize: "0.6875rem",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {user.display_name ? user.display_name[0].toUpperCase() : "U"}
              </div>
              <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)", fontWeight: 500 }}>
                {user.display_name}
              </span>
              {currentRole && (
                <span className="badge badge-indigo" style={{ fontSize: "0.6875rem", padding: "0.1rem 0.35rem" }}>
                  {currentRole}
                </span>
              )}
            </Link>

            <button
              type="button"
              onClick={() => logout()}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.3rem 0.65rem", color: "#ef4444" }}
              title="Sign out of AnalyzaX"
            >
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
    <GlobalSearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
  </>
  );
}


