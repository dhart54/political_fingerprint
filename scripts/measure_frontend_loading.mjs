// Opt-in, read-only timing probe. Uses the repository's installed Playwright.
// node scripts/measure_frontend_loading.mjs <selected-page-url> <output-directory>
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
const require = createRequire(new URL("../frontend/package.json", import.meta.url));
const { chromium } = require("playwright");
const [target, output] = process.argv.slice(2);
if (!target || !output || !["https:", "http:"].includes(new URL(target).protocol)) {
  throw Error("Supply a selected representative/issue HTTP URL and an output directory.");
}
fs.mkdirSync(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" });
  const page = await context.newPage();
  const runs = [];
  for (const mode of ["cold-browser-context", "warm-reload"]) {
    const start = performance.now();
    const elapsed = () => Math.round(performance.now() - start);
    const run = { mode, url: target, startedAt: new Date().toISOString(), stages: {}, requests: [], errors: [] };
    const pending = [];
    const responseHandler = request => {
      if (!new URL(request.url()).pathname.startsWith("/legislators/")) return;
      pending.push((async () => {
        const response = await request.response();
        run.requests.push({ url: request.url(), status: response?.status(), finishedMs: elapsed(), timing: request.timing() });
      })());
    };
    const errorHandler = error => run.errors.push(error.message);
    page.on("requestfinished", responseHandler);
    page.on("pageerror", errorHandler);
    try {
      await (mode === "warm-reload" ? page.reload({ waitUntil: "domcontentloaded", timeout: 30000 }) : page.goto(target, { waitUntil: "domcontentloaded", timeout: 30000 }));
      run.stages.domContentLoadedMs = elapsed();
      for (const [name, selector] of [["representative", "#representative-name"], ["issueSummary", "#issue-summary"], ["receipts", "[data-canonical-action-id]"]]) {
        await page.locator(selector).first().waitFor({ state: "visible", timeout: 120000 });
        run.stages[`${name}Ms`] = elapsed();
      }
      run.coverage = await page.locator("#issue-summary").innerText();
      await page.screenshot({ path: path.join(output, `${mode}.png`) });
    } catch (error) {
      run.errors.push(error.message);
    }
    // Only completed responses are included; stalled requests remain a limitation.
    await Promise.allSettled(pending);
    page.off("requestfinished", responseHandler);
    page.off("pageerror", errorHandler);
    runs.push(run);
    fs.writeFileSync(path.join(output, "loading-measurements.json"), JSON.stringify(runs, null, 2));
    console.log(JSON.stringify(run));
  }
} finally {
  await browser.close();
}
