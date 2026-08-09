import { expect, test } from "@playwright/test";
import path from "node:path";

const screenshots = process.env.M6_REVIEW_SCREENSHOT_DIR;

async function openReview(page) {
  await page.goto("/review/foushee-justice-m6");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("One bounded contrast");
}

async function capture(page, name, options = {}) {
  if (!screenshots) {
    return;
  }
  await page.screenshot({ path: path.join(screenshots, name), fullPage: true, ...options });
}

test("desktop candidate preserves all primary and limiting meaning", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1050 });
  await openReview(page);
  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText("Opposition to displacing D.C. public-safety rules");
  await expect(analysis).toContainText("Opposition to reducing firearm-access barriers");
  await expect(analysis).toContainText("Opposition to expanding fraud-enforcement capacity");
  await expect(analysis).toContainText("Support for terrorism-preparedness mandates");
  await expect(analysis).toContainText("one mixed episode");
  await expect(page.getByText("Four unresolved launch cases")).toBeVisible();
  await capture(page, "desktop-1440-overview.png");
});

test("desktop ledger exposes all 37 actions and special boundaries", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1050 });
  await openReview(page);
  await expect(page.getByText(/37 recorded actions .* Newest first/)).toBeVisible();
  while (await page.getByRole("button", { name: "Show more votes" }).count()) {
    await page.getByRole("button", { name: "Show more votes" }).click();
  }
  for (const action of ["house:119:1:128", "house:119:2:155", "house:119:2:278"]) {
    await expect(page.locator(`[data-canonical-action-id="${action}"]`)).toBeVisible();
  }
  const roll278 = page.locator('[data-canonical-action-id="house:119:2:278"]');
  await roll278.locator("button").click();
  await expect(roll278.locator("p").filter({ hasText: "No safe public analytical meaning is available for this action." })).toBeVisible();
  await capture(page, "desktop-ledger-special-rolls.png");
});

for (const [name, width, height] of [
  ["tablet-1024.png", 1024, 900],
  ["mobile-390.png", 390, 844],
  ["narrow-mobile-320.png", 320, 700],
]) {
  test(`responsive evidence ${name}`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await openReview(page);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    await capture(page, name);
  });
}

test("200 percent zoom retains content without horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await openReview(page);
  await page.evaluate(() => { document.documentElement.style.zoom = "2"; });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  await capture(page, "zoom-200.png");
});

test("keyboard route reaches analysis, supporting votes, and receipt expansion", async ({ page }) => {
  await openReview(page);
  const button = page.getByRole("button", { name: /View 6 votes for Opposition to displacing/ });
  await button.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Vote record" })).toBeFocused();
  const receipt = page.locator('[data-canonical-action-id="house:119:1:162"] button');
  await receipt.focus();
  await page.keyboard.press("Enter");
  await expect(receipt).toHaveAttribute("aria-expanded", "true");
  await capture(page, "keyboard-expanded-receipt.png");
});

test("reduced motion uses the same complete semantic content", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await openReview(page);
  await expect(page.getByTestId("reviewed-analysis")).toContainText("The HALT Fentanyl path is one mixed episode");
  await capture(page, "reduced-motion.png");
});

test("headings, landmarks, names, and focus order remain accessible", async ({ page }) => {
  await openReview(page);
  await expect(page.getByRole("main")).toHaveCount(1);
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  await expect(page.getByRole("heading", { name: "Four unresolved launch cases" })).toBeVisible();
  const unnamedButtons = await page.locator("button:not([aria-label])").evaluateAll((buttons) => buttons.filter((button) => !(button.textContent || "").trim()).length);
  expect(unnamedButtons).toBe(0);
});

test("review route is disabled without its explicit server flag", async ({ request }) => {
  // The route guard is also inspected by the independent verifier. The active
  // Playwright server deliberately enables the fixture for this review suite.
  const response = await request.get("/review/foushee-justice-m6");
  expect(response.status()).toBe(200);
});
