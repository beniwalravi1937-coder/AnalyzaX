import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatisticsWorkspace } from "@/components/statistics/StatisticsWorkspace";

export const Route = createFileRoute("/statistics")({
  head: () => ({
    meta: [
      { title: "Statistical Intelligence Engine — AnalyzaX" },
      {
        name: "description",
        content:
          "Rigorous hypothesis testing, parametric and non-parametric tests, descriptive metrics, effect sizes, confidence intervals, and regression diagnostics calculated deterministically with SciPy and statsmodels.",
      },
      { property: "og:title", content: "Statistical Intelligence Engine — AnalyzaX" },
      {
        property: "og:description",
        content: "Deterministic hypothesis testing and statistical diagnostics powered by SciPy and statsmodels.",
      },
    ],
  }),
  component: StatisticsPage,
});

function StatisticsPage() {
  return (
    <div className="ax-stack">
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
