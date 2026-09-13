import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { MLWorkspace } from "@/components/ml/MLWorkspace";

export const Route = createFileRoute("/ml")({
  head: () => ({
    meta: [
      { title: "Predictive Machine Learning — AnalyzaX" },
      {
        name: "description",
        content:
          "Train predictive AI models to forecast outcomes, classify customer churn, and score leads in one click — with zero machine learning coding needed.",
      },
      { property: "og:title", content: "Predictive Machine Learning — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Train predictive models to forecast outcomes, classify churn, and score leads with zero code needed.",
      },
    ],
  }),
  component: MachineLearningPage,
});

function MachineLearningPage() {
  return (
    <div className="ax-stack">
      <PageHeader
        title="Machine Learning Studio & Workspace"
        description="Deterministic, version-aware machine learning powered by scikit-learn. Automated suitability diagnostics, leakage-free preprocessing, multi-model evaluation, and live inference."
        badge={{ text: "Phase 11 — Production ML", variant: "indigo" }}
      />

      <div style={{ marginTop: "1rem" }}>
        <MLWorkspace />
      </div>
    </div>
  );
}
