"use client";

import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { ForecastingWorkspace } from "@/components/forecasting/ForecastingWorkspace";

export default function ForecastingPage() {
  return (
    <div>
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
