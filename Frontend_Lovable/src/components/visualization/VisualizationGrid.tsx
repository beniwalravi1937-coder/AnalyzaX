"use client";

import React, { useState, useMemo } from "react";
import { VisualizationRecommendation, SavedVisualization, ChartSpec } from "@/types";
import { VisualizationCard } from "./VisualizationCard";

interface VisualizationGridProps {
  recommendations?: VisualizationRecommendation[];
  savedCharts?: SavedVisualization[];
  onSelect: (spec: ChartSpec) => void;
  onDelete?: (id: string) => void;
  selectedSpec?: ChartSpec | null;
}

const CATEGORY_MAP: Record<string, string[]> = {
  All: [],
  Comparison: ["bar", "grouped_bar", "stacked_bar", "horizontal_bar"],
  Distribution: ["histogram", "boxplot", "violin"],
  Trend: ["line", "multi_line", "area", "stacked_area"],
  Composition: ["donut", "pie", "treemap"],
  Relationship: ["scatter", "bubble", "heatmap"],
};

export function VisualizationGrid({
  recommendations,
  savedCharts,
  onSelect,
  onDelete,
  selectedSpec,
}: VisualizationGridProps) {
  const [activeCategory, setActiveCategory] = useState("All");

  const items = useMemo(() => {
    if (recommendations) {
      if (activeCategory === "All") return recommendations;
      const allowedTypes = CATEGORY_MAP[activeCategory] || [];
      return recommendations.filter(
        (r) => r.spec?.chart_type && allowedTypes.includes(r.spec.chart_type)
      );
    }
    if (savedCharts) {
      if (activeCategory === "All") return savedCharts;
      const allowedTypes = CATEGORY_MAP[activeCategory] || [];
      return savedCharts.filter(
        (s) => s.spec?.chart_type && allowedTypes.includes(s.spec.chart_type)
      );
    }
    return [];
  }, [recommendations, savedCharts, activeCategory]);

  return (
    <div>
      {/* Category filter pills */}
      <div
        style={{
          display: "flex",
          gap: "0.4rem",
          overflowX: "auto",
          paddingBottom: "0.5rem",
          marginBottom: "1rem",
        }}
      >
        {Object.keys(CATEGORY_MAP).map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`btn btn-sm ${activeCategory === cat ? "btn-primary" : "btn-secondary"}`}
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Grid */}
      {items.length === 0 ? (
        <div
          style={{
            padding: "2rem",
            textAlign: "center",
            color: "var(--text-secondary)",
            fontSize: "0.85rem",
            backgroundColor: "rgba(15, 23, 42, 0.2)",
            borderRadius: "0.5rem",
            border: "1px dashed var(--border-subtle)",
          }}
        >
          No visualizations match the &quot;{activeCategory}&quot; category.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: "1rem",
          }}
        >
          {recommendations &&
            (items as VisualizationRecommendation[]).map((rec, idx) => (
              <VisualizationCard
                key={rec.spec.id || idx}
                recommendation={rec}
                onSelect={onSelect}
                isSelected={selectedSpec?.id === rec.spec.id}
              />
            ))}

          {savedCharts &&
            (items as SavedVisualization[]).map((chart) => (
              <VisualizationCard
                key={chart.id}
                savedChart={chart}
                onSelect={onSelect}
                onDelete={onDelete}
                isSelected={selectedSpec?.id === chart.spec.id}
              />
            ))}
        </div>
      )}
    </div>
  );
}
