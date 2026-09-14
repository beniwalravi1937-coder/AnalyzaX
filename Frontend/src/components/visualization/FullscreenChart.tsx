"use client";

import React, { useEffect } from "react";
import { ChartSpec, VisualizationEvent } from "@/types";
import { ChartRenderer } from "./ChartRenderer";

interface FullscreenChartProps {
  isOpen: boolean;
  onClose: () => void;
  spec: ChartSpec;
  data: Record<string, any>[];
  onPointClick?: (params: {
    name?: string;
    value?: any;
    seriesName?: string;
    dataIndex?: number;
    raw?: any;
  }) => void;
}

export function FullscreenChart({
  isOpen,
  onClose,
  spec,
  data,
  onPointClick,
}: FullscreenChartProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(10, 15, 29, 0.95)",
        backdropFilter: "blur(8px)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        padding: "1.5rem",
      }}
    >
      {/* Header bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingBottom: "1rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
            {spec.title || "Fullscreen Visualization"}
          </h2>
          {spec.subtitle && (
            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
              {spec.subtitle}
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="btn btn-secondary btn-sm"
          style={{
            fontSize: "0.85rem",
            padding: "0.4rem 0.8rem",
            borderRadius: "0.375rem",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
          }}
        >
          <span>✕</span> Close Fullscreen (Esc)
        </button>
      </div>

      {/* Chart container */}
      <div
        style={{
          flex: 1,
          marginTop: "1rem",
          backgroundColor: "var(--bg-surface, #0f172a)",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-subtle)",
          padding: "1rem",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <div style={{ flex: 1, minHeight: 0 }}>
          <ChartRenderer
            spec={spec}
            data={data}
            height="100%"
            onPointClick={onPointClick}
          />
        </div>
      </div>
    </div>
  );
}
