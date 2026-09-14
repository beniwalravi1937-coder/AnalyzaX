"use client";

import React from "react";
import { DashboardComponent, ComponentDataResponse } from "@/types/dashboard";
import { DashboardComponentCard } from "./DashboardComponentCard";
import { BarChart3, Plus } from "lucide-react";

interface DashboardGridProps {
  components: DashboardComponent[];
  componentData: Record<string, ComponentDataResponse>;
  isEditMode: boolean;
  onEditComponent: (component: DashboardComponent) => void;
  onDuplicateComponent: (componentId: string) => void;
  onDeleteComponent: (componentId: string) => void;
  onResizeWidth: (componentId: string, newWidth: number) => void;
  onInspectProvenance: (component: DashboardComponent) => void;
  onCrossFilter?: (field: string, value: any) => void;
  onOpenPalette: () => void;
}

export function DashboardGrid({
  components,
  componentData,
  isEditMode,
  onEditComponent,
  onDuplicateComponent,
  onDeleteComponent,
  onResizeWidth,
  onInspectProvenance,
  onCrossFilter,
  onOpenPalette,
}: DashboardGridProps) {
  if (components.length === 0) {
    return (
      <div
        style={{
          border: "2px dashed rgba(51, 65, 85, 0.6)",
          borderRadius: "12px",
          padding: "4rem 2rem",
          textAlign: "center",
          background: "rgba(15, 23, 42, 0.4)",
          margin: "1rem 0",
        }}
      >
        <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4 text-indigo-400">
          <BarChart3 className="w-6 h-6" />
        </div>
        <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#ffffff", marginBottom: "0.5rem" }}>
          Your Dashboard is Empty
        </h3>
        <p style={{ color: "#94a3b8", maxWidth: "480px", margin: "0 auto 1.5rem auto", fontSize: "0.9rem" }}>
          Start building your analytical narrative. Add KPI cards, ChartSpec visualizations, statistical tests, ML metrics, or narrative text blocks.
        </p>
        <button onClick={onOpenPalette} className="btn btn-primary" style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <Plus className="w-4 h-4" />
          <span>Add First Component</span>
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(12, 1fr)",
        gap: "1.25rem",
        gridAutoRows: "minmax(80px, auto)",
        width: "100%",
      }}
    >
      {components.map((cmp) => {
        const colSpan = Math.max(1, Math.min(12, cmp.size?.width || 6));
        const rowSpan = Math.max(1, Math.min(24, cmp.size?.height || 4));

        return (
          <div
            key={cmp.component_id}
            style={{
              gridColumn: `span ${colSpan}`,
              minHeight: `${rowSpan * 60}px`,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <DashboardComponentCard
              component={cmp}
              dataResp={componentData[cmp.component_id]}
              isEditMode={isEditMode}
              onEdit={onEditComponent}
              onDuplicate={onDuplicateComponent}
              onDelete={onDeleteComponent}
              onResizeWidth={onResizeWidth}
              onInspectProvenance={onInspectProvenance}
              onCrossFilter={onCrossFilter}
            />
          </div>
        );
      })}
    </div>
  );
}
