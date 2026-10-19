import { test, expect } from "@playwright/test";
import fs from "node:fs";

const production = process.env.PLAYWRIGHT_PRODUCTION_BUILD === "1";
for (const member of ["F000477", "M001184"]) {
  const presentation = JSON.parse(fs.readFileSync(`../docs/editorial/review_packages/health_bounded_choice_v1/${member.toLowerCase()}-presentation.json`, "utf8"));
  for (const [name, width, height] of [["desktop", 1280, 900], ["tablet", 768, 1024], ["mobile", 390, 844]]) {
    test(`${member} ${name}: bounded review and evidence stay truthful`, async ({ page }) => {
      await page.setViewportSize({ width, height });
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      const response = await page.goto(`/review/health-choice?member=${member}`);
      if (production) {
        expect(response.status()).toBe(404);
        await expect(page.getByTestId("bounded-choice-review")).toHaveCount(0);
        return;
      }
      expect(response.status()).toBe(200);
      const card = page.getByTestId("bounded-choice-review");
      await expect(card).toHaveAttribute("data-member-id", member);
      await expect(card).toHaveAttribute("data-display-role", presentation.display_role);
      await expect(card).toHaveAttribute("data-presentation-sha256", presentation.presentation_subject_sha256);
      for (const record of Object.values(presentation.records)) await expect(card).toContainText(record.text);
      await expect(page.getByTestId("supporting-choice")).toHaveCount(member === "F000477" ? 1 : 0);
      await expect(page.getByTestId("not-voting-accounting")).toHaveCount(member === "M001184" ? 1 : 0);
      await page.getByTestId("choice-receipts").locator("summary").focus();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("link", { name: "Official House vote" })).toBeVisible();
      await expect(page.getByRole("link", { name: "Exact Senate-engrossed bill text" })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      expect(errors).toEqual([]);
    });
  }
}
test("unknown member never borrows another member's preview", async ({ page }) => {
  expect((await page.goto("/review/health-choice?member=F000478")).status()).toBe(404);
});
