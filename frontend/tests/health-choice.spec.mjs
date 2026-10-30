import { test, expect } from "@playwright/test";
import fs from "node:fs";
import { installHealthRoutes, responseFor } from "./health-choice-routes.mjs";

for (const member of ["F000477", "M001184"]) {
  for (const scope of ["119", "all", "118"]) {
    for (const [viewport, width, height] of [["desktop",1280,900],["mobile",390,844]]) {
      test(`${member} ${scope} ${viewport}: normal representative API ingestion`, async ({page}) => {
        await page.setViewportSize({width,height});
        const errors=[]; page.on("pageerror", (e)=>errors.push(e.message));
        const profile=await installHealthRoutes(page,member);
        await page.goto(`/?representative=${profile.id}&issue=HEALTH_SOCIAL&scope=${scope}`);
        const card=page.getByTestId("bounded-choice-review");
        if (scope==="118") {
          await expect(page.getByTestId("issue-card")).not.toHaveCount(0);
          await expect(card).toHaveCount(0);
        } else {
          const presentation=responseFor(member,scope).presentations.find((p)=>p.issue_id==="HEALTH_SOCIAL").bounded_choice;
          await expect(card).toHaveAttribute("data-presentation-sha256",presentation.presentation_subject_sha256);
          await expect(card).toContainText("119th Congress");
          for (const record of Object.values(presentation.records)) await expect(card).toContainText(record.text);
          await expect(page.getByTestId("supporting-choice")).toHaveCount(member==="F000477"?1:0);
          await expect(page.getByTestId("not-voting-accounting")).toHaveCount(member==="M001184"?1:0);
          const overview=page.getByTestId("issue-card").filter({has:page.getByRole("heading",{name:"Health & Social Services",exact:true})});
          await expect(overview).toContainText(member==="F000477"?"Reviewed choice available":"Not Voting record available");
          await expect(overview).not.toContainText("Issue summary available");
          if(member==="F000477") {
            await page.getByRole("button",{name:"Explore Justice & Public Safety",exact:true}).click();
            await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
          }
        }
        expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
        expect(errors).toEqual([]);
      });
    }
  }
}

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
