import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";

test.beforeEach(async ({ page }, testInfo) => {
  await installPassARoutes(page, {
    episodes: testInfo.title.includes("episode component"),
  });
});

test("finder, compact selected header, issue URL state, and browser history work together", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Search by ZIP").fill("27701");
  await page.getByRole("button", { name: "Find by ZIP" }).click();
  await page.getByRole("button", { name: /Select Valerie P\. Foushee/ }).click();
  await expect(page.getByText("U.S. House · NC district 4 · Democratic")).toBeVisible();
  await expect(page.getByText("Scope: All available Congresses")).toBeVisible();
  await page.getByTestId("issue-card").filter({ hasText: "Justice & Public Safety" }).getByRole("button").click();
  await expect(page).toHaveURL(/issue=JUSTICE_PUBLIC_SAFETY/);
  await expect(
    page.getByTestId("issue-detail").getByRole("heading", {
      name: "Justice & Public Safety",
      exact: true,
    }),
  ).toBeFocused();
  await page.goBack();
  await expect(page).not.toHaveURL(/issue=/);
  await expect(page.getByTestId("issue-detail")).toHaveCount(0);
  await page.goForward();
  await expect(page.getByTestId("issue-detail")).toBeVisible();
});

test("issue sort and filter controls expose evidence and reviewed states", async ({ page }) => {
  await page.goto("/?representative=leg_valerie_p_foushee");
  const cards = page.getByTestId("issue-card");
  await expect(cards.nth(0)).toContainText("Justice & Public Safety");
  await page.getByRole("button", { name: "Most evidence" }).click();
  await expect(cards.nth(0)).toContainText("Economy & Taxes");
  await page.getByRole("button", { name: "Reviewed analysis" }).click();
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toContainText("Reviewed benchmark sample");
  await page.getByRole("button", { name: "A–Z" }).click();
  await expect(cards.nth(0)).toContainText("Economy & Taxes");
});

test("chronological ledger filters, progressive reveal, and single receipt expansion", async ({ page }) => {
  await page.goto("/?representative=leg_valerie_p_foushee&issue=ECONOMY_TAXES");
  const receipts = page.locator("[data-canonical-action-id]");
  await expect(receipts).toHaveCount(12);
  await expect(receipts.first()).toHaveAttribute("data-canonical-action-id", "house:119:1:412");
  await page.getByRole("button", { name: "Show 1 more" }).click();
  await expect(receipts).toHaveCount(13);
  const first = receipts.nth(0).getByRole("button");
  const second = receipts.nth(1).getByRole("button");
  await first.click();
  await expect(first).toHaveAttribute("aria-expanded", "true");
  await expect(receipts.nth(0)).toContainText("Policy-episode relationship");
  await expect(receipts.nth(0)).toContainText("Provenance references");
  await second.click();
  await expect(first).toHaveAttribute("aria-expanded", "false");
  await expect(second).toHaveAttribute("aria-expanded", "true");
  await page.getByRole("button", { name: "Nay", exact: true }).click();
  await expect(page.getByText(/Showing 6 of 6 matching actions/)).toBeVisible();
});

test("reviewed finding links resolve live-shaped evidence IDs and open the first receipt", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    window.__exactActionsScroll = [];
    const original = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function patched(options) {
      window.__exactActionsScroll.push(options?.behavior || null);
      return original.call(this, options);
    };
  });
  await page.goto("/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY");
  await page.getByRole("button", {
    name: /Show 3 exact actions for Certification, fentanyl research provisions/,
  }).click();
  await expect(page.getByText("Selected reviewed finding")).toBeVisible();
  await expect(page.getByText(/Showing 3 exact actions supplied/)).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Chronological action ledger" }),
  ).toBeFocused();
  expect(await page.evaluate(() => window.__exactActionsScroll)).toContain("auto");
  const receipts = page.locator("[data-canonical-action-id]");
  await expect(receipts).toHaveCount(3);
  await expect(receipts.first()).toHaveAttribute(
    "data-canonical-action-id",
    "house:119:1:166",
  );
  await expect(receipts.first().getByRole("button")).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await expect(receipts.first()).toContainText("Expanded vote receipt");
  await page.getByRole("button", { name: "Return to all 7 actions" }).click();
  await expect(page.getByRole("button", { name: "All", exact: true })).toBeVisible();
  await expect(receipts).toHaveCount(7);
});

test("episode component uses supplied order, keeps one open, and preserves oldest-first actions", async ({ page }) => {
  await page.goto("/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY");
  const episodes = page.locator("#policy-episodes article");
  await expect(episodes).toHaveCount(2);
  await expect(episodes.nth(0)).toContainText("Newer reviewed episode");
  const newer = episodes.nth(0).getByRole("button");
  const older = episodes.nth(1).getByRole("button");
  await newer.click();
  await expect(episodes.nth(0)).toContainText(/2025-09-17: First action[\s\S]*2025-11-19: Second action/);
  await expect(
    episodes.nth(0).getByRole("link", { name: "Official episode source" }),
  ).toHaveAttribute("href", "https://www.congress.gov/example/episode");
  await older.click();
  await expect(newer).toHaveAttribute("aria-expanded", "false");
  await expect(older).toHaveAttribute("aria-expanded", "true");
});

for (const width of [1440, 1024, 390, 320]) {
  test(`primary journey has no horizontal overflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
    await page.goto("/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY");
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
    await expect(page.locator("img")).toHaveCount(0);
  });
}

test("keyboard and reduced-motion selection transfer focus without smooth scrolling", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    window.__passAScroll = [];
    const original = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function patched(options) {
      window.__passAScroll.push(options?.behavior || null);
      return original.call(this, options);
    };
  });
  await page.goto("/?representative=leg_valerie_p_foushee");
  const justice = page.getByTestId("issue-card").filter({ hasText: "Justice & Public Safety" }).getByRole("button");
  await justice.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByTestId("issue-detail").getByRole("heading", {
      name: "Justice & Public Safety",
      exact: true,
    }),
  ).toBeFocused();
  expect(await page.evaluate(() => window.__passAScroll)).toContain("auto");
});

test("200 percent zoom keeps the primary journey readable and bounded", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY");
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
  await expect(page.getByRole("heading", { name: "Chronological action ledger" })).toBeVisible();
});

test("desktop and mobile rendered evidence can be captured for review", async ({ page }) => {
  const output = process.env.PASS_A_SCREENSHOT_DIR;
  test.skip(!output, "Set PASS_A_SCREENSHOT_DIR to capture review evidence.");
  fs.mkdirSync(output, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.goto("/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY");
  await expect(page.getByTestId("issue-card")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "Chronological action ledger" }),
  ).toBeVisible();
  const devPortal = page.locator("nextjs-portal");
  if (await devPortal.count()) {
    await devPortal.evaluate((element) => element.remove());
  }
  await page.screenshot({
    fullPage: true,
    path: path.join(output, "frontend-pass-a-desktop.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    fullPage: true,
    path: path.join(output, "frontend-pass-a-mobile.png"),
  });
});

test("/golden-render-fixture remains 404", async ({ page }) => {
  const response = await page.goto("/golden-render-fixture");
  expect(response?.status()).toBe(404);
});
