"use client";

import React from "react";
import { ComponentDataResponse } from "@/types/dashboard";

interface NarrativeWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function NarrativeWidget({ dataResp, configuration }: NarrativeWidgetProps) {
  const content = (dataResp?.data?.content || configuration.content || "Add your narrative here...").trim();

  // Simple, safe Markdown heading and paragraph formatter
  const lines = content.split("\n");

  return (
    <div style={{ color: "#e2e8f0", fontSize: "0.875rem", lineHeight: 1.6, overflow: "auto", height: "100%" }}>
      {lines.map((line: string, idx: number) => {
        const trimmed = line.trim();
        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={idx} style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginTop: "0.5rem", marginBottom: "0.25rem" }}>
              {trimmed.slice(4)}
            </h3>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h2 key={idx} style={{ fontSize: "1.25rem", fontWeight: 700, color: "#ffffff", marginTop: "0.75rem", marginBottom: "0.25rem" }}>
              {trimmed.slice(3)}
            </h2>
          );
        }
        if (trimmed.startsWith("# ")) {
          return (
            <h1 key={idx} style={{ fontSize: "1.5rem", fontWeight: 800, color: "#ffffff", marginTop: "1rem", marginBottom: "0.5rem" }}>
              {trimmed.slice(2)}
            </h1>
          );
        }
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          return (
            <li key={idx} style={{ marginLeft: "1.25rem", color: "#cbd5e1", marginBottom: "0.2rem" }}>
              {trimmed.slice(2)}
            </li>
          );
        }
        if (!trimmed) {
          return <div key={idx} style={{ height: "0.5rem" }} />;
        }
        return (
          <p key={idx} style={{ margin: "0 0 0.4rem 0", color: "#cbd5e1" }}>
            {trimmed}
          </p>
        );
      })}
    </div>
  );
}
