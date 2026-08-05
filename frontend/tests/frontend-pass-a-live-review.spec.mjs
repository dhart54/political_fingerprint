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
  test.setTimeout(120_000);
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
  await page.getByLabel("Search by name").fill("Valerie Foushee");
  await page.getByRole("button", { name: "Search names" }).click();
  await expect(
    page.getByRole("button", { name: /Select Valerie P\. Foushee/ }),
  ).toBeVisible();
  await capture(page, "01-finder-full-name-results-1440.png");
  await page.getByRole("button", { name: /Select Valerie P\. Foushee/ }).click();
  await expect(page).toHaveURL(/representative=leg_valerie_p_foushee/);
  const cards = page.getByTestId("issue-card");
  await expect(cards.first()).toContainText("Justice & Public Safety");
  await expect(
    cards.filter({ hasText: "Justice & Public Safety" }),
  ).toContainText("Issue summary available");
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
      name: "Patterns in this issue record",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Certification, fentanyl research provisions, and officer-safety reporting",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "The fentanyl episode is mixed" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Evidence boundaries" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Issue summaries", exact: true }),
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
  await expect(receipts.first()).not.toContainText("house:119:1:166");
  await expect(page.getByText("1635", { exact: true })).toHaveCount(0);
  await assertBounded(page);
  await capture(page, "05-exact-actions-focused-1440.png");

  const roll32 = page.locator(
    '[data-canonical-action-id="house:119:1:32"]',
  );
  await roll32.getByRole("button").click();
  await expect(roll32.getByRole("button")).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await expect(roll32).toContainText(
    "overdose-reduction certification",
  );
  await expect(roll32).not.toContainText("house:119:1:32");
  await expect(roll32).not.toContainText("clerk_roll_032");
  await expect(roll32).not.toContainText("congress_hamdt5");
  await expect(roll32).toContainText("Official vote");
  await expect(roll32).not.toContainText("Limited context");
  await expect(roll32).not.toContainText("insufficient amendment text");
  await capture(page, "06-corrected-roll-32-expanded-1440.png");

  await page.getByRole("button", { name: "Return to all 76 actions" }).click();
  await expect(page.getByText(/Showing the first 12/)).toBeVisible();
  await expect(page.getByRole("button", { name: "All", exact: true })).toBeVisible();
  await capture(page, "07-returned-to-complete-record-1440.png");

  for (const [width, height, name] of [
    [1024, 900, "08-filtered-ledger-1024.png"],
    [390, 844, "09-corrected-roll-32-expanded-390.png"],
    [320, 844, "10-filtered-ledger-320.png"],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto(selectedUrl);
    await page.getByRole("button", { name: supportFinding }).click();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
    if (width === 390) {
      const mobileRoll32 = page.locator(
        '[data-canonical-action-id="house:119:1:32"]',
      );
      await mobileRoll32.getByRole("button").click();
      await expect(mobileRoll32).not.toContainText("congress_hamdt5");
      await expect(mobileRoll32).toContainText("Official vote");
    }
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
  await capture(page, "11-effective-zoom-200.png", { fullPage: false });

  await page.unrouteAll({ behavior: "wait" });
  await page.route("**/editorial-presentations*", async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    const presentation = payload.presentations.find(
      (item) => item.issue_id === "JUSTICE_PUBLIC_SAFETY",
    );
    presentation.repeated_patterns = presentation.repeated_patterns.map(
      (finding, index) => index === 0
        ? { ...finding, action_ids: ["house:119:1:999"] }
        : finding,
    );
    await route.fulfill({ response, json: payload });
  });
  await page.evaluate(() => {
    document.documentElement.style.zoom = "1";
  });
  await page.goto(selectedUrl);
  await page.getByRole("button", {
    name: /Show 1 exact action for Certification, fentanyl research provisions/,
  }).click();
  await expect(page.getByRole("status").filter({
    hasText: "complete chronological record remains available",
  })).toBeVisible();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  await expect(page.getByText(/Showing the first 12/)).toBeVisible();
  await capture(page, "12-zero-match-fallback-full-ledger-1440.png");
});
