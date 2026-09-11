"use client";

import React, { useState } from "react";

interface ChartImageExportProps {
  elementId?: string;
  chartTitle?: string;
  onExportComplete?: (format: "png" | "svg") => void;
}

export function ChartImageExport({
  elementId,
  chartTitle = "chart_export",
  onExportComplete,
}: ChartImageExportProps) {
  const [scale, setScale] = useState<number>(2);
  const [isExporting, setIsExporting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const exportSvg = () => {
    setIsExporting(true);
    setStatusMessage(null);
    try {
      const container = elementId
        ? document.getElementById(elementId)
        : document.querySelector(".recharts-wrapper, svg");

      if (!container) {
        throw new Error("No chart SVG element found on page to export.");
      }

      const svgEl = container.tagName.toLowerCase() === "svg"
        ? (container as SVGSVGElement)
        : container.querySelector("svg");

      if (!svgEl) {
        throw new Error("Could not find SVG inside the chart container.");
      }

      const serializer = new XMLSerializer();
      let source = serializer.serializeToString(svgEl);

      // Ensure xmlns
      if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
      }

      const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${chartTitle.toLowerCase().replace(/\s+/g, "_")}.svg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setStatusMessage("SVG exported successfully!");
      if (onExportComplete) onExportComplete("svg");
    } catch (err: unknown) {
      setStatusMessage(err instanceof Error ? err.message : "SVG export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const exportPng = () => {
    setIsExporting(true);
    setStatusMessage(null);
    try {
      const container = elementId
        ? document.getElementById(elementId)
        : document.querySelector(".recharts-wrapper, svg");

      if (!container) {
        throw new Error("No chart SVG element found on page to export.");
      }

      const svgEl = container.tagName.toLowerCase() === "svg"
        ? (container as SVGSVGElement)
        : container.querySelector("svg");

      if (!svgEl) {
        throw new Error("Could not find SVG inside the chart container.");
      }

      const serializer = new XMLSerializer();
      const svgString = serializer.serializeToString(svgEl);
      const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
      const URLObj = window.URL || window.webkitURL || window;
      const blobURL = URLObj.createObjectURL(svgBlob);

      const image = new Image();
      image.onload = () => {
        const canvas = document.createElement("canvas");
        const bbox = svgEl.getBoundingClientRect();
        const width = bbox.width || 800;
        const height = bbox.height || 450;

        canvas.width = width * scale;
        canvas.height = height * scale;

        const ctx = canvas.getContext("2d");
        if (!ctx) {
          setStatusMessage("Could not create 2D canvas context");
          setIsExporting(false);
          return;
        }

        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

        const pngUrl = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.href = pngUrl;
        link.download = `${chartTitle.toLowerCase().replace(/\s+/g, "_")}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URLObj.revokeObjectURL(blobURL);

        setStatusMessage(`PNG exported at ${scale}x resolution!`);
        if (onExportComplete) onExportComplete("png");
        setIsExporting(false);
      };

      image.onerror = () => {
        setStatusMessage("Failed to render SVG onto canvas");
        setIsExporting(false);
      };

      image.src = blobURL;
    } catch (err: unknown) {
      setStatusMessage(err instanceof Error ? err.message : "PNG export failed");
      setIsExporting(false);
    }
  };

  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        padding: "1.25rem",
      }}
    >
      <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)" }}>
        🖼️ Chart Image & Vector Export
      </h3>
      <p style={{ margin: "0 0 1rem 0", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
        Export active visualization as high-resolution PNG or lossless vector SVG for slides and publications.
      </p>

      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <label style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>Resolution:</label>
          <select
            value={scale}
            onChange={(e) => setScale(Number(e.target.value))}
            style={{
              padding: "0.3rem 0.6rem",
              borderRadius: "0.375rem",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-surface)",
              color: "var(--text-primary)",
              fontSize: "0.8125rem",
            }}
          >
            <option value={1}>1x (Standard)</option>
            <option value={2}>2x (High DPI / Retina)</option>
            <option value={3}>3x (Print 300 DPI)</option>
          </select>
        </div>

        <button
          onClick={exportPng}
          disabled={isExporting}
          className="btn btn-primary btn-sm"
          style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}
        >
          {isExporting ? "Rendering..." : "⬇ Export PNG"}
        </button>

        <button
          onClick={exportSvg}
          disabled={isExporting}
          className="btn btn-secondary btn-sm"
          style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}
        >
          {isExporting ? "Extracting..." : "⬇ Export Vector SVG"}
        </button>
      </div>

      {statusMessage && (
        <div
          style={{
            fontSize: "0.8125rem",
            padding: "0.5rem 0.75rem",
            borderRadius: "0.375rem",
            background: statusMessage.includes("fail") || statusMessage.includes("error")
              ? "rgba(239, 68, 68, 0.1)"
              : "rgba(16, 185, 129, 0.1)",
            color: statusMessage.includes("fail") || statusMessage.includes("error")
              ? "#ef4444"
              : "#10b981",
          }}
        >
          {statusMessage}
        </div>
      )}
    </div>
  );
}
