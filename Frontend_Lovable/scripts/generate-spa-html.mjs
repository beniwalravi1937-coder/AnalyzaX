import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");

async function generate() {
  try {
    const serverPath = path.join(rootDir, ".output/server/index.mjs");
    if (fs.existsSync(serverPath)) {
      const serverModule = await import(`file://${serverPath.replace(/\\/g, "/")}`);
      const res = await serverModule.default.fetch(
        new Request("http://localhost:3000/"),
        {},
        { waitUntil: () => {}, passThroughOnException: () => {} }
      );
      if (res.status === 200) {
        const html = await res.text();
        const distDir = path.join(rootDir, "dist");
        if (fs.existsSync(distDir)) {
          fs.writeFileSync(path.join(distDir, "index.html"), html, "utf-8");
        }
        console.log("Successfully generated SPA index.html (" + html.length + " bytes)");
      }
    }

    // Prepare .vercel/output for Vercel Build Output API v3
    const vercelOutputDir = path.join(rootDir, ".vercel/output");
    const vercelStaticDir = path.join(vercelOutputDir, "static");
    fs.mkdirSync(vercelStaticDir, { recursive: true });

    const distDir = path.join(rootDir, "dist");
    if (fs.existsSync(distDir)) {
      fs.cpSync(distDir, vercelStaticDir, { recursive: true });
    }

    const configJson = {
      version: 3,
      routes: [
        { handle: "filesystem" },
        { src: "/(.*)", dest: "/index.html" }
      ]
    };
    fs.writeFileSync(
      path.join(vercelOutputDir, "config.json"),
      JSON.stringify(configJson, null, 2),
      "utf-8"
    );
    console.log("Prepared .vercel/output for Vercel Build Output API v3");

    // Clean up .output so Nitro SSR Cloudflare worker is never deployed on Vercel Node runtime
    const nitroOutputDir = path.join(rootDir, ".output");
    if (fs.existsSync(nitroOutputDir)) {
      fs.rmSync(nitroOutputDir, { recursive: true, force: true });
      console.log("Cleaned up .output directory to ensure pure static edge deployment");
    }
  } catch (e) {
    console.warn("generate-spa-html error:", e.message);
  }
}

generate();
