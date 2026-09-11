import React from "react";

interface StatCardProps {
  label: string;
  value?: string | number | null;
  subtext?: string;
  icon?: React.ReactNode;
  badge?: {
    text: string;
    variant?: "neutral" | "emerald" | "indigo" | "amber";
  };
}

export function StatCard({
  label,
  value,
  subtext,
  icon,
  badge,
}: StatCardProps) {
  const displayValue = value !== undefined && value !== null ? String(value) : "—";
  const isEvaluated = value !== undefined && value !== null;

  return (
    <div className="stat-card">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span className="stat-label">{label}</span>
        {icon && (
          <div style={{ color: "var(--text-muted)", display: "flex" }}>
            {icon}
          </div>
        )}
      </div>

      <div className="stat-value">
        <span
          style={{
            color: isEvaluated ? "var(--text-primary)" : "var(--text-faint)",
          }}
        >
          {displayValue}
        </span>
        {badge && (
          <span
            className={`badge ${
              badge.variant === "emerald"
                ? "badge-emerald"
                : badge.variant === "amber"
                ? "badge-amber"
                : badge.variant === "indigo"
                ? "badge-indigo"
                : "badge-neutral"
            }`}
            style={{ fontSize: "0.625rem" }}
          >
            {badge.text}
          </span>
        )}
      </div>

      {subtext && <span className="stat-subtext">{subtext}</span>}
    </div>
  );
}
