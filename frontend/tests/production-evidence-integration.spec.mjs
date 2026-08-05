import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";


const fixture = JSON.parse(fs.readFileSync(
  path.resolve("fixtures/foushee_justice_m6_review.json"),
  "utf8",
));

const controls = new Map([
  ["house:119:2:155", "context_only_control_exclusion"],
  ["house:119:2:278", "exact_action_eligibility"],
]);

const evidence = fixture.ledger.map((record) => ({
  canonical_action_id: record.canonical_action_id,
  chamber: "house",
  congress: 119,
  rollcall_number: record.roll_call,
  vote_date: record.date,
  vote_type: record.legislative_stage,
  description: `House roll ${record.roll_call}`,
  position: record.member_action,
  interpretation_status: record.non_proposition_state || "interpreted",
  plain_english_summary:
    record.governed_action_meaning
    || "No safe public analytical meaning is available for this action.",
  question:
    record.governed_action_meaning
    || "The exact final-package policy question remains unresolved.",
  uncertainty_note: record.limitations.join(" "),
  source_url: record.official_vote_source?.[0]?.url,
  source_basis: (record.official_action_meaning_sources || []).map((source) => ({
    label: source.source_id,
    url: source.url,
  })),
  governed_receipt_control: controls.has(record.canonical_action_id)
    ? {
        status: "noncounting_control",
        boundary_type: controls.get(record.canonical_action_id),
        detail: record.limitations.join(" "),
      }
    : undefined,
}));

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page, {
    justiceEvidenceOverride: evidence,
    justicePresentationOverride: fixture.presentation,
  });
});

test("launched representative page renders the 37-action governed ledger", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );

  await expect(page.getByTestId("issue-detail").getByRole("alert")).toHaveCount(0);
  await expect(page.getByText(
    "The exact vote receipts for this issue are unavailable right now.",
  )).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Chronological action ledger" })).toBeVisible();
  await expect(page.getByText("All 37 recorded actions remain available.")).toBeVisible();
  await expect(page.getByText(/Showing 12 of 37 matching actions/)).toBeVisible();

  await page.getByRole("button", { name: "Procedural / context" }).click();
  await expect(page.getByText(/Showing 2 of 2 matching actions/)).toBeVisible();
  const roll278 = page.locator('[data-canonical-action-id="house:119:2:278"]');
  await roll278.getByRole("button").click();
  await expect(roll278).toContainText("Governed non-counting control");
});
