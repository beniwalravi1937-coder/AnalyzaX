"use client";

import React, { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { ChartSpec } from "@/types";

interface ChartRendererProps {
  spec: ChartSpec;
  data?: Record<string, any>[];
  height?: number | string;
  onDataPointClick?: (params: {
    name?: string;
    value?: any;
    seriesName?: string;
    dataIndex?: number;
    raw?: any;
  }) => void;
  onPointClick?: (params: {
    name?: string;
    value?: any;
    seriesName?: string;
    dataIndex?: number;
    raw?: any;
  }) => void;
  className?: string;
}

export function ChartRenderer({
  spec,
  data: propData,
  height = 380,
  onDataPointClick,
  onPointClick,
  className = "",
}: ChartRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Dispose old instance if spec changes
    if (chartInstanceRef.current) {
      chartInstanceRef.current.dispose();
      chartInstanceRef.current = null;
    }

    try {
      setRenderError(null);
      const chart = echarts.init(containerRef.current, "dark", {
        renderer: "canvas",
      });
      chartInstanceRef.current = chart;

      const effectiveSpec = propData ? { ...spec, data: propData } : spec;
      const option = buildEChartsOption(effectiveSpec);
      chart.setOption(option, true);

      // Handle interactive data point clicks (VIZ-29)
      chart.on("click", (params: any) => {
        const pointData = {
          name: params.name,
          value: params.value,
          seriesName: params.seriesName,
          dataIndex: params.dataIndex,
          raw: params.data,
        };
        if (onDataPointClick) onDataPointClick(pointData);
        if (onPointClick) onPointClick(pointData);
      });

      // Responsive resize observer (VIZ-54)
      const resizeObserver = new ResizeObserver(() => {
        chart.resize();
      });
      resizeObserver.observe(containerRef.current);

      return () => {
        resizeObserver.disconnect();
        chart.dispose();
        chartInstanceRef.current = null;
      };
    } catch (err: any) {
      console.error("ECharts rendering error:", err);
      setRenderError(err?.message || "Failed to render chart");
    }
  }, [spec, onDataPointClick]);

  if (renderError) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height,
          backgroundColor: "var(--bg-card)",
          border: "1px dashed var(--danger, #ef4444)",
          borderRadius: "0.5rem",
          color: "var(--text-muted)",
          padding: "1.5rem",
          textAlign: "center",
        }}
      >
        <p style={{ color: "var(--danger, #ef4444)", fontWeight: 600, marginBottom: "0.5rem" }}>
          Visualization Render Error
        </p>
        <p style={{ fontSize: "0.85rem" }}>{renderError}</p>
      </div>
    );
  }

  // Handle specialized KPI
  if (spec.chart_type === "kpi") {
    const kpiVal = spec.data && spec.data.length > 0 ? spec.data[0].value ?? 0 : 0;
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height,
          backgroundColor: "var(--bg-card)",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-subtle)",
          padding: "2rem",
        }}
      >
        <span style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
          {spec.title}
        </span>
        <span style={{ fontSize: "2.75rem", fontWeight: 700, color: "var(--brand-primary, #6366f1)" }}>
          {typeof kpiVal === "number" ? kpiVal.toLocaleString() : String(kpiVal)}
        </span>
        {spec.subtitle && (
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
            {spec.subtitle}
          </span>
        )}
      </div>
    );
  }

  // Handle Table View
  if (spec.chart_type === "table") {
    const tableData = spec.data || [];
    const columns = tableData.length > 0 ? Object.keys(tableData[0]) : [];
    return (
      <div
        style={{
          width: "100%",
          height,
          overflow: "auto",
          backgroundColor: "var(--bg-card)",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-subtle)",
          padding: "1rem",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
              {columns.map((col) => (
                <th key={col} style={{ padding: "0.5rem 0.75rem", color: "var(--text-secondary)" }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)", opacity: 0.9 }}>
                {columns.map((col) => (
                  <td key={col} style={{ padding: "0.5rem 0.75rem", color: "var(--text-primary)" }}>
                    {typeof row[col] === "number" ? row[col].toLocaleString() : String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Handle Tier 3 Deferred Specialized Charts
  const tier3Types = ["sankey", "radar", "candlestick", "choropleth"];
  if (tier3Types.includes(spec.chart_type as string)) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height,
          backgroundColor: "var(--bg-card)",
          borderRadius: "0.5rem",
          border: "1px dashed var(--border-subtle)",
          padding: "2rem",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>🧭</div>
        <span style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
          Tier 3 Specialized Chart (Deferred)
        </span>
        <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: "420px" }}>
          "{spec.chart_type}" is registered in AnalyzaX architecture, with its interactive renderer scheduled for Phase 10.
        </span>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        width: "100%",
        height,
        minHeight: 280,
      }}
    />
  );
}

/**
 * Maps our unified ChartSpec to an Apache ECharts configuration option.
 */
function buildEChartsOption(spec: ChartSpec): echarts.EChartsOption {
  const data = spec.data || [];
  const chartType = spec.chart_type || "bar";
  const axes = spec.axes || {};
  const legend = spec.legend || {};

  const baseTheme = {
    backgroundColor: "transparent",
    textStyle: {
      fontFamily: "inherit",
      color: "var(--text-secondary, #94a3b8)",
    },
    tooltip: {
      trigger: (chartType === "pie" || chartType === "donut" || chartType === "treemap" ? "item" : "axis") as "item" | "axis",
      backgroundColor: "rgba(15, 23, 42, 0.92)",
      borderColor: "rgba(255, 255, 255, 0.12)",
      textStyle: { color: "#f8fafc", fontSize: 12 },
      axisPointer: { type: "cross" as const, crossStyle: { color: "#64748b" } },
    },
    grid: {
      top: 45,
      bottom: axes.x_rotate ? 75 : 45,
      left: 60,
      right: 35,
      containLabel: true,
    },
    color: [
      "#6366f1",
      "#10b981",
      "#f59e0b",
      "#ec4899",
      "#06b6d4",
      "#8b5cf6",
      "#3b82f6",
      "#14b8a6",
      "#f97316",
    ],
  };

  // 1. Pie / Donut Chart
  if (chartType === "pie" || chartType === "donut") {
    const isDonut = chartType === "donut";
    return {
      ...baseTheme,
      legend: legend.show !== false ? { bottom: 10, textStyle: { color: "#94a3b8" } } : undefined,
      series: [
        {
          name: spec.title,
          type: "pie",
          radius: isDonut ? ["42%", "72%"] : "72%",
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: isDonut ? 6 : 2,
            borderColor: "#0f172a",
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: "{b}: {d}%",
            color: "#cbd5e1",
            fontSize: 11,
          },
          emphasis: {
            label: { show: true, fontSize: 13, fontWeight: "bold" },
          },
          data: data.map((d) => ({
            name: String(d.x ?? d.name ?? "Unknown"),
            value: Number(d.y ?? d.value ?? 0),
          })),
        },
      ],
    };
  }

  // 2. Treemap
  if (chartType === "treemap") {
    return {
      ...baseTheme,
      series: [
        {
          type: "treemap",
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          label: { show: true, formatter: "{b}\n{c}", fontSize: 11 },
          itemStyle: { borderColor: "#0f172a", borderWidth: 1, gapWidth: 2 },
          data: data.map((d) => ({
            name: String(d.x ?? "Unknown"),
            value: Number(d.y ?? 0),
          })),
        },
      ],
    };
  }

  // 3. Scatter / Bubble
  if (chartType === "scatter" || chartType === "bubble") {
    return {
      ...baseTheme,
      xAxis: {
        type: "value",
        name: axes.x_label || spec.x || "X",
        nameLocation: "middle",
        nameGap: 30,
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
        axisLabel: { color: "#94a3b8" },
      },
      yAxis: {
        type: "value",
        name: axes.y_label || spec.y || "Y",
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
        axisLabel: { color: "#94a3b8" },
      },
      series: [
        {
          type: "scatter",
          symbolSize: (val: any) => (chartType === "bubble" ? Math.min(Math.max((val[2] || 10) / 5, 8), 35) : 8),
          itemStyle: { opacity: 0.8, color: "#6366f1" },
          data: data.map((d) => [d.x, d.y, d.size || d.color]),
        },
      ],
    };
  }

  // 4. Heatmap
  if (chartType === "heatmap") {
    const xCategories = Array.from(new Set(data.map((d) => String(d.x))));
    const yCategories = Array.from(new Set(data.map((d) => String(d.y))));
    const maxVal = Math.max(...data.map((d) => Number(d.value || 0)), 1);

    return {
      ...baseTheme,
      xAxis: {
        type: "category",
        data: xCategories,
        splitArea: { show: true },
        axisLabel: { rotate: axes.x_rotate || 30, color: "#94a3b8" },
      },
      yAxis: {
        type: "category",
        data: yCategories,
        splitArea: { show: true },
        axisLabel: { color: "#94a3b8" },
      },
      visualMap: {
        min: 0,
        max: maxVal,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 0,
        inRange: { color: ["#1e1b4b", "#6366f1", "#ec4899"] },
        textStyle: { color: "#94a3b8" },
      },
      series: [
        {
          type: "heatmap",
          data: data.map((d) => [
            xCategories.indexOf(String(d.x)),
            yCategories.indexOf(String(d.y)),
            Number(d.value || 0),
          ]),
          label: { show: true, fontSize: 10, color: "#f8fafc" },
          itemStyle: { borderColor: "#0f172a", borderWidth: 1 },
        },
      ],
    };
  }

  // 5. Boxplot
  if (chartType === "box") {
    const categories = data.map((d) => String(d.x || "Overall"));
    const boxData = data.map((d) => [d.min, d.q1, d.median, d.q3, d.max]);

    return {
      ...baseTheme,
      xAxis: {
        type: "category",
        data: categories,
        axisLabel: { color: "#94a3b8", rotate: axes.x_rotate || 0 },
        splitLine: { show: false },
      },
      yAxis: {
        type: "value",
        name: axes.y_label || spec.y || "Value",
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
        axisLabel: { color: "#94a3b8" },
      },
      series: [
        {
          name: spec.title,
          type: "boxplot",
          data: boxData,
          itemStyle: {
            color: "rgba(99, 102, 241, 0.4)",
            borderColor: "#818cf8",
            borderWidth: 1.5,
          },
        },
      ],
    };
  }

  // 6. Standard Bar / Line / Area / Horizontal Bar
  const isHorizontal = chartType === "horizontal_bar";
  const isArea = chartType === "area" || chartType === "stacked_area";
  const isLine = chartType === "line" || chartType === "multi_line" || isArea;
  const isStacked = chartType === "stacked_bar" || chartType === "stacked_area";

  // Check if multiple series are present
  const hasSeries = Boolean(data.length > 0 && data[0].series !== undefined);

  if (hasSeries) {
    const seriesNames = Array.from(new Set(data.map((d) => String(d.series))));
    const categories = Array.from(new Set(data.map((d) => String(d.x))));

    const seriesList = seriesNames.map((sName) => {
      const seriesPoints = categories.map((cat) => {
        const match = data.find((d) => String(d.x) === cat && String(d.series) === sName);
        return match ? Number(match.y || 0) : 0;
      });

      return {
        name: sName,
        type: isLine ? ("line" as const) : ("bar" as const),
        stack: isStacked ? "total" : undefined,
        smooth: isLine,
        areaStyle: isArea ? { opacity: 0.25 } : undefined,
        data: seriesPoints,
      };
    });

    return {
      ...baseTheme,
      legend: { show: legend.show !== false, top: 0, textStyle: { color: "#94a3b8" } },
      xAxis: {
        type: isHorizontal ? "value" : "category",
        data: isHorizontal ? undefined : categories,
        axisLabel: { rotate: axes.x_rotate || 0, color: "#94a3b8" },
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
      },
      yAxis: {
        type: isHorizontal ? "category" : "value",
        data: isHorizontal ? categories : undefined,
        axisLabel: { color: "#94a3b8" },
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
      },
      series: seriesList,
    };
  }

  // Single series standard plot
  const xData = data.map((d) => String(d.x ?? ""));
  const yData = data.map((d) => Number(d.y ?? d.count ?? 0));

  const categoryAxis = {
    type: "category" as const,
    data: xData,
    axisLabel: {
      rotate: axes.x_rotate || (xData.length > 8 ? 30 : 0),
      color: "#94a3b8",
      fontSize: 11,
    },
    splitLine: { show: false },
  };

  const valueAxis = {
    type: "value" as const,
    name: axes.y_label || (spec.aggregation ? `${spec.y || ""} (${spec.aggregation})` : spec.y || ""),
    axisLabel: { color: "#94a3b8", fontSize: 11 },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
    min: axes.zero_baseline !== false ? 0 : undefined,
  };

  return {
    ...baseTheme,
    xAxis: isHorizontal ? valueAxis : categoryAxis,
    yAxis: isHorizontal ? categoryAxis : valueAxis,
    series: [
      {
        name: spec.title,
        type: isLine ? ("line" as const) : ("bar" as const),
        data: yData,
        smooth: isLine,
        areaStyle: isArea ? { opacity: 0.3 } : undefined,
        itemStyle: {
          borderRadius: !isLine ? (isHorizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]) : 0,
          color: "#6366f1",
        },
      },
    ],
  };
}
