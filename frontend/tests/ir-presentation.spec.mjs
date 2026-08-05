import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page);
  await page.goto("/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY");
  await expect(page.getByRole("heading", { name: "Valerie P. Foushee", exact: true })).toBeVisible();
});

test("benchmark analysis uses the public sample label and supplied finding directions", async ({ page }) => {
  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText("Reviewed record sample");
  await expect(analysis).toContainText("7 reviewed actions");
  await expect(analysis).toContainText("5 policy episodes");
  await expect(analysis).toContainText("Main takeaway");
  await expect(analysis).toContainText("Pattern index");
  await expect(analysis).toContainText("Support");
  await expect(analysis).toContainText("Opposition");
  await expect(analysis).toContainText("Mixed");
  await expect(analysis).toContainText("Limitations and unresolved actions · 1");
  await expect(analysis).not.toContainText("Full review complete");
  await expect(analysis).not.toContainText("Full issue interpretation available");
});

test("scope all preserves 119th boundary and scope 118 removes analysis", async ({ page }) => {
  await expect(page.getByTestId("reviewed-analysis")).toContainText(
    "bounded to the reviewed 119th-Congress",
  );
  await page.getByRole("button", { name: "118th Congress" }).click();
  await expect(page).toHaveURL(/scope=118/);
  await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Issue summary" }),
  ).toHaveCount(0);
});

test("exact-action control highlights only supplied actions and keeps full ledger available", async ({ page }) => {
  await page.getByRole("button", {
    name: /Show 3 exact actions for Certification, fentanyl research provisions/,
  }).click();
  await expect(page.getByRole("heading", { name: "Chronological action ledger" })).toBeFocused();
  await expect(page.getByText("Selected pattern")).toBeVisible();
  await expect(page.getByText(/Showing 3 exact actions across 2 policy episodes/)).toBeVisible();
  await expect(page.locator('[data-canonical-action-id="house:119:1:32"]')).toBeVisible();
  await page.getByRole("button", { name: /Return to all 7 actions/ }).click();
  await expect(page.getByRole("button", { name: "All", exact: true })).toHaveAttribute("aria-pressed", "true");
});

test("/golden-render-fixture remains unavailable", async ({ page }) => {
  const response = await page.goto("/golden-render-fixture");
  expect(response?.status()).toBe(404);
});
