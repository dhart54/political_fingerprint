import fs from "node:fs";

import { expect, test } from "@playwright/test";


const selectedPath = "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119";
const output = process.env.M14G_SCREENSHOT_DIR;


async function openSelectedIssue(page) {
  await page.goto(selectedPath);
  await expect(page.locator("#selected-issue-heading")).toHaveText("Education & Workforce");
  await expect(page.locator("#issue-summary")).toContainText("3 findings supported by 6 votes");
}


test("real M14G backend and frontend render exact hierarchy and receipt meaning", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1600 });
  await openSelectedIssue(page);
  await page.getByRole("link", { name: "Issue summary" }).click();
  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText("2 linked findings · 4 House votes");
  await expect(analysis.getByText("Patterns in this issue record")).toBeVisible();
  await expect(analysis.getByText("What the record shows across choices")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  if (output) {
    fs.mkdirSync(output, { recursive: true });
    await page.screenshot({ path: `${output}/desktop_overview.png` });
  }

  await analysis.getByText("Other notable choices · 1").click();
  const notable = analysis.locator("article").filter({ hasText: "Supported a reporting-focused replacement, opposed the final H.R. 1048 package" });
  await expect(notable.locator(".semantic-label")).toHaveText("Mixed");
  await notable.getByText("Boundaries and limitations").click();
  await expect(notable).toContainText("The final H.R. 1048 vote applied to the whole package");
  if (output) {
    await page.screenshot({ path: `${output}/desktop_notable_expanded.png` });
  }

  const bargaining = analysis.locator("article").filter({ hasText: "Supported keeping collective bargaining in force" });
  await bargaining.getByRole("button", { name: /View supporting votes/ }).click();
  const hr2550 = page.locator('[data-canonical-action-id="house:119:1:332"]');
  await hr2550.getByRole("button", { name: /Expand H\.R\. 2550/ }).click();
  const eo14251 = hr2550.locator(
    'a[href="https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm"]',
  );
  await expect(eo14251).toHaveText("Executive order");
  await expect(hr2550.locator(
    'a[href="https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm"]',
    { hasText: "Bill or amendment text" },
  )).toHaveCount(0);
  const hr5408 = page.locator('[data-canonical-action-id="house:119:2:216"]');
  await hr5408.getByRole("button", { name: /Expand H\.R\. 5408/ }).click();
  await expect(hr5408).toContainText("Current wages, hours, and employment terms would have to be maintained");
  await expect(hr5408).toContainText("arbitration award would bind the parties for two years");
  await expect(hr5408).not.toContainText("accelerate workplace time-to-contract");
  if (output) {
    await hr5408.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${output}/desktop_hr5408_receipt.png` });
  }
});


test("real M14G mobile preview has no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openSelectedIssue(page);
  await page.getByRole("link", { name: "Issue summary" }).click();
  await expect(page.getByText("Main takeaway", { exact: true })).toBeVisible();
  await expect(page.getByText("Patterns in this issue record", { exact: true })).toBeAttached();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  if (output) {
    fs.mkdirSync(output, { recursive: true });
    await page.screenshot({ fullPage: true, path: `${output}/mobile_overview.png` });
  }
});
