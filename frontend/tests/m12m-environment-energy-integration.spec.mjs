import fs from "node:fs";

import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";
import { environmentEvidenceForScope, environmentPositionsForScope, environmentPresentation } from "./m12m-environment-energy-fixtures.mjs";

const selectedPath = "/?representative=leg_valerie_p_foushee&issue=ENVIRONMENT_ENERGY&scope=119";

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page, { evidenceOverrides: { ENVIRONMENT_ENERGY: environmentEvidenceForScope }, presentationOverride: environmentPresentation, positionsOverride: environmentPositionsForScope });
});

test("real selected-issue route preserves exact M12M wording, counts, and directionlessness", async ({ page }) => {
  await page.goto(selectedPath);
  await expect(page.locator("#selected-issue-heading")).toHaveText("Environment & Energy");
  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis.locator("article")).toHaveCount(4);
  for (const [title, label] of [["Congressional efforts to overturn agency decisions", "13 resolutions · 3 repeated patterns"], ["California vehicle-emissions waivers", "2 resolutions · 2 separate decisions"], ["Appliance and commercial-equipment rules", "4 resolutions · 4 separate rules"], ["Bureau of Land Management decisions", "7 resolutions · 7 separate land decisions"]]) {
    const card = analysis.locator("article").filter({ hasText: title });
    await expect(card).toContainText(label);
    await expect(card.locator(".semantic-label")).toHaveCount(0);
  }
  await expect(page.locator("#issue-summary")).toContainText("63 recorded actions currently visible");
});

test("200 percent zoom has no overflow and preserves receipt controls", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.goto(selectedPath);
  await page.evaluate(() => { document.documentElement.style.zoom = "2"; });
  await expect(page.getByRole("button", { name: /View supporting votes for California vehicle-emissions waivers/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  const output = process.env.M12M_SCREENSHOT_DIR;
  if (output) {
    fs.mkdirSync(output, { recursive: true });
    await page.screenshot({ fullPage: true, path: `${output}/zoom-200-percent.png` });
  }
});
