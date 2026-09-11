"use client";

import React from "react";
import { ComponentDataResponse } from "@/types/dashboard";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";
import { ChartSpec } from "@/types";

interface ChartWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
  onCrossFilter?: (field: string, value: any) => void;
}

export function ChartWidget({ dataResp, configuration, onCrossFilter }: ChartWidgetProps) {
  const chartData = dataResp?.data || configuration.spec;

  if (!chartData || !chartData.chart_type) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#64748b" }}>
        No ChartSpec configured
      </div>
    );
  }

  const spec = chartData as ChartSpec;

  const handlePointClick = (params: any) => {
    if (!onCrossFilter || !params) return;
    const categoryField =
      (spec as any).encodings?.find((e: any) => e.semantic_role === "dimension")?.field ||
      spec.x ||
      spec.x_field ||
      "category";
    const clickedVal = params.name || params.value;
    if (clickedVal) {
      onCrossFilter(categoryField, clickedVal);
    }
  };

  return (
    <div style={{ width: "100%", height: "100%", minHeight: "220px" }}>
      <ChartRenderer
        spec={spec}
        height="100%"
        onDataPointClick={handlePointClick}
        onPointClick={handlePointClick}
      />
    </div>
  );
}
