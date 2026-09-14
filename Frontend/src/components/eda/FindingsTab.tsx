"use client";

import React, { useState, useMemo } from "react";
import { EDAFinding } from "@/types";
import { SearchIcon, AlertCircleIcon, CheckIcon } from "@/components/icons";

interface FindingsTabProps {
  findings: EDAFinding[];
}

function normalizeSeverity(s: string): "critical" | "warning" | "info" | string {
  const lower = String(s || "").toLowerCase();
  if (lower === "high" || lower === "critical") return "critical";
  if (lower === "medium" || lower === "warning") return "warning";
  if (lower === "low" || lower === "info") return "info";
  return lower;
}

export function FindingsTab({ findings }: FindingsTabProps) {
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Unique categories
  const categories = useMemo(() => {
    const cats = new Set<string>();
    findings.forEach((f) => {
      if (f.category) cats.add(f.category);
    });
    return Array.from(cats);
  }, [findings]);

  // Counts by severity
  const counts = useMemo(() => {
    return {
      all: findings.length,
      critical: findings.filter((f) => normalizeSeverity(f.severity) === "critical").length,
      warning: findings.filter((f) => normalizeSeverity(f.severity) === "warning").length,
      info: findings.filter((f) => normalizeSeverity(f.severity) === "info").length,
    };
  }, [findings]);

  // Filtered findings
  const filtered = useMemo(() => {
    return findings.filter((f) => {
      const normSev = normalizeSeverity(f.severity);
      const matchesSeverity = severityFilter === "all" || normSev === severityFilter;
      const matchesCat = categoryFilter === "all" || f.category.toLowerCase() === categoryFilter.toLowerCase();
      const title = f.title || "";
      const msg = f.message || f.description || "";
      const rec = f.recommendation || f.evidence || "";
      const cols = f.impacted_columns || f.columns || [];

      const matchesSearch =
        searchQuery === "" ||
        title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        msg.toLowerCase().includes(searchQuery.toLowerCase()) ||
        rec.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cols.some((col) => col.toLowerCase().includes(searchQuery.toLowerCase()));

      return matchesSeverity && matchesCat && matchesSearch;
    });
  }, [findings, severityFilter, categoryFilter, searchQuery]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header Filter Controls */}
      <div
        className="card"
        style={{
          padding: "1.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Automated Analytical Findings & Rule-Based Insights
            </h3>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              Heuristic patterns, distribution anomalies, and multicollinearity alerts detected by AnalyzaX EDA Intelligence Engine.
            </p>
          </div>

          {/* Search box */}
          <div style={{ position: "relative", minWidth: "260px" }}>
            <SearchIcon
              size={14}
              style={{
                position: "absolute",
                left: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            />
            <input
              type="text"
              placeholder="Search findings or column..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input"
              style={{ paddingLeft: "2rem", width: "100%", fontSize: "0.8125rem" }}
            />
          </div>
        </div>

        {/* Severity Tabs & Category Badges */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.75rem" }}>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              onClick={() => setSeverityFilter("all")}
              className={`btn ${severityFilter === "all" ? "btn-primary" : "btn-ghost"}`}
              style={{ fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}
            >
              All ({counts.all})
            </button>
            <button
              onClick={() => setSeverityFilter("critical")}
              className={`btn ${severityFilter === "critical" ? "btn-primary" : "btn-ghost"}`}
              style={{
                fontSize: "0.75rem",
                padding: "0.3rem 0.75rem",
                color: severityFilter !== "critical" ? "#f43f5e" : undefined,
              }}
            >
              Critical ({counts.critical})
            </button>
            <button
              onClick={() => setSeverityFilter("warning")}
              className={`btn ${severityFilter === "warning" ? "btn-primary" : "btn-ghost"}`}
              style={{
                fontSize: "0.75rem",
                padding: "0.3rem 0.75rem",
                color: severityFilter !== "warning" ? "#f59e0b" : undefined,
              }}
            >
              Warning ({counts.warning})
            </button>
            <button
              onClick={() => setSeverityFilter("info")}
              className={`btn ${severityFilter === "info" ? "btn-primary" : "btn-ghost"}`}
              style={{
                fontSize: "0.75rem",
                padding: "0.3rem 0.75rem",
                color: severityFilter !== "info" ? "#38bdf8" : undefined,
              }}
            >
              Info ({counts.info})
            </button>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Category:</span>
            <button
              onClick={() => setCategoryFilter("all")}
              className={`badge ${categoryFilter === "all" ? "badge-primary" : "badge-neutral"}`}
              style={{ cursor: "pointer", fontSize: "0.6875rem" }}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`badge ${categoryFilter === cat ? "badge-primary" : "badge-neutral"}`}
                style={{ cursor: "pointer", fontSize: "0.6875rem", textTransform: "capitalize" }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Findings Cards List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {filtered.length === 0 ? (
          <div className="card" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
            <CheckIcon size={32} style={{ color: "#10b981", margin: "0 auto 0.75rem" }} />
            <h4 style={{ color: "var(--text-primary)", fontSize: "1rem" }}>No matching findings</h4>
            <p style={{ fontSize: "0.8125rem", marginTop: "0.25rem" }}>
              No automated findings match the selected severity and category filters.
            </p>
          </div>
        ) : (
          filtered.map((finding) => (
            <FindingFullCard key={finding.finding_id || (finding as any).id || finding.title} finding={finding} />
          ))
        )}
      </div>
    </div>
  );
}

function FindingFullCard({ finding }: { finding: EDAFinding }) {
  const normSev = normalizeSeverity(finding.severity);
  const isCritical = normSev === "critical";
  const isWarning = normSev === "warning";

  const borderColor = isCritical
    ? "rgba(244, 63, 94, 0.3)"
    : isWarning
    ? "rgba(245, 158, 11, 0.3)"
    : "var(--border-subtle)";

  const badgeClass = isCritical
    ? "badge-rose"
    : isWarning
    ? "badge-amber"
    : "badge-indigo";

  const message = finding.message || finding.description || "";
  const recommendation = finding.recommendation || (finding as any).actionable_recommendation || finding.evidence || "";
  const columns: string[] = finding.impacted_columns || finding.columns || (finding as any).affected_columns || [];

  return (
    <div
      className="card"
      style={{
        padding: "1.25rem",
        border: `1px solid ${borderColor}`,
        borderRadius: "var(--radius-md)",
      }}
    >
      {/* Top row: Severity, Category, Title */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
            <span className={`badge ${badgeClass}`} style={{ fontSize: "0.6875rem", textTransform: "uppercase" }}>
              {normSev}
            </span>
            <span className="badge badge-neutral" style={{ fontSize: "0.6875rem", textTransform: "capitalize" }}>
              {finding.category}
            </span>
          </div>

          <h4 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {finding.title}
          </h4>
        </div>
      </div>

      {/* Message description */}
      {message && (
        <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginTop: "0.6rem", lineHeight: 1.5 }}>
          {message}
        </p>
      )}

      {/* Impacted Columns */}
      {columns && columns.length > 0 && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Impacted Features:</span>
          {columns.map((col) => (
            <span
              key={col}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.6875rem",
                padding: "2px 6px",
                borderRadius: "4px",
                backgroundColor: "rgba(255, 255, 255, 0.05)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
              }}
            >
              {col}
            </span>
          ))}
        </div>
      )}

      {/* Actionable Recommendation Box */}
      {recommendation && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            backgroundColor: "rgba(99, 102, 241, 0.06)",
            border: "1px solid rgba(99, 102, 241, 0.2)",
            borderRadius: "var(--radius-sm)",
            fontSize: "0.8125rem",
            color: "var(--text-primary)",
            display: "flex",
            alignItems: "flex-start",
            gap: "0.5rem",
          }}
        >
          <span style={{ color: "#818cf8", fontWeight: 700 }}>💡 Recommendation:</span>
          <span style={{ color: "var(--text-secondary)" }}>{recommendation}</span>
        </div>
      )}
    </div>
  );
}
