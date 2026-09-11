"use client";

import React from "react";
import { ComponentType } from "@/types/dashboard";
import {
  BarChartIcon,
  StatisticsIcon,
  MLIcon,
  ForecastingIcon,
  EDAIcon,
  AIAnalystIcon,
  DatasetIcon,
  DashboardIcon,
} from "@/components/icons";

interface ComponentPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectType: (type: ComponentType) => void;
}

const PALETTE_OPTIONS: {
  type: ComponentType;
  title: string;
  desc: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
}[] = [
  {
    type: "KPI",
    title: "KPI Metric Card",
    desc: "Scalar aggregate (sum, avg, count, max) with formatted typography and comparisons.",
    icon: DashboardIcon,
    color: "#34d399",
  },
  {
    type: "CHART",
    title: "ChartSpec Visualization",
    desc: "Embed Phase 9 line, bar, scatter, donut, or heatmap chart with interactive cross-filtering.",
    icon: BarChartIcon,
    color: "#818cf8",
  },
  {
    type: "TABLE",
    title: "Bounded Data Table",
    desc: "Paginated, searchable data table backed by in-memory DuckDB queries.",
    icon: DatasetIcon,
    color: "#38bdf8",
  },
  {
    type: "STATISTICS",
    title: "Hypothesis Test / ANOVA",
    desc: "Embed Phase 10 statistical significance test with p-value and filter safety warnings.",
    icon: StatisticsIcon,
    color: "#f59e0b",
  },
  {
    type: "ML_RESULT",
    title: "Machine Learning Model",
    desc: "Champion model evaluation metrics, lift over baseline, and feature importance.",
    icon: MLIcon,
    color: "#ec4899",
  },
  {
    type: "FORECAST",
    title: "Temporal Forecast",
    desc: "Horizon forecast predictions and validation metrics from Phase 12.",
    icon: ForecastingIcon,
    color: "#06b6d4",
  },
  {
    type: "EDA_FINDING",
    title: "EDA Discovery Card",
    desc: "Automated distribution anomaly, high correlation, or quality audit observation.",
    icon: EDAIcon,
    color: "#a855f7",
  },
  {
    type: "AI_INSIGHT",
    title: "AI Analyst Insight",
    desc: "Natural-language analytical synthesis with citations to underlying data results.",
    icon: AIAnalystIcon,
    color: "#6366f1",
  },
  {
    type: "TEXT",
    title: "Narrative Markdown",
    desc: "Executive summaries, annotations, bullet lists, and structured explanations.",
    icon: DashboardIcon,
    color: "#e2e8f0",
  },
  {
    type: "SECTION",
    title: "Section Divider",
    desc: "Visual separator and category header to organize complex dashboard workflows.",
    icon: DashboardIcon,
    color: "#64748b",
  },
];

export function ComponentPaletteModal({ isOpen, onClose, onSelectType }: ComponentPaletteModalProps) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.8)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#1e293b",
          border: "1px solid rgba(99, 102, 241, 0.3)",
          borderRadius: "14px",
          padding: "1.5rem",
          maxWidth: "680px",
          width: "92%",
          maxHeight: "85vh",
          overflowY: "auto",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.6)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, color: "#ffffff" }}>
              Add Dashboard Component
            </h3>
            <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.85rem", color: "#94a3b8" }}>
              Choose an analytical widget or presentation block to add to your grid.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "1.25rem",
            }}
          >
            ✕
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: "0.85rem",
          }}
        >
          {PALETTE_OPTIONS.map((opt) => {
            const IconComp = opt.icon;
            return (
              <button
                key={opt.type}
                onClick={() => {
                  onSelectType(opt.type);
                  onClose();
                }}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.85rem",
                  padding: "1rem",
                  background: "rgba(15, 23, 42, 0.6)",
                  border: "1px solid rgba(51, 65, 85, 0.6)",
                  borderRadius: "10px",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = opt.color;
                  e.currentTarget.style.transform = "translateY(-2px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "rgba(51, 65, 85, 0.6)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div
                  style={{
                    padding: "0.5rem",
                    borderRadius: "8px",
                    background: `${opt.color}22`,
                    color: opt.color,
                    flexShrink: 0,
                  }}
                >
                  <IconComp size={20} />
                </div>
                <div>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#ffffff", marginBottom: "0.25rem" }}>
                    {opt.title}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", lineHeight: 1.4 }}>
                    {opt.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
