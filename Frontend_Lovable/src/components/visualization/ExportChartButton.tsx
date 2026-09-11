"use client";

import React, { useState, useRef, useEffect } from "react";
import { DownloadIcon } from "@/components/icons";

interface ExportChartButtonProps {
  onExportPng: () => void;
  onExportCsv: () => void;
  onExportJson?: () => void;
  disabled?: boolean;
}

export function ExportChartButton({
  onExportPng,
  onExportCsv,
  onExportJson,
  disabled,
}: ExportChartButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} style={{ position: "relative", display: "inline-block" }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className="btn btn-secondary btn-sm"
        style={{
          fontSize: "0.75rem",
          padding: "0.25rem 0.6rem",
          display: "flex",
          alignItems: "center",
          gap: "0.3rem",
        }}
        title="Export options"
      >
        <DownloadIcon size={13} />
        Export
        <span style={{ fontSize: "0.65rem", marginLeft: "0.15rem" }}>▼</span>
      </button>

      {isOpen && (
        <div
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 4px)",
            backgroundColor: "var(--bg-surface, #1e293b)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.375rem",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.4)",
            zIndex: 50,
            minWidth: "150px",
            padding: "0.25rem 0",
          }}
        >
          <button
            onClick={() => {
              setIsOpen(false);
              onExportPng();
            }}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              padding: "0.4rem 0.75rem",
              fontSize: "0.75rem",
              background: "none",
              border: "none",
              color: "var(--text-primary)",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.05)")}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
          >
            🖼 Export as PNG Image
          </button>

          <button
            onClick={() => {
              setIsOpen(false);
              onExportCsv();
            }}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              padding: "0.4rem 0.75rem",
              fontSize: "0.75rem",
              background: "none",
              border: "none",
              color: "var(--text-primary)",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.05)")}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
          >
            📊 Export Data as CSV
          </button>

          {onExportJson && (
            <button
              onClick={() => {
                setIsOpen(false);
                onExportJson();
              }}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "0.4rem 0.75rem",
                fontSize: "0.75rem",
                background: "none",
                border: "none",
                color: "var(--text-primary)",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.05)")}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
            >
              📄 Export Spec as JSON
            </button>
          )}
        </div>
      )}
    </div>
  );
}
