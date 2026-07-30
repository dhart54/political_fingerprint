import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page);
});

test("primary route starts with the finder and does not auto-render a sample profile", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("representative-finder")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Start with a person, not a score." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Aaron Bean", exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Valerie P. Foushee", exact: true })).toHaveCount(0);
  await expect(page.locator("img")).toHaveCount(0);
});

test("name search selects a representative and receipts-only issues stay neutral", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Search by name").fill("Foushee");
  await page.getByRole("button", { name: "Search names" }).click();
  await page.getByRole("button", { name: /Select Valerie P\. Foushee/ }).click();
  await expect(page.getByRole("heading", { name: "Valerie P. Foushee", exact: true })).toBeVisible();
  await expect(page).toHaveURL(/representative=leg_valerie_p_foushee/);
  const economy = page.getByTestId("issue-card").filter({ hasText: "Economy & Taxes" });
  await expect(economy).toContainText("Vote receipts available");
  await expect(economy).not.toContainText(/conclusion|full review complete/i);
});

test("removed rich-editorial fixture route remains 404", async ({ page }) => {
  const response = await page.goto("/golden-render-fixture");
  expect(response?.status()).toBe(404);
});
