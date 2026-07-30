import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const output = process.env.PASS_A_LIVE_REVIEW_DIR;
const selectedUrl =
  "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY";
const supportFinding =
  /Show 3 exact actions for Certification, fentanyl research provisions/;

async function removeDevelopmentPortal(page) {
  const portal = page.locator("nextjs-portal");
  if (await portal.count()) {
    await portal.evaluate((element) => element.remove());
  }
}

async function capture(page, name, { fullPage = true } = {}) {
  await removeDevelopmentPortal(page);
  await page.screenshot({
    fullPage,
    path: path.join(output, name),
  });
}

async function assertBounded(page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
  await expect(page.locator("img")).toHaveCount(0);
  for (const deferred of [
    "Across Congresses",
    "Compare",
    "Preferences",
    "Alerts",
  ]) {
    await expect(page.getByText(deferred, { exact: true })).toHaveCount(0);
  }
}

test("capture the matching branch full-stack Frontend Pass A review package", async ({
  page,
}) => {
  test.skip(
    !output,
    "Set PASS_A_LIVE_REVIEW_DIR and run against the matching local backend.",
  );
  fs.mkdirSync(output, { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    window.__passALiveScroll = [];
    const original = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function patched(options) {
      window.__passALiveScroll.push(options?.behavior || null);
      return original.call(this, options);
    };
  });

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await expect(page.getByTestId("representative-finder")).toBeVisible();
  await capture(page, "01-finder-1440.png");

  await page.getByLabel("Search by ZIP").fill("27701");
  await page.getByRole("button", { name: "Find by ZIP" }).click();
  await page.getByRole("button", { name: /Select Valerie P\. Foushee/ }).click();
  await expect(page).toHaveURL(/representative=leg_valerie_p_foushee/);
  const cards = page.getByTestId("issue-card");
  await expect(cards.first()).toContainText("Justice & Public Safety");
  await expect(
    cards.filter({ hasText: "Justice & Public Safety" }),
  ).toContainText("Reviewed benchmark sample");
  await expect(
    page.getByRole("button", { name: "Recommended" }),
  ).toHaveAttribute("aria-pressed", "true");
  await capture(page, "02-selected-overview-recommended-1440.png");

  const justiceButton = cards
    .filter({ hasText: "Justice & Public Safety" })
    .getByRole("button");
  await justiceButton.focus();
  await capture(page, "03-visible-focus-issue-selection-1440.png", {
    fullPage: false,
  });
  await page.keyboard.press("Enter");
  const justiceHeading = page
    .getByTestId("issue-detail")
    .getByRole("heading", {
      name: "Justice & Public Safety",
      exact: true,
    });
  await expect(justiceHeading).toBeFocused();
  expect(await page.evaluate(() => window.__passALiveScroll)).toContain("auto");

  await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Where the reviewed sample shows support",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Where the reviewed sample shows opposition",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Where the record is mixed" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Evidence boundaries" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Reviewed analysis", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Selected issue sections" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Chronological action ledger" }),
  ).toBeVisible();
  await assertBounded(page);
  await capture(page, "04-justice-detail-ledger-1440.png");

  const exactActionButton = page.getByRole("button", {
    name: supportFinding,
  });
  await expect(exactActionButton).toHaveText("Show 3 exact actions");
  await exactActionButton.click();
  await expect(
    page.getByRole("heading", { name: "Chronological action ledger" }),
  ).toBeFocused();
  expect(await page.evaluate(() => window.__passALiveScroll)).toContain("auto");
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
  await expect(receipts.first()).toContainText("house:119:1:166");
  await expect(page.getByText("1635", { exact: true })).toHaveCount(0);
  await assertBounded(page);
  await capture(page, "05-exact-actions-focused-1440.png");

  await page.getByRole("button", { name: "Return to all 76 actions" }).click();
  await expect(page.getByText(/Showing 12 of 76 matching actions/)).toBeVisible();
  await expect(page.getByRole("button", { name: "All", exact: true })).toBeVisible();
  await capture(page, "06-returned-to-complete-record-1440.png");

  for (const [width, height, name] of [
    [1024, 900, "07-filtered-ledger-1024.png"],
    [390, 844, "08-filtered-ledger-390.png"],
    [320, 844, "09-filtered-ledger-320.png"],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto(selectedUrl);
    await page.getByRole("button", { name: supportFinding }).click();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
    await expect(
      page.getByRole("navigation", { name: "Selected issue sections" }),
    ).toBeVisible();
    await assertBounded(page);
    await capture(page, name);
  }

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(selectedUrl);
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  await page.getByRole("button", { name: supportFinding }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
  await assertBounded(page);
  await capture(page, "10-effective-zoom-200.png", { fullPage: false });
});
