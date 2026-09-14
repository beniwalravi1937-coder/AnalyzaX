import { createFileRoute } from "@tanstack/react-router";
import { DataQualityPage } from "./quality";

export const Route = createFileRoute("/data-quality")({
  head: () => ({
    meta: [
      { title: "Data Quality — AnalyzaX" },
      {
        name: "description",
        content:
          "Audit completeness, validity, uniqueness, and consistency across dataset versions.",
      },
      { property: "og:title", content: "Data Quality — AnalyzaX" },
    ],
  }),
  component: DataQualityPage,
});
