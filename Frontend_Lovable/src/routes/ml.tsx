import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { MLWorkspace } from "@/components/ml/MLWorkspace";

export const Route = createFileRoute("/ml")({
  head: () => ({
    meta: [
      { title: "Machine Learning Studio & Workspace — AnalyzaX" },
      {
        name: "description",
        content:
          "Deterministic, version-aware machine learning powered by scikit-learn. Automated suitability diagnostics, leakage-free preprocessing, multi-model evaluation, and live inference.",
      },
      { property: "og:title", content: "Machine Learning Studio & Workspace — AnalyzaX" },
      {
        property: "og:description",
        content: "Deterministic machine learning studio powered by scikit-learn.",
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
