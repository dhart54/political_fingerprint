import fs from "node:fs";

import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";
import {
  nationalSecurityEvidenceForScope,
  nationalSecurityEvidence119,
  nationalSecurityPositionsForScope,
  nationalSecurityPresentation,
} from "./m11m-national-security-fixtures.mjs";

const selectedPath = "/?representative=leg_valerie_p_foushee&issue=NATIONAL_SECURITY_FOREIGN&scope=119";

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page, {
    evidenceOverrides: {
      NATIONAL_SECURITY_FOREIGN: nationalSecurityEvidenceForScope,
    },
    presentationOverride: nationalSecurityPresentation,
    positionsOverride: nationalSecurityPositionsForScope,
  });
});

test("real selected-issue path renders all 18 governed public wording items", async ({ page }) => {
  expect(nationalSecurityEvidence119).toHaveLength(82);
  await page.goto(selectedPath);

  await expect(page.locator("#selected-issue-heading")).toHaveText("National Security & Foreign Policy");
  await expect(page.locator("#issue-summary")).toContainText("82 recorded actions currently visible");
  await expect(page.locator("#issue-summary")).toContainText("82 votes across 81 legislative episodes");

  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText(
    "Foushee repeatedly supported War Powers resolutions to remove U.S. forces from specified hostilities involving Iran, Lebanon, and Venezuela. Her security-assistance choices differed by country and proposal.",
  );
  await expect(analysis).toContainText("15 findings · 32 votes");
  await expect(analysis.getByRole("heading", { name: "What the record shows across choices" })).toBeVisible();
  await expect(analysis.getByRole("heading", { name: "Patterns in this issue record" })).toBeVisible();
  await expect(analysis.getByRole("heading", { name: "A limiting trajectory" })).toBeVisible();
  await expect(analysis.locator("article")).toHaveCount(17);
  await expect(analysis).not.toContainText("Bounded finding");

  for (const title of [
    "War Powers resolutions across three countries",
    "Security assistance differed by country and proposal",
    "FISA Title VII extensions",
    "Iran War Powers resolutions",
    "Lebanon War Powers resolutions",
    "Venezuela War Powers resolutions",
    "Terrorism preparedness requirements",
    "Ukraine assistance",
    "Jordan assistance restrictions",
    "Military and DoD sex-and-gender amendments",
    "Successive military construction and veterans appropriations packages",
  ]) {
    await expect(analysis.getByRole("heading", { name: title })).toBeVisible();
  }

  const ukraine = analysis.locator("article").filter({ hasText: "Ukraine assistance" });
  await expect(ukraine).toContainText(
    "Opposed three proposals to restrict Ukraine aid and supported one measure authorizing support for Ukraine.",
  );
  await expect(ukraine).toContainText("4 votes · 4 assistance choices");
  await expect(ukraine).not.toContainText("Mixed");
  await expect(ukraine).not.toContainText("±");
  await expect(ukraine.locator(".semantic-label")).toHaveCount(0);

  const assistance = analysis.locator("article").filter({
    hasText: "Security assistance differed by country and proposal",
  });
  await expect(assistance.locator(".semantic-label")).toHaveCount(0);
  await expect(assistance).not.toContainText("Bounded finding");

  const trajectory = analysis.locator("article").filter({
    hasText: "Successive military construction and veterans appropriations packages",
  });
  await expect(trajectory).toContainText("Mixed");
  await expect(trajectory).toContainText("±");

  await analysis.getByText("Other notable choices · 6").click();
  for (const title of [
    "Israel funding and Foreign Military Financing reduction",
    "1991 and 2002 military-force authorizations",
    "International Criminal Court sanctions bill",
    "Taiwan security-cooperation funding",
    "Temporary Protected Status for Haiti",
    "FY2026 defense authorization package",
  ]) {
    await expect(analysis.getByRole("heading", { name: title })).toBeVisible();
  }
  await expect(analysis.locator("article")).toHaveCount(17);
  await expect(analysis).not.toContainText("M11");
  await expect(analysis).not.toContainText("content_subject_sha256");
});

