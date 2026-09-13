import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import { PageHeader } from "../components/layout/PageHeader";
import { SectionCard } from "../components/ui/SectionCard";
import { useBackendHealth } from "../hooks/useBackendHealth";
import { RefreshIcon, CheckIcon, AlertCircleIcon } from "../components/icons";
import { SettingsNav } from "../components/settings/SettingsNav";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Workspace Settings — AnalyzaX" },
      {
        name: "description",
        content:
          "Manage your account preferences, system integrations, and workspace configuration options all in one place.",
      },
      { property: "og:title", content: "Workspace Settings — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Manage your account preferences, system integrations, and workspace configuration options.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { connection, health, lastChecked, refetch } = useBackendHealth();

  return (
    <div>
      <PageHeader
        title="Settings & System Diagnostics"
        description="Application environment configurations, backend engine health monitoring, and system properties."
        badge={{ text: "v0.1.0", variant: "neutral" }}
        actions={
          <button
            type="button"
            onClick={() => refetch()}
            className="btn btn-secondary btn-sm"
          >
            <RefreshIcon size={14} />
            <span>Check Connectivity</span>
          </button>
        }
      />

      <SettingsNav />

      {/* Backend Diagnostics Section */}
      <div style={{ marginBottom: "1.75rem" }}>
        <SectionCard
          title="Backend Infrastructure & Engines"
          subtitle="Real-time status of backend service layers and analytical engines"
        >
          <div className="table-wrapper">
            <table className="analyzax-table">
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Service Layer</th>
                  <th>Status</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>FastAPI Application</td>
                  <td style={{ color: "var(--text-muted)" }}>REST & WebSocket Layer</td>
                  <td>
                    <span className={`badge ${connection === "connected" ? "badge-emerald" : "badge-amber"}`}>
                      {connection === "connected" ? <CheckIcon size={10} /> : <AlertCircleIcon size={10} />}
                      {connection.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    http://127.0.0.1:8000
                  </td>
                </tr>

                <tr>
                  <td style={{ fontWeight: 600 }}>DuckDB Vectorized Engine</td>
                  <td style={{ color: "var(--text-muted)" }}>In-Memory OLAP Studio</td>
                  <td>
                    <span className={`badge ${health?.duckdb === "available" ? "badge-emerald" : "badge-amber"}`}>
                      {health?.duckdb === "available" ? <CheckIcon size={10} /> : <AlertCircleIcon size={10} />}
                      {(health?.duckdb ?? "Unknown").toUpperCase()}
                    </span>
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    Version: {health?.duckdb_version ?? "v1.5.5"}
                  </td>
                </tr>

                <tr>
                  <td style={{ fontWeight: 600 }}>PostgreSQL Metadata Store</td>
                  <td style={{ color: "var(--text-muted)" }}>Async SQLAlchemy Lineage</td>
                  <td>
                    <span className="badge badge-neutral">
                      {(health?.database ?? "Configured").toUpperCase()}
                    </span>
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    Metadata persistence & project catalogs
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {lastChecked && (
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.75rem" }}>
              Last health heartbeat check: {lastChecked.toLocaleTimeString()}
            </p>
          )}
        </SectionCard>
      </div>

      {/* Platform Information */}
      <SectionCard
        title="Development Constitution & Governance"
        subtitle="AnalyzaX architectural guarantees as specified in AGENTS.md"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
          <p>
            &bull; <strong style={{ color: "var(--text-primary)" }}>Deterministic Calculations:</strong> All numerical calculations (averages, correlations, p-values, metrics) are computed deterministically by DuckDB, Polars, SciPy, and scikit-learn. LLMs never compute numbers.
          </p>
          <p>
            &bull; <strong style={{ color: "var(--text-primary)" }}>Immutable Raw Datasets:</strong> Uploaded source files are strictly immutable. Cleaning or transformations generate versioned derivatives with complete lineage logs.
          </p>
          <p>
            &bull; <strong style={{ color: "var(--text-primary)" }}>Strict 4-Tier Layering:</strong> Presentation (Next.js/Vite) &rarr; API Routes (FastAPI) &rarr; Application Services &rarr; Pure Analytical Engines.
          </p>
        </div>
      </SectionCard>
    </div>
  );
}
