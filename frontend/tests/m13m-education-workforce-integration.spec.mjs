import fs from "node:fs";

import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";
import { educationEvidenceForScope, educationPositionsForScope, educationPresentation } from "./m13m-education-workforce-fixtures.mjs";

const selectedPath = "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119";

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page, { evidenceOverrides: { EDUCATION_WORKFORCE: educationEvidenceForScope }, presentationOverride: educationPresentation, positionsOverride: educationPositionsForScope });
});

test("real selected-issue route preserves exact M13M wording, accounting, and Mixed boundary", async ({ page }) => {
  await page.goto(selectedPath);
  await expect(page.locator("#selected-issue-heading")).toHaveText("Education & Workforce");
  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText("2 findings · 4 House votes");
  await expect(analysis).toContainText("Funding restrictions tied to institutional relationships or support");
  const pattern = analysis.locator("article").filter({ hasText: "Funding restrictions tied to institutional relationships or support" });
  await expect(pattern.locator(".semantic-label")).toHaveCount(0);
  await expect(analysis.getByText("What the record shows across choices")).toHaveCount(0);
  await analysis.getByText("Other notable choices · 1").click();
  const notable = analysis.locator("article").filter({ hasText: "H.R. 1048 amendment and final passage" });
  await expect(notable.locator(".semantic-label")).toHaveText("Mixed");
  await expect(page.locator("#issue-summary")).toContainText("17 recorded actions currently visible");
});

test("responsive captures preserve controls without horizontal overflow", async ({ page }) => {
  const output = process.env.M13M_SCREENSHOT_DIR;
  const captures = [
    ["desktop-1440.png", 1440, 1000],
    ["desktop-1024.png", 1024, 900],
    ["mobile-390.png", 390, 844],
    ["mobile-320.png", 320, 720],
  ];
  for (const [name, width, height] of captures) {
    await page.setViewportSize({ width, height });
    await page.goto(selectedPath);
    await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
    if (output) {
      fs.mkdirSync(output, { recursive: true });
      await page.screenshot({ fullPage: true, path: `${output}/${name}` });
    }
  }
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.goto(selectedPath);
  await page.evaluate(() => { document.documentElement.style.zoom = "2"; });
  await expect(page.getByRole("button", { name: /View supporting votes for Funding restrictions tied to institutional relationships or support/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  if (output) {
    await page.screenshot({ fullPage: true, path: `${output}/zoom-200-percent.png` });
  }
});
