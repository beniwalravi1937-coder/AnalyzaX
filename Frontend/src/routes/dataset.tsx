import { createFileRoute } from "@tanstack/react-router";
import { DataPage } from "./data";

export const Route = createFileRoute("/dataset")({
  head: () => ({
    meta: [
      { title: "Dataset Inspector — AnalyzaX" },
      {
        name: "description",
        content:
          "Upload, inspect, and organize all your files in one place. Get instant summaries of columns, rows, and data health without writing code.",
      },
      { property: "og:title", content: "Dataset Inspector — AnalyzaX" },
    ],
  }),
  component: DataPage,
});
