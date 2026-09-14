const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

console.log("==> Starting AnalyzaX Frontend Build Bridge...");

const frontendDir = path.resolve(__dirname, "../Frontend");
const distDir = path.join(__dirname, "dist");
const frontendDistDir = path.join(frontendDir, "dist");

try {
  const outputDir = path.join(frontendDir, ".output");
  if (fs.existsSync(outputDir)) {
    fs.rmSync(outputDir, { recursive: true, force: true });
  }
} catch (err) {
  // Ignore Windows file lock if running dev server concurrently
}

console.log("==> Installing dependencies in Frontend...");
execSync("npm install --prefix ../Frontend", { stdio: "inherit" });

console.log("==> Building Frontend...");
execSync("npm run build --prefix ../Frontend", { stdio: "inherit" });

// Prepare dist directories
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}
if (!fs.existsSync(frontendDistDir)) {
  fs.mkdirSync(frontendDistDir, { recursive: true });
}

// Copy .output/public contents to dist
const ssrPublic = path.join(frontendDir, ".output/public");
if (fs.existsSync(ssrPublic)) {
  console.log(`==> Copying static files from ${ssrPublic} to dist...`);
  fs.cpSync(ssrPublic, distDir, { recursive: true });
  fs.cpSync(ssrPublic, frontendDistDir, { recursive: true });
}

// Copy public assets if any exist
const frontendPublic = path.join(frontendDir, "public");
if (fs.existsSync(frontendPublic)) {
  fs.cpSync(frontendPublic, distDir, { recursive: true });
  fs.cpSync(frontendPublic, frontendDistDir, { recursive: true });
}

// Detect generated JS entry and CSS entry
const assetsDir = path.join(distDir, "assets");
let entryJs = null;
let entryCss = null;

if (fs.existsSync(assetsDir)) {
  const files = fs.readdirSync(assetsDir);
  entryJs = files.find(f => f.startsWith("index-") && f.endsWith(".js"));
  entryCss = files.find(f => f.startsWith("styles-") && f.endsWith(".css"));
}

console.log(`==> Detected entry bundles: JS=${entryJs}, CSS=${entryCss}`);

// Ensure index.html exists in dist
const templateHtmlPath = path.join(__dirname, "index.html");
let htmlContent = "";

if (fs.existsSync(templateHtmlPath)) {
  htmlContent = fs.readFileSync(templateHtmlPath, "utf8");
} else if (fs.existsSync(path.join(distDir, "index.html"))) {
  htmlContent = fs.readFileSync(path.join(distDir, "index.html"), "utf8");
}

if (htmlContent) {
  if (entryJs) {
    htmlContent = htmlContent.replace(
      /\/assets\/index-[a-zA-Z0-9_-]+\.js/g,
      `/assets/${entryJs}`
    );
  }
  if (entryCss) {
    htmlContent = htmlContent.replace(
      /\/assets\/styles-[a-zA-Z0-9_-]+\.css/g,
      `/assets/${entryCss}`
    );
  }

  // Write updated index.html to both dist locations and template
  fs.writeFileSync(path.join(distDir, "index.html"), htmlContent, "utf8");
  fs.writeFileSync(path.join(frontendDistDir, "index.html"), htmlContent, "utf8");
  fs.writeFileSync(templateHtmlPath, htmlContent, "utf8");
  console.log("==> Successfully generated and updated index.html with new asset hashes!");
} else {
  console.error("==> WARNING: Could not find template index.html to populate dist/index.html!");
}

// Validation gate
if (fs.existsSync(path.join(distDir, "index.html"))) {
  const stats = fs.statSync(path.join(distDir, "index.html"));
  console.log(`==> Verified dist/index.html exists (${stats.size} bytes).`);
} else {
  console.error("==> ERROR: dist/index.html does not exist!");
  process.exit(1);
}

console.log("==> AnalyzaX Frontend Build Bridge Completed Successfully!");
