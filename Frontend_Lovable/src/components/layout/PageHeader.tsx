import React from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: {
    text: string;
    variant?: "neutral" | "emerald" | "indigo" | "amber";
  };
  actions?: React.ReactNode;
}

export function PageHeader({
  title,
  description,
  badge,
  actions,
}: PageHeaderProps) {
  const badgeClass =
    badge?.variant === "emerald"
      ? "badge-emerald"
      : badge?.variant === "indigo"
      ? "badge-indigo"
      : badge?.variant === "amber"
      ? "badge-amber"
      : "badge-neutral";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: "1.5rem",
        marginBottom: "1.75rem",
        flexWrap: "wrap",
      }}
    >
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <h1
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--text-primary)",
              letterSpacing: "-0.02em",
            }}
          >
            {title}
          </h1>
          {badge && <span className={`badge ${badgeClass}`}>{badge.text}</span>}
        </div>
        {description && (
          <p
            style={{
              fontSize: "0.875rem",
              color: "var(--text-muted)",
              marginTop: "0.25rem",
              maxWidth: "680px",
              lineHeight: 1.5,
            }}
          >
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {actions}
        </div>
      )}
    </div>
  );
}
