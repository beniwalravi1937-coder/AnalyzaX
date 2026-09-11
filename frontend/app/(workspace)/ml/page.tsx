"use client";

import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { MLWorkspace } from "@/components/ml/MLWorkspace";

export default function MachineLearningPage() {
  return (
    <div>
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
