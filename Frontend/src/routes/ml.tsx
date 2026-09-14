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
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-ml.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-ml.png" },
    ],
  }),
  component: MachineLearningPage,
});

function MachineLearningPage() {
  return (
    <div className="flex flex-col min-h-[calc(100vh-100px)]">
      <MLWorkspace />
    </div>
  );
}
