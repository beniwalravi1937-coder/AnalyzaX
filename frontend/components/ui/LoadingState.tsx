import React from "react";

export function CardSkeleton({ height = "120px" }: { height?: string }) {
  return (
    <div
      className="card"
      style={{
        height,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <div className="skeleton" style={{ width: "40%", height: "14px" }} />
      <div className="skeleton" style={{ width: "70%", height: "24px" }} />
      <div className="skeleton" style={{ width: "50%", height: "12px" }} />
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="table-wrapper" style={{ padding: "1rem" }}>
      <div
        className="skeleton"
        style={{ width: "100%", height: "36px", marginBottom: "0.75rem" }}
      />
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ width: "100%", height: "28px", marginBottom: "0.5rem" }}
        />
      ))}
    </div>
  );
}

export function ChartSkeleton({ height = "300px" }: { height?: string }) {
  return (
    <div
      className="card"
      style={{
        height,
        display: "flex",
        flexDirection: "column",
        padding: "1.25rem",
      }}
    >
      <div
        className="skeleton"
        style={{ width: "35%", height: "18px", marginBottom: "1.5rem" }}
      />
      <div className="skeleton" style={{ flex: 1, width: "100%" }} />
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div className="skeleton" style={{ width: "300px", height: "32px" }} />
      <div className="skeleton" style={{ width: "480px", height: "16px" }} />
      <div className="grid-4" style={{ marginTop: "1rem" }}>
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
      <ChartSkeleton height="350px" />
    </div>
  );
}
