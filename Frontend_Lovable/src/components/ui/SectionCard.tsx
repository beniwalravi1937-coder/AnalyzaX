import React from "react";

interface SectionCardProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function SectionCard({
  title,
  subtitle,
  actions,
  action,
  children,
  className = "",
}: SectionCardProps) {
  const headerActions = actions || action;
  return (
    <section className={`card ${className}`}>
      <div className="card-header">
        <div>
          <h2 className="card-title">{title}</h2>
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
        {headerActions && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            {headerActions}
          </div>
        )}
      </div>
      <div>{children}</div>
    </section>
  );
}
