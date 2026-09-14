import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatisticsWorkspace } from "@/components/statistics/StatisticsWorkspace";

export const Route = createFileRoute("/statistics")({
  head: () => ({
    meta: [
      { title: "Statistical Testing & Analysis — AnalyzaX" },
      {
        name: "description",
        content:
          "Run rigorous statistical tests, compare group differences, and check significance levels with automated explanations anyone on your team can understand.",
      },
      { property: "og:title", content: "Statistical Testing & Analysis — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Run statistical tests and compare group differences with automated explanations anyone can understand.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-statistics.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-statistics.png" },
    ],
  }),
  component: StatisticsPage,
});

function StatisticsPage() {
  return (
    <div className="flex flex-col min-h-[calc(100vh-100px)]">
      <StatisticsWorkspace />
    </div>
  );
}
