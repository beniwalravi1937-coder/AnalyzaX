"use client";

import React from "react";
import { VisualizationRecommendation, SavedVisualization, ChartSpec } from "@/types";
import { BarChartIcon, EyeIcon, TrashIcon, ArrowRightIcon } from "@/components/icons";

interface VisualizationCardProps {
  recommendation?: VisualizationRecommendation;
  savedChart?: SavedVisualization;
  onSelect?: (spec: ChartSpec) => void;
  onDelete?: (id: string) => void;
  isSelected?: boolean;
}

export function VisualizationCard({
  recommendation,
  savedChart,
  onSelect,
  onDelete,
  isSelected,
}: VisualizationCardProps) {
  const spec = recommendation?.spec || savedChart?.spec;
  if (!spec) return null;

  const score = recommendation?.score ?? null;
  const rationale = recommendation?.rationale || savedChart?.description;
  const isRecommended = recommendation?.is_recommended;

  // Visual badge for chart family
  const chartType = spec.chart_type;

  return (
    <div
      className={`card ${isSelected ? "border-brand" : ""}`}
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "1rem",
        backgroundColor: "var(--bg-surface, #0f172a)",
        border: isSelected ? "2px solid var(--brand-primary, #6366f1)" : "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        transition: "transform 0.15s ease, border-color 0.15s ease",
        cursor: "pointer",
        position: "relative",
      }}
      onClick={() => onSelect && onSelect(spec)}
    >
      <div>
        {/* Header: Title & Badges */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.5rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  padding: "0.15rem 0.4rem",
                  borderRadius: "0.25rem",
                  backgroundColor: "rgba(99, 102, 241, 0.15)",
                  color: "var(--brand-primary, #6366f1)",
                }}
              >
                {chartType}
              </span>

              {isRecommended && (
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 600,
                    padding: "0.15rem 0.4rem",
                    borderRadius: "0.25rem",
                    backgroundColor: "rgba(16, 185, 129, 0.15)",
                    color: "var(--status-success, #10b981)",
                  }}
                >
                  ★ Recommended
                </span>
              )}

              {score !== null && (
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 600,
                    padding: "0.15rem 0.4rem",
                    borderRadius: "0.25rem",
                    backgroundColor: "rgba(245, 158, 11, 0.15)",
                    color: "var(--status-warning, #f59e0b)",
                  }}
                  title="Deterministic suitability score (0-1)"
                >
                  Score: {Math.round(score * 100)}%
                </span>
              )}
            </div>

            <h4
              style={{
                fontSize: "0.925rem",
                fontWeight: 600,
                color: "var(--text-primary)",
                margin: "0.4rem 0 0.2rem 0",
              }}
            >
              {spec.title || savedChart?.name || "Untitled Chart"}
            </h4>
          </div>

          {onDelete && savedChart && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(savedChart.id);
              }}
              className="btn btn-ghost btn-sm"
              style={{ padding: "0.25rem", color: "var(--status-danger, #ef4444)" }}
              title="Delete saved chart"
            >
              <TrashIcon size={14} />
            </button>
          )}
        </div>

        {/* Fields summary */}
        <div
          style={{
            fontSize: "0.75rem",
            color: "var(--text-secondary)",
            marginTop: "0.4rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.15rem",
          }}
        >
          {spec.x_axis?.field && (
            <div>
              <span style={{ color: "var(--text-muted)" }}>X: </span>
              <strong>{spec.x_axis.field}</strong>
            </div>
          )}
          {spec.y_axis?.field && (
            <div>
              <span style={{ color: "var(--text-muted)" }}>Y: </span>
              <strong>{spec.y_axis.field}</strong>
              {spec.y_axis.aggregation && (
                <span style={{ color: "var(--brand-primary, #6366f1)" }}> ({spec.y_axis.aggregation})</span>
              )}
            </div>
          )}
          {spec.series_field && (
            <div>
              <span style={{ color: "var(--text-muted)" }}>Series: </span>
              <strong>{spec.series_field}</strong>
            </div>
          )}
        </div>

        {/* Rationale explanation */}
        {rationale && (
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--text-secondary)",
              backgroundColor: "rgba(255, 255, 255, 0.03)",
              borderRadius: "0.375rem",
              padding: "0.4rem 0.6rem",
              marginTop: "0.6rem",
              lineHeight: 1.35,
            }}
          >
            {rationale}
          </div>
        )}
      </div>

      {/* Footer Action */}
      <div
        style={{
          marginTop: "1rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderTop: "1px solid var(--border-subtle)",
          paddingTop: "0.6rem",
        }}
      >
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
          {savedChart ? `v${savedChart.dataset_version_id}` : spec.rule_id ? `Rule: ${spec.rule_id}` : "Custom"}
        </span>

        <span
          style={{
            fontSize: "0.75rem",
            fontWeight: 600,
            color: "var(--brand-primary, #6366f1)",
            display: "flex",
            alignItems: "center",
            gap: "0.25rem",
          }}
        >
          Open in Studio <ArrowRightIcon size={12} />
        </span>
      </div>
    </div>
  );
}