test("every finding links to exact supporting votes and H.R. 8800 stays outside", async ({ page }) => {
  await page.goto(selectedPath);
  const analysis = page.getByTestId("reviewed-analysis");
  const ukraine = analysis.locator("article").filter({ hasText: "Ukraine assistance" });
  await ukraine.getByRole("button", { name: /View supporting votes/ }).click();
  await expect(page.locator(".pattern-strip")).toContainText("4 matching votes");
  await expect(page.locator(".pattern-strip")).not.toContainText("Mixed");
  await expect(page.locator(".pattern-strip")).not.toContainText("±");
  await expect(page.locator(".pattern-strip")).not.toContainText("Bounded finding");
  await expect(page.locator(".pattern-strip .semantic-label")).toHaveCount(0);
  await expect(page.locator('[data-canonical-action-id="house:119:2:278"]')).toHaveCount(0);

  await page.getByRole("button", { name: "Show all 82 votes" }).click();
  const warPowers = analysis.locator("article").filter({
    hasText: "War Powers resolutions across three countries",
  });
  await expect(warPowers).toContainText("9 votes \u00b7 9 country-specific resolutions");
  await warPowers.getByRole("button", { name: /View supporting votes/ }).click();
  await expect(page.locator(".pattern-strip")).toContainText("9 matching votes");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(9);
  await expect(page.locator('[data-canonical-action-id="house:119:1:244"]')).toHaveCount(0);
  for (const actionId of [
    "house:119:1:346",
    "house:119:2:48",
    "house:119:2:85",
    "house:119:2:114",
    "house:119:2:170",
    "house:119:2:199",
    "house:119:2:201",
    "house:119:2:232",
    "house:119:2:282",
  ]) {
    await expect(page.locator(`[data-canonical-action-id="${actionId}"]`)).toBeVisible();
  }

  await page.getByRole("button", { name: "Show all 82 votes" }).click();
  await analysis.getByText("Other notable choices · 6").click();
  const aumf = analysis.locator("article").filter({
    hasText: "1991 and 2002 military-force authorizations",
  });
  await aumf.getByRole("button", { name: /View supporting vote/ }).click();
  await expect(page.locator('[data-canonical-action-id="house:119:1:244"]')).toBeVisible();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);

  await page.getByRole("button", { name: "Show all 82 votes" }).click();
  await expect(page.locator('[data-canonical-action-id="house:119:2:278"]')).toBeVisible();
  const blocked = page.locator('[data-canonical-action-id="house:119:2:278"]');
  await expect(blocked).toContainText("Non-counting control");
  await blocked.getByRole("button").click();
  await expect(blocked).toContainText("No safe public analytical meaning is available for this action.");
});

test("scope all stays explicitly bounded and 118 fails closed", async ({ page }) => {
  await page.goto(selectedPath.replace("scope=119", "scope=all"));
  await page.getByText("Scope boundary").click();
  await expect(page.getByTestId("reviewed-analysis")).toContainText("119th-Congress House record");

  await page.getByRole("button", { name: "118th Congress" }).click();
  await expect(page).toHaveURL(/scope=118/);
  await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
});

for (const width of [1440, 1024, 390, 320]) {
  test(`responsive layout has no horizontal overflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(selectedPath);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    await expect(page.getByRole("navigation", { name: "Selected issue sections" })).toBeVisible();
    await expect(page.getByRole("button", { name: /View supporting votes for Ukraine assistance/ })).toBeVisible();
  });
}

test("200 percent zoom preserves controls and reading order", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.goto(selectedPath);
  await page.evaluate(() => { document.documentElement.style.zoom = "2"; });
  await expect(page.getByRole("heading", { name: "Patterns in this issue record" })).toBeVisible();
  await expect(page.getByRole("button", { name: /View supporting votes for Ukraine assistance/ })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});

test("capture M11M responsive review surfaces", async ({ page }) => {
  const output = process.env.M11M_SCREENSHOT_DIR;
  test.skip(!output, "Set M11M_SCREENSHOT_DIR to capture the review packet.");
  fs.mkdirSync(output, { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });
  for (const [name, width, height] of [
    ["desktop-1440", 1440, 1000],
    ["desktop-1024", 1024, 900],
    ["mobile-390", 390, 844],
    ["mobile-320", 320, 720],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto(selectedPath);
    await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
    await page.screenshot({ fullPage: true, path: `${output}/${name}.png` });
  }
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.goto(selectedPath);
  await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
  await page.evaluate(() => { document.documentElement.style.zoom = "2"; });
  await page.screenshot({ fullPage: true, path: `${output}/zoom-200-percent.png` });
});
