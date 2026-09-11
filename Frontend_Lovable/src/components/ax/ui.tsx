import React from "react";
import { Link } from "@tanstack/react-router";

import type { Row } from "../../lib/ax/types";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="ax-page-header">
      <div>
        {eyebrow && <span className="badge badge-indigo">{eyebrow}</span>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="ax-page-actions">{actions}</div>}
    </div>
  );
}

export function StatCard({
  label,
  value,
  sub,
  tone = "indigo",
}: {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  tone?: "indigo" | "emerald" | "amber" | "rose" | "cyan";
}) {
  return (
    <div className="stat-card" data-tone={tone}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {sub && <span className="stat-subtext">{sub}</span>}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon">{icon}</div>}
      <div className="empty-state-title">{title}</div>
      {description && <div className="empty-state-desc">{description}</div>}
      {action}
    </div>
  );
}

export function NoDataState() {
  return (
    <EmptyState
      title="No dataset loaded"
      description="Upload a CSV or Excel-exported file to start profiling, cleaning and charting your data — everything runs right here in your browser."
      action={
        <Link to="/data" className="btn btn-primary">
          Go to data sources
        </Link>
      }
    />
  );
}

export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: Array<{ value: T; label: string; icon?: React.ReactNode }>;
}) {
  return (
    <div className="segmented">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          className={o.value === value ? "segmented-item active" : "segmented-item"}
          onClick={() => onChange(o.value)}
        >
          {o.icon}
          <span>{o.label}</span>
        </button>
      ))}
    </div>
  );
}

export function DataTable({
  columns,
  rows,
  limit = 25,
}: {
  columns: string[];
  rows: Row[];
  limit?: number;
}) {
  const shown = rows.slice(0, limit);
  return (
    <div className="table-wrapper">
      <table className="analyzax-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((r, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c}>
                  {r[c] === null || r[c] === "" ? (
                    <span className="cell-null">null</span>
                  ) : (
                    String(r[c])
                  )}
                </td>
              ))}
            </tr>
          ))}
          {shown.length === 0 && (
            <tr>
              <td colSpan={Math.max(1, columns.length)}>No rows</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function Card({
  title,
  subtitle,
  actions,
  children,
}: {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="card">
      {(title || actions) && (
        <div className="card-header">
          <div>
            {title && <div className="card-title">{title}</div>}
            {subtitle && <div className="card-subtitle">{subtitle}</div>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </div>
  );
}
