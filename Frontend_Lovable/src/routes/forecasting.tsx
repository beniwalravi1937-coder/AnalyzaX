import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { ForecastingWorkspace } from "@/components/forecasting/ForecastingWorkspace";

export const Route = createFileRoute("/forecasting")({
  head: () => ({
    meta: [
      { title: "Forecasting & Time-Series Intelligence — AnalyzaX" },
      {
        name: "description",
        content:
          "Deterministic, version-aware temporal forecasting. Automatic frequency detection, rolling-origin backtesting, 8 statistical estimators, prediction intervals, and leakage-free out-of-sample projections.",
      },
      { property: "og:title", content: "Forecasting & Time-Series Intelligence — AnalyzaX" },
      {
        property: "og:description",
        content: "Deterministic time-series forecasting powered by statsmodels.",
      },
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
