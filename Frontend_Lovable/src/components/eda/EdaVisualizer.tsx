"use client";

import React, { useState } from "react";
import { ChartSpec } from "@/types";

interface EdaVisualizerProps {
  spec: ChartSpec;
  height?: number | string;
  onCellClick?: (x: string, y: string, value: number) => void;
}

export function EdaVisualizer({
  spec,
  height = 320,
  onCellClick,
}: EdaVisualizerProps) {
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    title: string;
    content: string;
  }>({ visible: false, x: 0, y: 0, title: "", content: "" });

  const chartType = spec.chart_type || (spec.type as any) || "bar";
  const data = spec.data || [];

  const handleMouseEnter = (
    e: React.MouseEvent,
    title: string,
    content: string
  ) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltip({
      visible: true,
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
      title,
      content,
    });
  };

  const handleMouseLeave = () => {
    setTooltip((prev) => ({ ...prev, visible: false }));
  };

  // 1. Histogram Renderer
  const renderHistogram = () => {
    if (!data.length) return <EmptyChartMessage msg="No histogram bins computed" />;
    const maxCount = Math.max(...data.map((d) => (d.count as number) || 0), 1);
    const svgWidth = 600;
    const svgHeight = 240;
    const padX = 45;
    const padY = 30;
    const chartW = svgWidth - padX * 2;
    const chartH = svgHeight - padY * 2;
    const barWidth = Math.max(chartW / data.length - 2, 2);

    return (
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: "100%", maxHeight: "260px" }}
        >
          <defs>
            <linearGradient id="histGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = padY + chartH * (1 - pct);
            return (
              <g key={i}>
                <line
                  x1={padX}
                  y1={y}
                  x2={svgWidth - padX}
                  y2={y}
                  stroke="rgba(255,255,255,0.06)"
                  strokeDasharray="3 3"
                />
                <text
                  x={padX - 8}
                  y={y + 3}
                  textAnchor="end"
                  fill="var(--text-muted)"
                  fontSize="10"
                >
                  {Math.round(maxCount * pct)}
                </text>
              </g>
            );
          })}

          {/* Bars */}
          {data.map((bin, i) => {
            const count = (bin.count as number) || 0;
            const barH = (count / maxCount) * chartH;
            const x = padX + i * (chartW / data.length);
            const y = padY + chartH - barH;
            const start = typeof bin.bin_start === "number" ? bin.bin_start.toFixed(2) : bin.bin_start;
            const end = typeof bin.bin_end === "number" ? bin.bin_end.toFixed(2) : bin.bin_end;
            const pct = typeof bin.percentage === "number" ? `${bin.percentage.toFixed(1)}%` : "";

            return (
              <rect
                key={i}
                x={x + 1}
                y={y}
                width={barWidth}
                height={barH}
                fill="url(#histGrad)"
                rx="2"
                style={{ cursor: "pointer", transition: "opacity 0.2s" }}
                onMouseEnter={(e) =>
                  handleMouseEnter(
                    e,
                    `Range: [${start} — ${end}]`,
                    `Count: ${count.toLocaleString()} (${pct})`
                  )
                }
                onMouseLeave={handleMouseLeave}
              />
            );
          })}

          {/* X Axis */}
          <line
            x1={padX}
            y1={padY + chartH}
            x2={svgWidth - padX}
            y2={padY + chartH}
            stroke="var(--border-subtle)"
          />
          {data.length > 0 && (
            <>
              <text
                x={padX}
                y={svgHeight - 8}
                fill="var(--text-muted)"
                fontSize="10"
              >
                {typeof data[0].bin_start === "number"
                  ? (data[0].bin_start as number).toFixed(1)
                  : String(data[0].bin_start ?? "")}
              </text>
              <text
                x={svgWidth - padX}
                y={svgHeight - 8}
                textAnchor="end"
                fill="var(--text-muted)"
                fontSize="10"
              >
                {typeof data[data.length - 1].bin_end === "number"
                  ? (data[data.length - 1].bin_end as number).toFixed(1)
                  : String(data[data.length - 1].bin_end ?? "")}
              </text>
            </>
          )}
        </svg>
      </div>
    );
  };

  // 2. Box Plot Renderer
  const renderBoxPlot = () => {
    if (!data.length) return <EmptyChartMessage msg="No boxplot data computed" />;
    const box = data[0];
    const min = (box.min as number) ?? 0;
    const q1 = (box.q1 as number) ?? 0;
    const median = (box.median as number) ?? 0;
    const q3 = (box.q3 as number) ?? 0;
    const max = (box.max as number) ?? 0;
    const outliers = (box.outlier_points as number[]) || [];

    const allVals = [min, q1, median, q3, max, ...outliers];
    const domainMin = Math.min(...allVals);
    const domainMax = Math.max(...allVals);
    const range = domainMax - domainMin || 1;

    const svgWidth = 560;
    const svgHeight = 160;
    const padX = 50;
    const chartW = svgWidth - padX * 2;
    const centerY = svgHeight / 2;

    const scaleX = (val: number) => padX + ((val - domainMin) / range) * chartW;

    return (
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: "100%", maxHeight: "180px" }}
        >
          {/* Whiskers line */}
          <line
            x1={scaleX(min)}
            y1={centerY}
            x2={scaleX(max)}
            y2={centerY}
            stroke="var(--border-strong, #64748b)"
            strokeWidth="2"
          />

          {/* Min cap */}
          <line
            x1={scaleX(min)}
            y1={centerY - 16}
            x2={scaleX(min)}
            y2={centerY + 16}
            stroke="#94a3b8"
            strokeWidth="2"
          />

          {/* Max cap */}
          <line
            x1={scaleX(max)}
            y1={centerY - 16}
            x2={scaleX(max)}
            y2={centerY + 16}
            stroke="#94a3b8"
            strokeWidth="2"
          />

          {/* IQR Box */}
          <rect
            x={scaleX(q1)}
            y={centerY - 32}
            width={Math.max(scaleX(q3) - scaleX(q1), 2)}
            height={64}
            fill="rgba(99, 102, 241, 0.25)"
            stroke="#818cf8"
            strokeWidth="2"
            rx="4"
            style={{ cursor: "pointer" }}
            onMouseEnter={(e) =>
              handleMouseEnter(
                e,
                "Interquartile Range (IQR)",
                `Q1: ${q1.toFixed(2)} | Q3: ${q3.toFixed(2)} | IQR: ${(q3 - q1).toFixed(2)}`
              )
            }
            onMouseLeave={handleMouseLeave}
          />

          {/* Median line */}
          <line
            x1={scaleX(median)}
            y1={centerY - 32}
            x2={scaleX(median)}
            y2={centerY + 32}
            stroke="#38bdf8"
            strokeWidth="3"
            style={{ cursor: "pointer" }}
            onMouseEnter={(e) =>
              handleMouseEnter(
                e,
                "Median (Q2)",
                `Value: ${median.toFixed(2)}`
              )
            }
            onMouseLeave={handleMouseLeave}
          />

          {/* Outliers dots */}
          {outliers.map((pt, i) => (
            <circle
              key={i}
              cx={scaleX(pt)}
              cy={centerY}
              r="3.5"
              fill="#f43f5e"
              stroke="#fff"
              strokeWidth="1"
              style={{ cursor: "pointer" }}
              onMouseEnter={(e) =>
                handleMouseEnter(
                  e,
                  "Statistical Outlier",
                  `Value: ${pt.toFixed(2)} (outside 1.5×IQR fences)`
                )
              }
              onMouseLeave={handleMouseLeave}
            />
          ))}

          {/* Value labels */}
          <text x={scaleX(min)} y={centerY + 36} fontSize="10" fill="var(--text-muted)" textAnchor="middle">
            {min.toFixed(1)}
          </text>
          <text x={scaleX(median)} y={centerY - 38} fontSize="11" fill="#38bdf8" fontWeight="bold" textAnchor="middle">
            {median.toFixed(1)}
          </text>
          <text x={scaleX(max)} y={centerY + 36} fontSize="10" fill="var(--text-muted)" textAnchor="middle">
            {max.toFixed(1)}
          </text>
        </svg>
      </div>
    );
  };

  // 3. Bar Chart Renderer (Categorical frequencies / Missingness)
  const renderBarChart = () => {
    if (!data.length) return <EmptyChartMessage msg="No category data computed" />;
    const maxVal = Math.max(
      ...data.map((d) => (d.count as number) ?? (d.missing_percentage as number) ?? 0),
      1
    );

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", padding: "0.5rem 0" }}>
        {data.slice(0, 15).map((item, i) => {
          const label = String(item.category ?? item.column ?? `Item ${i}`);
          const count = (item.count as number) ?? (item.missing_count as number) ?? 0;
          const pct =
            (item.percentage as number) ??
            (item.missing_percentage as number) ??
            (count / maxVal) * 100;
          const barWidthPct = Math.min(Math.max((pct / (item.missing_percentage !== undefined ? 100 : (maxVal > 100 ? maxVal : 100))) * 100, 2), 100);

          return (
            <div
              key={i}
              style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.8125rem" }}
              onMouseEnter={(e) =>
                handleMouseEnter(e, label, `Value: ${count.toLocaleString()} (${pct.toFixed(1)}%)`)
              }
              onMouseLeave={handleMouseLeave}
            >
              <span
                style={{
                  width: "120px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  color: "var(--text-secondary)",
                  textAlign: "right",
                  flexShrink: 0,
                }}
                title={label}
              >
                {label}
              </span>
              <div
                style={{
                  flex: 1,
                  height: "20px",
                  backgroundColor: "rgba(255,255,255,0.04)",
                  borderRadius: "4px",
                  overflow: "hidden",
                  position: "relative",
                }}
              >
                <div
                  style={{
                    width: `${barWidthPct}%`,
                    height: "100%",
                    background: "linear-gradient(90deg, #6366f1 0%, #a855f7 100%)",
                    borderRadius: "4px",
                    transition: "width 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                />
              </div>
              <span
                style={{
                  width: "70px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                  textAlign: "right",
                  flexShrink: 0,
                }}
              >
                {count > 0 ? count.toLocaleString() : `${pct.toFixed(1)}%`}
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  // 4. Line Chart Renderer (Time Series)
  const renderLineChart = () => {
    if (!data.length) return <EmptyChartMessage msg="No time series points" />;
    const maxVal = Math.max(...data.map((d) => (d.count as number) || 0), 1);
    const svgWidth = 600;
    const svgHeight = 220;
    const padX = 40;
    const padY = 25;
    const chartW = svgWidth - padX * 2;
    const chartH = svgHeight - padY * 2;

    const points = data.map((d, i) => {
      const x = padX + (i / Math.max(data.length - 1, 1)) * chartW;
      const y = padY + chartH - (((d.count as number) || 0) / maxVal) * chartH;
      return { x, y, raw: d };
    });

    const polylinePts = points.map((p) => `${p.x},${p.y}`).join(" ");
    const areaPts = `${points[0].x},${padY + chartH} ` + polylinePts + ` ${points[points.length - 1].x},${padY + chartH}`;

    return (
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: "100%", maxHeight: "240px" }}
        >
          <defs>
            <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Area under curve */}
          <polygon points={areaPts} fill="url(#lineGrad)" />

          {/* Polyline */}
          <polyline
            points={polylinePts}
            fill="none"
            stroke="#06b6d4"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Interactive points */}
          {points.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="3.5"
              fill="#0891b2"
              stroke="#cffafe"
              strokeWidth="1.5"
              style={{ cursor: "pointer" }}
              onMouseEnter={(e) =>
                handleMouseEnter(
                  e,
                  String(p.raw.timestamp || p.raw.period || `Step ${i}`),
                  `Count: ${(p.raw.count as number)?.toLocaleString() || 0}`
                )
              }
              onMouseLeave={handleMouseLeave}
            />
          ))}

          {/* Labels */}
          {data.length > 0 && (
            <>
              <text x={padX} y={svgHeight - 6} fontSize="10" fill="var(--text-muted)">
                {String(data[0].timestamp || data[0].period || "")}
              </text>
              <text x={svgWidth - padX} y={svgHeight - 6} fontSize="10" fill="var(--text-muted)" textAnchor="end">
                {String(data[data.length - 1].timestamp || data[data.length - 1].period || "")}
              </text>
            </>
          )}
        </svg>
      </div>
    );
  };

  // 5. Scatter Plot Renderer (Numeric vs Numeric)
  const renderScatter = () => {
    if (!data.length) return <EmptyChartMessage msg="No coordinate data" />;
    const xs = data.map((d) => (d.x as number) || 0);
    const ys = data.map((d) => (d.y as number) || 0);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;

    const svgWidth = 560;
    const svgHeight = 240;
    const pad = 40;
    const chartW = svgWidth - pad * 2;
    const chartH = svgHeight - pad * 2;

    const scaleX = (val: number) => pad + ((val - minX) / rangeX) * chartW;
    const scaleY = (val: number) => pad + chartH - ((val - minY) / rangeY) * chartH;

    return (
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: "100%", maxHeight: "260px" }}
        >
          {/* Grid lines */}
          <line x1={pad} y1={pad + chartH} x2={pad + chartW} y2={pad + chartH} stroke="var(--border-subtle)" />
          <line x1={pad} y1={pad} x2={pad} y2={pad + chartH} stroke="var(--border-subtle)" />

          {/* Points */}
          {data.map((pt, i) => {
            const px = scaleX((pt.x as number) || 0);
            const py = scaleY((pt.y as number) || 0);
            return (
              <circle
                key={i}
                cx={px}
                cy={py}
                r="3"
                fill="rgba(99, 102, 241, 0.7)"
                stroke="#c7d2fe"
                strokeWidth="0.5"
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) =>
                  handleMouseEnter(
                    e,
                    `Point #${i + 1}`,
                    `X: ${((pt.x as number) || 0).toFixed(2)} | Y: ${((pt.y as number) || 0).toFixed(2)}`
                  )
                }
                onMouseLeave={handleMouseLeave}
              />
            );
          })}

          {/* Axis Labels */}
          <text x={pad} y={svgHeight - 8} fontSize="10" fill="var(--text-muted)">
            {minX.toFixed(1)}
          </text>
          <text x={pad + chartW} y={svgHeight - 8} fontSize="10" fill="var(--text-muted)" textAnchor="end">
            {maxX.toFixed(1)}
          </text>
          <text x={pad - 6} y={pad + chartH} fontSize="10" fill="var(--text-muted)" textAnchor="end">
            {minY.toFixed(1)}
          </text>
          <text x={pad - 6} y={pad + 10} fontSize="10" fill="var(--text-muted)" textAnchor="end">
            {maxY.toFixed(1)}
          </text>
        </svg>
      </div>
    );
  };

  // 6. Correlation Heatmap Renderer
  const renderHeatmap = () => {
    if (!data.length) return <EmptyChartMessage msg="No correlation matrix computed" />;
    // Extract unique labels
    const labelsSet = new Set<string>();
    data.forEach((d) => {
      if (d.x) labelsSet.add(String(d.x));
      if (d.y) labelsSet.add(String(d.y));
    });
    const labels = Array.from(labelsSet);
    const n = labels.length;
    if (n === 0) return <EmptyChartMessage msg="No correlation labels found" />;

    const matrixMap = new Map<string, number>();
    data.forEach((d) => {
      matrixMap.set(`${d.x}__${d.y}`, (d.value as number) ?? 0);
    });

    const getCorrColor = (val: number) => {
      if (val >= 0.8) return "rgba(16, 185, 129, 0.85)"; // strong positive
      if (val >= 0.4) return "rgba(16, 185, 129, 0.5)";
      if (val >= 0.1) return "rgba(16, 185, 129, 0.25)";
      if (val > -0.1) return "rgba(255, 255, 255, 0.05)"; // neutral
      if (val > -0.4) return "rgba(244, 63, 94, 0.25)";
      if (val > -0.8) return "rgba(244, 63, 94, 0.5)";
      return "rgba(244, 63, 94, 0.85)"; // strong negative
    };

    return (
      <div style={{ width: "100%", overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "separate",
            borderSpacing: "3px",
            fontSize: "0.75rem",
          }}
        >
          <thead>
            <tr>
              <th style={{ padding: "6px" }}></th>
              {labels.map((col) => (
                <th
                  key={col}
                  style={{
                    padding: "6px",
                    color: "var(--text-muted)",
                    maxWidth: "70px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    transform: "rotate(-30deg)",
                    transformOrigin: "bottom left",
                  }}
                  title={col}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {labels.map((rowCol) => (
              <tr key={rowCol}>
                <td
                  style={{
                    padding: "6px 8px",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    textAlign: "right",
                    maxWidth: "90px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={rowCol}
                >
                  {rowCol}
                </td>
                {labels.map((colCol) => {
                  const val = matrixMap.get(`${rowCol}__${colCol}`) ?? 0;
                  const bg = getCorrColor(val);
                  return (
                    <td
                      key={colCol}
                      onClick={() => onCellClick && onCellClick(rowCol, colCol, val)}
                      onMouseEnter={(e) =>
                        handleMouseEnter(
                          e,
                          `${rowCol} vs ${colCol}`,
                          `Correlation: ${val > 0 ? "+" : ""}${val.toFixed(3)}`
                        )
                      }
                      onMouseLeave={handleMouseLeave}
                      style={{
                        backgroundColor: bg,
                        color: Math.abs(val) > 0.4 ? "#fff" : "var(--text-secondary)",
                        textAlign: "center",
                        padding: "8px 4px",
                        borderRadius: "4px",
                        cursor: onCellClick ? "pointer" : "default",
                        transition: "transform 0.15s ease",
                        fontWeight: Math.abs(val) > 0.5 ? 600 : 400,
                      }}
                    >
                      {val.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div
      style={{
        width: "100%",
        minHeight: typeof height === "number" ? `${height}px` : height,
        display: "flex",
        flexDirection: "column",
        position: "relative",
      }}
    >
      {/* Sampling badge if applicable */}
      {spec.sampling && spec.sampling.is_sampled && (
        <div
          style={{
            fontSize: "0.6875rem",
            color: "#f59e0b",
            backgroundColor: "rgba(245, 158, 11, 0.08)",
            padding: "3px 8px",
            borderRadius: "4px",
            marginBottom: "0.5rem",
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            alignSelf: "flex-start",
          }}
        >
          <span>⚡</span>
          <span>
            Sampled ({(spec.sampling.displayed_points ?? spec.sampling.sample_size ?? 0).toLocaleString()} of{" "}
            {spec.sampling.original_row_count.toLocaleString()} rows displayed)
          </span>
        </div>
      )}

      {/* Chart content */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {chartType === "histogram" && renderHistogram()}
        {chartType === "box" && renderBoxPlot()}
        {chartType === "bar" && renderBarChart()}
        {chartType === "line" && renderLineChart()}
        {chartType === "scatter" && renderScatter()}
        {chartType === "heatmap" && renderHeatmap()}
        {chartType !== "histogram" &&
          chartType !== "box" &&
          chartType !== "bar" &&
          chartType !== "line" &&
          chartType !== "scatter" &&
          chartType !== "heatmap" &&
          renderBarChart()}
      </div>

      {/* Hover Floating Tooltip */}
      {tooltip.visible && (
        <div
          style={{
            position: "fixed",
            left: `${tooltip.x}px`,
            top: `${tooltip.y}px`,
            transform: "translate(-50%, -100%)",
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            backdropFilter: "blur(8px)",
            border: "1px solid var(--border-subtle, #334155)",
            borderRadius: "6px",
            padding: "6px 10px",
            pointerEvents: "none",
            zIndex: 9999,
            boxShadow: "0 4px 14px rgba(0, 0, 0, 0.35)",
            whiteSpace: "nowrap",
          }}
        >
          <div style={{ fontWeight: 600, fontSize: "0.75rem", color: "#f8fafc" }}>
            {tooltip.title}
          </div>
          <div style={{ fontSize: "0.6875rem", color: "#94a3b8", marginTop: "2px" }}>
            {tooltip.content}
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyChartMessage({ msg }: { msg: string }) {
  return (
    <div
      style={{
        padding: "2rem",
        textAlign: "center",
        color: "var(--text-muted)",
        fontSize: "0.8125rem",
      }}
    >
      {msg}
    </div>
  );
}
