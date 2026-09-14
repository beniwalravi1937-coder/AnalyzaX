import { createFileRoute } from "@tanstack/react-router";
import type {} from "@tanstack/react-start";

const BASE_URL = process.env.SITE_URL || "https://analyzaxab-vp.vercel.app";

interface SitemapEntry {
  path: string;
  lastmod?: string;
  changefreq?: "always" | "hourly" | "daily" | "weekly" | "monthly" | "yearly" | "never";
  priority?: string;
}

export const Route = createFileRoute("/sitemap.xml")({
  server: {
    handlers: {
      GET: async () => {
        const entries: SitemapEntry[] = [
          { path: "/", changefreq: "weekly", priority: "1.0" },
          { path: "/data", changefreq: "weekly", priority: "0.8" },
          { path: "/cleaning", changefreq: "weekly", priority: "0.7" },
          { path: "/visualizations", changefreq: "weekly", priority: "0.7" },
          { path: "/ai-analyst", changefreq: "weekly", priority: "0.7" },
          { path: "/insights", changefreq: "weekly", priority: "0.8" },
          { path: "/sql", changefreq: "weekly", priority: "0.7" },
          { path: "/eda", changefreq: "weekly", priority: "0.7" },
          { path: "/statistics", changefreq: "weekly", priority: "0.7" },
          { path: "/ml", changefreq: "weekly", priority: "0.7" },
          { path: "/forecasting", changefreq: "weekly", priority: "0.7" },
          { path: "/metrics", changefreq: "weekly", priority: "0.6" },
          { path: "/exports", changefreq: "weekly", priority: "0.6" },
          { path: "/quality", changefreq: "weekly", priority: "0.8" },
          { path: "/projects", changefreq: "weekly", priority: "0.6" },
          { path: "/notifications", changefreq: "daily", priority: "0.5" },
          { path: "/settings", changefreq: "monthly", priority: "0.4" },
          { path: "/team", changefreq: "monthly", priority: "0.5" },
          { path: "/login", changefreq: "monthly", priority: "0.4" },
          { path: "/register", changefreq: "monthly", priority: "0.4" },
        ];

        const urls = entries.map((e) =>
          [
            `  <url>`,
            `    <loc>${BASE_URL}${e.path}</loc>`,
            e.lastmod ? `    <lastmod>${e.lastmod}</lastmod>` : null,
            e.changefreq ? `    <changefreq>${e.changefreq}</changefreq>` : null,
            e.priority ? `    <priority>${e.priority}</priority>` : null,
            `  </url>`,
          ]
            .filter(Boolean)
            .join("\n"),
        );

        const xml = [
          `<?xml version="1.0" encoding="UTF-8"?>`,
          `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`,
          ...urls,
          `</urlset>`,
        ].join("\n");

        return new Response(xml, {
          headers: {
            "Content-Type": "application/xml",
            "Cache-Control": "public, max-age=3600",
          },
        });
      },
    },
  },
});
