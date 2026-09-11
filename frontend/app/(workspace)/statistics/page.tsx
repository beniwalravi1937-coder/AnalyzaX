"use client";

import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatisticsWorkspace } from "@/components/statistics/StatisticsWorkspace";

export default function StatisticsPage() {
  return (
    <div>
      <PageHeader
        title="Statistical Intelligence Engine"
        description="Rigorous hypothesis testing, parametric and non-parametric tests, descriptive metrics, effect sizes, confidence intervals, and regression diagnostics calculated deterministically with SciPy and statsmodels."
        badge={{ text: "Phase 10 — Advanced Statistics", variant: "indigo" }}
      />

      <div style={{ marginTop: "1rem" }}>
        <StatisticsWorkspace />
      </div>
    </div>
  );
}

