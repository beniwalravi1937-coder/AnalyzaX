import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { ForecastingWorkspace } from "@/components/forecasting/ForecastingWorkspace";

export const Route = createFileRoute("/forecasting")({
  head: () => ({
    meta: [
      { title: "Trend Forecasting & Projections — AnalyzaX" },
      {
        name: "description",
        content:
          "Project future revenue, demand, and growth trends with automated time-series forecasting. See clear confidence bands and future estimates in seconds.",
      },
      { property: "og:title", content: "Trend Forecasting & Projections — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Project future revenue, demand, and growth trends with automated time-series forecasting.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-forecasting.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-forecasting.png" },
    ],
  }),
  component: ForecastingPage,
});

function ForecastingPage() {
  return (
    <div className="ax-stack">
      <PageHeader
        title="Forecasting & Time-Series Intelligence"
        description="Deterministic, version-aware temporal forecasting. Automatic frequency detection, rolling-origin backtesting, 8 statistical estimators, prediction intervals, and leakage-free out-of-sample projections."
        badge={{ text: "Phase 12 — Time-Series Intelligence", variant: "indigo" }}
      />

      <div style={{ marginTop: "1rem" }}>
        <ForecastingWorkspace />
      </div>
    </div>
  );
}
