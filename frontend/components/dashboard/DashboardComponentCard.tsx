"use client";

import React, { useState } from "react";
import { DashboardComponent, ComponentDataResponse } from "@/types/dashboard";
import { KpiWidget } from "./widgets/KpiWidget";
import { ChartWidget } from "./widgets/ChartWidget";
import { TableWidget } from "./widgets/TableWidget";
import { StatisticsWidget } from "./widgets/StatisticsWidget";
import { MlResultWidget } from "./widgets/MlResultWidget";
import { ForecastWidget } from "./widgets/ForecastWidget";
import { EdaFindingWidget } from "./widgets/EdaFindingWidget";
import { AiInsightWidget } from "./widgets/AiInsightWidget";
import { NarrativeWidget } from "./widgets/NarrativeWidget";

interface DashboardComponentCardProps {
  component: DashboardComponent;
  dataResp?: ComponentDataResponse;
  isEditMode: boolean;
  onEdit: (component: DashboardComponent) => void;
  onDuplicate: (componentId: string) => void;
  onDelete: (componentId: string) => void;
  onResizeWidth: (componentId: string, newWidth: number) => void;
  onInspectProvenance: (component: DashboardComponent) => void;
  onCrossFilter?: (field: string, value: any) => void;
}

export function DashboardComponentCard({
  component,
  dataResp,
  isEditMode,
  onEdit,
  onDuplicate,
  onDelete,
  onResizeWidth,
  onInspectProvenance,
  onCrossFilter,
}: DashboardComponentCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  const status = dataResp?.status || component.status || "READY";
  const isStale = dataResp?.is_stale || status === "STALE_VERSION";
  const isError = status === "ERROR";

  const renderWidget = () => {
    if (isError) {
      return (
        <div
          style={{
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            color: "#f87171",
            padding: "1rem",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "1.2rem", marginBottom: "0.25rem" }}>⚠️</div>
          <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>Component Failed to Load</div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>
            {dataResp?.error_message || "An unexpected error occurred."}
          </div>
        </div>
      );
    }

    switch (component.type) {
      case "KPI":
        return <KpiWidget dataResp={dataResp} configuration={component.configuration} />;
      case "CHART":
        return <ChartWidget dataResp={dataResp} configuration={component.configuration} onCrossFilter={onCrossFilter} />;
      case "TABLE":
        return <TableWidget dataResp={dataResp} configuration={component.configuration} />;
      case "STATISTICS":
        return <StatisticsWidget dataResp={dataResp} configuration={component.configuration} />;
      case "ML_RESULT":
        return <MlResultWidget dataResp={dataResp} configuration={component.configuration} />;
      case "FORECAST":
        return <ForecastWidget dataResp={dataResp} configuration={component.configuration} />;
      case "EDA_FINDING":
        return <EdaFindingWidget dataResp={dataResp} configuration={component.configuration} />;
      case "AI_INSIGHT":
        return <AiInsightWidget dataResp={dataResp} configuration={component.configuration} />;
      case "TEXT":
        return <NarrativeWidget dataResp={dataResp} configuration={component.configuration} />;
      case "SECTION":
      case "DIVIDER":
        return null;
      default:
        return (
          <div style={{ color: "#94a3b8", fontSize: "0.85rem" }}>
            {JSON.stringify(dataResp?.data || component.configuration)}
          </div>
        );
    }
  };

  // If SECTION / DIVIDER
  if (component.type === "SECTION" || component.type === "DIVIDER") {
    return (
      <div
        style={{
          borderBottom: "2px solid rgba(99, 102, 241, 0.4)",
          paddingBottom: "0.5rem",
          margin: "1rem 0",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700, color: "#ffffff" }}>
            {component.title}
          </h2>
          {component.subtitle && (
            <span style={{ fontSize: "0.85rem", color: "#94a3b8" }}>{component.subtitle}</span>
          )}
        </div>
        {isEditMode && (
          <button
            onClick={() => onDelete(component.component_id)}
            style={{ background: "transparent", border: "none", color: "#f87171", cursor: "pointer", fontSize: "0.8rem" }}
          >
            Remove Section
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        background: "#1e293b",
        border: isStale
          ? "1px solid rgba(239, 68, 68, 0.5)"
          : isError
          ? "1px solid rgba(239, 68, 68, 0.4)"
          : "1px solid rgba(51, 65, 85, 0.6)",
        borderRadius: "10px",
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.2)",
        position: "relative",
      }}
    >
      {/* Component Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
        <div style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "#ffffff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {component.title}
            </h3>
            {isStale && (
              <span
                style={{
                  fontSize: "0.65rem",
                  fontWeight: 700,
                  background: "rgba(239, 68, 68, 0.2)",
                  color: "#f87171",
                  padding: "0.1rem 0.4rem",
                  borderRadius: "4px",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                }}
              >
                STALE VERSION
              </span>
            )}
          </div>
          {component.subtitle && (
            <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{component.subtitle}</span>
          )}
        </div>

        {/* Action icons / menu */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <button
            onClick={() => onInspectProvenance(component)}
            title="Inspect Source & Provenance"
            style={{
              background: "rgba(15, 23, 42, 0.5)",
              border: "1px solid rgba(51, 65, 85, 0.5)",
              color: "#94a3b8",
              borderRadius: "4px",
              padding: "0.2rem 0.45rem",
              fontSize: "0.7rem",
              cursor: "pointer",
            }}
          >
            Source
          </button>

          {isEditMode && (
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setShowMenu(!showMenu)}
                style={{
                  background: "rgba(15, 23, 42, 0.5)",
                  border: "1px solid rgba(51, 65, 85, 0.5)",
                  color: "#cbd5e1",
                  borderRadius: "4px",
                  padding: "0.2rem 0.45rem",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                }}
              >
                •••
              </button>

              {showMenu && (
                <div
                  style={{
                    position: "absolute",
                    right: 0,
                    top: "100%",
                    marginTop: "0.25rem",
                    background: "#0f172a",
                    border: "1px solid rgba(51, 65, 85, 0.8)",
                    borderRadius: "6px",
                    boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
                    zIndex: 10,
                    minWidth: "140px",
                    display: "flex",
                    flexDirection: "column",
                  }}
                  onMouseLeave={() => setShowMenu(false)}
                >
                  <button
                    onClick={() => {
                      onEdit(component);
                      setShowMenu(false);
                    }}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#cbd5e1",
                      padding: "0.5rem 0.75rem",
                      textAlign: "left",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    Edit Config
                  </button>
                  <button
                    onClick={() => {
                      onDuplicate(component.component_id);
                      setShowMenu(false);
                    }}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#cbd5e1",
                      padding: "0.5rem 0.75rem",
                      textAlign: "left",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    Duplicate
                  </button>

                  <div style={{ borderTop: "1px solid rgba(51,65,85,0.4)", margin: "0.25rem 0" }} />

                  {/* Width adjustments */}
                  <div style={{ padding: "0.25rem 0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Width: {component.size.width}</span>
                    <div style={{ display: "flex", gap: "0.2rem" }}>
                      <button
                        onClick={() => onResizeWidth(component.component_id, Math.max(1, component.size.width - 1))}
                        disabled={component.size.width <= 1}
                        style={{ padding: "0.1rem 0.3rem", fontSize: "0.7rem", cursor: "pointer" }}
                      >
                        -
                      </button>
                      <button
                        onClick={() => onResizeWidth(component.component_id, Math.min(12, component.size.width + 1))}
                        disabled={component.size.width >= 12}
                        style={{ padding: "0.1rem 0.3rem", fontSize: "0.7rem", cursor: "pointer" }}
                      >
                        +
                      </button>
                    </div>
                  </div>

                  <div style={{ borderTop: "1px solid rgba(51,65,85,0.4)", margin: "0.25rem 0" }} />

                  <button
                    onClick={() => {
                      onDelete(component.component_id);
                      setShowMenu(false);
                    }}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#f87171",
                      padding: "0.5rem 0.75rem",
                      textAlign: "left",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Widget Body */}
      <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
        {renderWidget()}
      </div>
    </div>
  );
}
