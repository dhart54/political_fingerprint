// Actual Chromium captures, not mock screenshots. Run against the local dev route.
import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import { chromium } from "@playwright/test";

const root = path.resolve(process.cwd(), "..");
const directory = path.join(root, "docs/editorial/review_packages/health_bounded_choice_v1");
const digest = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const canonical = (value) => Array.isArray(value) ? `[${value.map(canonical).join(",")}]`
  : value !== null && typeof value === "object" ? `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`
    : JSON.stringify(value);
const runtime = JSON.parse(execFileSync(process.env.PYTHON || "python", ["-c", "import json; from backend.app.editorial_presentations.bounded_choice_review import rendering_manifest; print(json.dumps(rendering_manifest()))"], { cwd: root, encoding: "utf8" }));
await fs.mkdir(path.join(directory, "previews"), { recursive: true });
const browser = await chromium.launch();
try {
  for (const member of ["F000477", "M001184"]) {
    const presentation = JSON.parse(await fs.readFile(path.join(directory, `${member.toLowerCase()}-presentation.json`), "utf8"));
    const captures = [];
    for (const [viewport, width, height] of [["desktop", 1280, 900], ["mobile", 390, 844]]) {
      const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      const response = await page.goto(`http://127.0.0.1:3100/review/health-choice?member=${member}`);
      if (response.status() !== 200) throw new Error(`preview status ${response.status()}`);
      await page.evaluate(() => document.fonts.ready);
      const card = page.getByTestId("bounded-choice-review");
      if (await card.getAttribute("data-presentation-sha256") !== presentation.presentation_subject_sha256) throw new Error("preview identity differs");
      await page.getByTestId("choice-receipts").locator("summary").click();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (overflow) throw new Error(`${member} ${viewport}: horizontal overflow`);
      for (const record of Object.values(presentation.records)) {
        if (!(await card.innerText()).includes(record.text)) throw new Error(`mapped field missing: ${record.field_id}`);
      }
      const file = `docs/editorial/review_packages/health_bounded_choice_v1/previews/${member.toLowerCase()}-${viewport}.png`;
      const raw = await page.screenshot({ path: path.join(root, file), fullPage: true, animations: "disabled" });
      captures.push({ viewport, width, height, path: file, sha256: digest(raw), visible_text_sha256: digest(await card.innerText()), presentation_subject_sha256: presentation.presentation_subject_sha256, page_errors: errors });
      if (errors.length) throw new Error(errors.join("\n"));
      await page.close();
    }
    const rendering = { schema_version: "bounded_choice_rendering_subject_v1", member_id: member, presentation_subject_sha256: presentation.presentation_subject_sha256, runtime_manifest: runtime, captures };
    rendering.rendering_subject_sha256 = digest(canonical(rendering));
    await fs.writeFile(path.join(directory, `${member.toLowerCase()}-rendering.json`), `${JSON.stringify(rendering, null, 2)}\n`);
  }
} finally { await browser.close(); }
console.log("Four actual browser captures and two rendering subjects retained.");
