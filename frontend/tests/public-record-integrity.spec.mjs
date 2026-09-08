import fs from "node:fs";
import { expect, test } from "@playwright/test";
import { installPassARoutes, positions } from "./pass-a-fixtures.mjs";

const candidate = JSON.parse(fs.readFileSync(
  "../docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/site_integration_candidate.json",
  "utf8",
));
const presentation = candidate.subject.presentation;
const reviewed = candidate.subject.receipt_projections.map((row) => ({
  ...row, interpretation_review_state: "reviewed_interpretation",
}));
const newAction = {
  canonical_action_id: "house:119:2:9999", roll_call_id: "synthetic-9999",
  chamber: "house", congress: 119, session: 2, rollcall_number: 9999,
  vote_date: "2026-07-01", position: "nay", issue_domain: "EDUCATION_WORKFORCE",
  description: "Additional education action", question: "On passage",
  source_url: "https://clerk.house.gov/",
  interpretation_review_state: "not_yet_in_reviewed_interpretation",
};

for (const additional of [false, true]) {
  test(`M14 findings stay fixed with ${additional ? 18 : 17} available actions`, async ({ page }) => {
    const rows = additional ? [...reviewed, newAction] : reviewed;
    await installPassARoutes(page, {
      presentationOverride: presentation,
      evidenceOverrides: { EDUCATION_WORKFORCE: rows },
      positionsOverride: {
        ...positions,
        positions: positions.positions.map((row) => row.domain === "EDUCATION_WORKFORCE"
          ? { ...row, total_votes: rows.length, reviewed_action_count: 17 }
          : row),
      },
    });
    await page.goto("/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119");
    await expect(page.locator("#issue-summary")).toContainText(`${rows.length} recorded actions currently visible`);
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope");
    await expect(page.locator("#issue-summary")).toContainText("3 findings supported by 6 votes");
    const analysis = page.getByTestId("reviewed-analysis");
    await expect(analysis).toContainText(presentation.overview.summary || presentation.overview.text || presentation.overview.title);
    for (const pattern of presentation.repeated_patterns) {
      await expect(analysis).toContainText(pattern.title);
    }
    await analysis.getByText("Other notable choices · 1").click();
    await expect(analysis).toContainText(presentation.notable_choices[0].title);
    await expect(analysis.locator(".semantic-label").filter({ hasText: /^Mixed$/ })).toHaveCount(1);
    if (additional) {
      await expect(page.locator("#issue-summary")).toContainText("1 additional recorded action is available below");
      const receipt = page.locator('article[data-canonical-action-id="house:119:2:9999"]');
      await expect(receipt).toContainText("Not yet included in the reviewed interpretation");
      await receipt.getByRole("button").click();
      await expect(receipt.getByRole("button")).toHaveAttribute("aria-expanded", "true");
      await expect(receipt).toContainText("Official sources");
      await expect(analysis).not.toContainText("Additional education action");
      await receipt.scrollIntoViewIfNeeded();
      await page.screenshot({ path: "test-results/public-record-additional-action.png" });
    } else {
      await expect(page.getByText("Not yet included in the reviewed interpretation", { exact: true })).toHaveCount(0);
      await expect(page.locator("#issue-summary")).not.toContainText("additional recorded");
    }
  });
}
