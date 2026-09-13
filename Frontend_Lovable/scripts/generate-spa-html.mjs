import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");

async function generate() {
  try {
    const serverPath = path.join(rootDir, ".output/server/index.mjs");
    if (!fs.existsSync(serverPath)) return;
    const serverModule = await import(`file://${serverPath.replace(/\\/g, "/")}`);
    const res = await serverModule.default.fetch(
      new Request("http://localhost:3000/"),
      {},
      { waitUntil: () => {}, passThroughOnException: () => {} }
    );
    if (res.status === 200) {
      const html = await res.text();
      const distDir = path.join(rootDir, "dist");
      const outPublicDir = path.join(rootDir, ".output/public");
      if (fs.existsSync(distDir)) {
        fs.writeFileSync(path.join(distDir, "index.html"), html, "utf-8");
      }
      if (fs.existsSync(outPublicDir)) {
        fs.writeFileSync(path.join(outPublicDir, "index.html"), html, "utf-8");
      }
      console.log("Successfully generated SPA index.html (" + html.length + " bytes)");
    }
  } catch (e) {
    console.warn("Could not pre-render index.html:", e.message);
  }
}

generate();
