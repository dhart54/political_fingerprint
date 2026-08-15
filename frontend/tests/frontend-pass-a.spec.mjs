import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import {
  foushee,
  installPassARoutes,
  justicePresentation,
} from "./pass-a-fixtures.mjs";

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

test("finder accepts an ordinary first-and-last-name query", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Search by name").fill("Valerie Foushee");
  await page.getByRole("button", { name: "Search names" }).click();
  await expect(
    page.getByRole("button", { name: /Select Valerie P\. Foushee/ }),
  ).toBeVisible();
});

test("Justice keeps its complete conclusion under progressive disclosure", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );
  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText(justicePresentation.teaser);
  const disclosure = analysis.locator("details").filter({
    hasText: "Read the complete conclusion",
  });
  await expect(disclosure).toHaveCount(1);
  await expect(disclosure).not.toHaveAttribute("open", "");
  await expect(disclosure.locator("p")).not.toBeVisible();
  await disclosure.getByText("Read the complete conclusion").click();
  await expect(disclosure).toHaveAttribute("open", "");
  await expect(disclosure.locator("p")).toContainText(
    "In this reviewed 119th-Congress sample",
  );
  await expect(analysis).toContainText("Patterns in this issue record");
  await expect(analysis).toContainText("Limitations and unresolved actions · 1");
});

test("issue sort and filter controls expose evidence and reviewed states", async ({ page }) => {
  await page.goto("/?representative=leg_valerie_p_foushee");
  const cards = page.getByTestId("issue-card");
  await expect(cards.nth(0)).toContainText("Justice & Public Safety");
  await page.getByRole("button", { name: "Most evidence" }).click();
  await expect(cards.nth(0)).toContainText("Economy & Taxes");
  await page.getByRole("button", { name: "Issue summaries" }).click();
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toContainText("Issue summary available");
  await page.getByRole("button", { name: "A–Z" }).click();
  await expect(cards.nth(0)).toContainText("Economy & Taxes");
});

test("chronological ledger filters, progressive reveal, and single receipt expansion", async ({ page }) => {
  await page.goto("/?representative=leg_valerie_p_foushee&issue=ECONOMY_TAXES");
  const receipts = page.locator("[data-canonical-action-id]");
  await expect(receipts).toHaveCount(12);
  await expect(receipts.first()).toHaveAttribute("data-canonical-action-id", "house:119:1:412");
  await page.getByRole("button", { name: "Show more votes" }).click();
  await expect(receipts).toHaveCount(13);
  const first = receipts.nth(0).getByRole("button");
  const second = receipts.nth(1).getByRole("button");
  await first.click();
  await expect(first).toHaveAttribute("aria-expanded", "true");
  await expect(receipts.nth(0)).toContainText("How Valerie P. Foushee voted");
  await expect(receipts.nth(0)).toContainText("Official vote");
  await expect(receipts.nth(0)).not.toContainText("Provenance references");
  await second.click();
  await expect(first).toHaveAttribute("aria-expanded", "false");
  await expect(second).toHaveAttribute("aria-expanded", "true");
  await page.getByRole("button", { name: "Nay", exact: true }).click();
  await expect(page.getByText(/Showing all 6 matching votes/)).toBeVisible();
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
    name: /View 3 votes for Certification, fentanyl research provisions/,
  }).click();
  await expect(page.locator(".pattern-strip")).toBeVisible();
  await expect(page.locator(".pattern-strip")).toContainText("3 votes");
  await expect(
    page.getByRole("heading", { name: "Vote record" }),
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
  await expect(receipts.first()).toContainText("What this vote was about");
  const roll32 = page.locator(
    '[data-canonical-action-id="house:119:1:32"]',
  );
  await roll32.getByRole("button").click();
  await expect(roll32).toContainText("overdose-reduction certification");
  await expect(roll32).toContainText("Official vote");
  await expect(roll32).toContainText("Bill or amendment text");
  for (const forbidden of [
    "congress_hamdt5",
    "clerk_roll_032",
    "acceptance_receipt.json",
    "launch_ratification",
    "m10r1-receipt",
    "M10R1 launch",
    "2026-08-04",
    "Interpretation digest",
    "Provenance references",
    "Reviewed exact-action meaning supplied",
  ]) {
    await expect(roll32).not.toContainText(forbidden);
  }
  await expect(roll32).not.toContainText("Limited context");
  await expect(roll32).not.toContainText("insufficient");
  await expect(roll32).not.toContainText("Justice measure 32 stakes.");
  await page.getByRole("button", { name: "Show all 7 votes" }).click();
  await expect(page.getByRole("button", { name: "All", exact: true })).toBeVisible();
  await expect(receipts).toHaveCount(7);
});

test("zero-match exact-action request keeps the complete ledger and announces the fallback", async ({ page }) => {
  await page.route("**/editorial-presentations*", async (route) => {
    const stale = {
      ...justicePresentation,
      repeated_patterns: justicePresentation.repeated_patterns.map(
        (finding, index) => index === 0
          ? { ...finding, action_ids: ["house:119:1:999"] }
          : finding,
      ),
    };
    await route.fulfill({
      json: {
        schema_version: "editorial_public_presentations_api_v1",
        legislator_id: foushee.id,
        member_bioguide_id: foushee.bioguide_id,
        scope: "all",
        presentations: [stale],
      },
    });
  });
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY",
  );
  await page.getByRole("button", {
    name: /View 1 vote for Certification, fentanyl research provisions/,
  }).click();
  await expect(page.getByRole("status").filter({
    hasText: "linked exact actions are unavailable",
  })).toBeVisible();
  await expect(page.getByRole("button", { name: "All", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(7);
  await expect(page.getByText(/Showing all 7 matching votes/)).toBeVisible();
  await expect(page.getByText("No recorded actions match this filter.")).toHaveCount(0);
});

test("changing scope clears stale exact-action filtering", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY",
  );
  await page.getByRole("button", {
    name: /View 3 votes for Certification, fentanyl research provisions/,
  }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
  await page.getByRole("button", { name: "118th Congress" }).click();
  await expect(page.getByRole("button", { name: "All", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(7);
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
  await expect(page.getByRole("heading", { name: "Vote record" })).toBeVisible();
});

test("desktop and mobile rendered evidence can be captured for review", async ({ page }) => {
  const output = process.env.PASS_A_SCREENSHOT_DIR;
  test.skip(!output, "Set PASS_A_SCREENSHOT_DIR to capture review evidence.");
  fs.mkdirSync(output, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.goto("/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY");
  await expect(page.getByTestId("issue-card")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "Vote record" }),
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
