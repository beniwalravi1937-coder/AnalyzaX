import { createFileRoute } from "@tanstack/react-router";
import React, { useState } from "react";
import { HomeDashboard } from "@/components/dashboard/HomeDashboard";
import { DashboardWorkspace } from "@/components/dashboard/DashboardWorkspace";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — AnalyzaX" },
      {
        name: "description",
        content:
          "Your analytics workspace. Explore real-time KPIs, data health diagnostics, deterministic insights, ChartSpec visualizations, and recommended next steps.",
      },
      { property: "og:title", content: "Dashboard — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Your analytics workspace. Explore real-time KPIs, data health diagnostics, deterministic insights, and ChartSpec visualizations.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
    ],
  }),
  component: DashboardRouteComponent,
});

function DashboardRouteComponent() {
  const [selectedDashboardId, setSelectedDashboardId] = useState<string | null>(null);

  if (selectedDashboardId) {
    return (
      <DashboardWorkspace
        dashboardId={selectedDashboardId}
        onBackToList={() => setSelectedDashboardId(null)}
      />
    );
  }

  return <HomeDashboard onOpenCustomDashboard={(id) => setSelectedDashboardId(id)} />;
}
