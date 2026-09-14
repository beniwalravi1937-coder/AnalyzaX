const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

console.log("==> Starting AnalyzaX Frontend Build Bridge...");

const frontendDir = path.resolve(__dirname, "../Frontend");

try {
  const outputDir = path.join(frontendDir, ".output");
  if (fs.existsSync(outputDir)) {
    fs.rmSync(outputDir, { recursive: true, force: true });
  }
} catch (err) {
  // Ignore Windows file lock if running dev server concurrently
}

execSync("npm install --prefix ../Frontend", { stdio: "inherit" });
execSync("npm run build --prefix ../Frontend", { stdio: "inherit" });

const distDir = path.join(__dirname, "dist");
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

const ssrPublic = path.join(frontendDir, ".output/public");
if (fs.existsSync(ssrPublic)) {
  fs.cpSync(ssrPublic, distDir, { recursive: true });
}

const clientDist = path.join(frontendDir, "dist");
if (fs.existsSync(clientDist)) {
  fs.cpSync(clientDist, distDir, { recursive: true });
}

console.log("==> AnalyzaX Frontend Build Bridge Completed Successfully!");
