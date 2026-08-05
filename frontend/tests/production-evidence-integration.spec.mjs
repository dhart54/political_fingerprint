import { expect, test } from "@playwright/test";

import { installPassARoutes } from "./pass-a-fixtures.mjs";
import {
  selectedIssueEvidence118 as evidence118,
  selectedIssueEvidence119 as evidence119,
  selectedIssueEvidenceForScope as evidenceForScope,
  selectedIssueReview as fixture,
} from "./selected-issue-fixtures.mjs";

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page, {
    justiceEvidenceOverride: evidenceForScope,
    justicePresentationOverride: fixture.presentation,
  });
});

test("selected issue separates all-Congress evidence from the governed interpretation scope", async ({ page }) => {
  expect(evidence119).toHaveLength(37);
  expect(evidence119.filter((row) => row.governed_receipt_projection)).toHaveLength(35);
  expect(evidence119.filter((row) => row.governed_receipt_control)).toHaveLength(2);
  expect(evidence118).toHaveLength(52);
  expect(evidence118.filter((row) => row.governed_receipt_projection)).toHaveLength(0);
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY",
  );

  const detail = page.getByTestId("issue-detail");
  await expect(detail).toContainText("Recorded actions shown");
  await expect(detail).toContainText("All available Congresses");
  await expect(detail).toContainText("89 recorded actions currently visible");
  await expect(detail).toContainText("Reviewed interpretation");
  await expect(detail).toContainText("119th Congress · full defined issue record");
  await expect(detail).toContainText("37 reviewed actions · 32 policy episodes");
  await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
  await expect(page.getByText("89 recorded actions. Newest first")).toBeVisible();
});

test("119th and 118th scope states preserve their distinct evidence contracts", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );
  await expect(page.getByTestId("issue-detail")).toContainText(
    "37 recorded actions currently visible",
  );
  await expect(page.getByTestId("reviewed-analysis")).toContainText(
    "Full reviewed record",
  );
  await expect(page.getByTestId("reviewed-analysis")).toContainText(
    "37 reviewed actions",
  );

  await page.getByRole("button", { name: "118th Congress" }).click();
  await expect(page).toHaveURL(/scope=118/);
  await expect(page.getByTestId("issue-detail")).toContainText(
    "52 recorded actions currently visible",
  );
  await expect(page.getByTestId("issue-detail")).toContainText(
    "Not published for this scope",
  );
  await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
  await expect(page.getByText("52 recorded actions. Newest first")).toBeVisible();
});

test("scan-first pattern index preserves governed action and episode accounting", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );

  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText(
    "One meaningful contrast in the reviewed record is opposition to the reviewed displacement of D.C. public-safety rules alongside support for two terrorism-preparedness mandates; separate firearm-access and fraud-enforcement patterns remain primary findings.",
  );
  await expect(analysis).not.toContainText(
    "One bounded contrast within a record with four primary patterns",
  );
  await expect(analysis).toContainText("Patterns in this issue record");
  await expect(analysis).not.toContainText("Bar length reflects");
  await expect(analysis).not.toContainText("Across six separate episodes.");
  await expect(analysis).toContainText("6 exact actions · 6 episodes");
  await expect(analysis).toContainText("3 exact actions · 3 episodes");
  await expect(analysis).toContainText("2 exact actions · 2 episodes");
  await expect(analysis.getByText("2 exact actions · 2 episodes")).toHaveCount(2);
  await expect(analysis).toContainText("3 exact actions · 1 episode");
  await expect(analysis.getByRole("button", { name: /Show .* exact actions for/ })).toHaveCount(5);
  await expect(analysis).toContainText(
    "Based on reviewed recorded actions; this does not infer motive, ideology, character, future behavior, or voting advice.",
  );
});

test("pattern focus filters exact actions, explains mixed episode accounting, and clears", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );

  await page.getByRole("button", {
    name: /Show 3 exact actions for The HALT Fentanyl path is one mixed episode/,
  }).click();
  await expect(page.getByText("Selected pattern")).toBeVisible();
  await expect(page.getByText(/Showing 3 exact actions across 1 policy episode/)).toBeVisible();
  await expect(page.getByText(/no single action or stage is presented as the complete episode/)).toBeVisible();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "Chronological action ledger" }),
  ).toBeFocused();

  await page.getByRole("button", { name: "Return to all 37 actions" }).click();
  await expect(page.getByRole("button", { name: "All", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByText(/Showing the first 12/)).toBeVisible();
});

test("all five pattern controls resolve exact governed counts and scope-all clear restores 89", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY",
  );
  const patterns = [
    ["Opposition to displacing D.C. public-safety rules", 6],
    ["Opposition to reducing firearm-access barriers", 3],
    ["Opposition to expanding fraud-enforcement capacity", 2],
    ["Support for terrorism-preparedness mandates", 2],
    ["The HALT Fentanyl path is one mixed episode", 3],
  ];
  for (const [name, count] of patterns) {
    await page.getByRole("button", {
      name: new RegExp(`Show ${count} exact actions for ${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`),
    }).click();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(count);
    await page.getByRole("button", { name: "Return to all 89 actions" }).click();
  }
  await expect(page.getByText(/89 recorded actions\. Newest first/)).toBeVisible();
  await expect(page.getByText(/Showing the first 12/)).toBeVisible();
});

test("limitations are collapsed, complete, and bounded to supplied review language", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );
  const summary = page.getByText("Limitations and unresolved actions · 3");
  await expect(summary).toBeVisible();
  await expect(page.getByText("Roll 128: resolved scope only")).not.toBeVisible();
  await summary.click();
  await expect(page.getByText("Roll 128: resolved scope only")).toBeVisible();
  await expect(page.getByText("Roll 155: source identity conflict")).toBeVisible();
  await expect(page.getByText("Roll 278: no safe final-package meaning")).toBeVisible();
});

test("related NDAA actions remain five independent receipts with the control visible", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );
  const group = page.getByTestId("related-action-group").filter({
    hasText: "National Defense Authorization Act for Fiscal Year 2027",
  });
  await expect(group).toHaveCount(1);
  await expect(group).toContainText("Related actions · 5 individual votes");
  await expect(group).toContainText("5 Nay");
  await expect(group).toContainText("1 governed non-counting control");
  await expect(group.locator("[data-canonical-action-id]")).toHaveCount(5);
  await expect(group).toContainText(
    "This is a navigation group, not an aggregate vote.",
  );

  const roll278 = group.locator('[data-canonical-action-id="house:119:2:278"]');
  await expect(roll278).toContainText("Governed non-counting control");
  await roll278.getByRole("button").click();
  await expect(roll278).toContainText("Material context or limitations");

  await page.getByRole("button", { name: "Procedural / context" }).click();
  await expect(page.getByText(/Showing 2 of 2 matching actions/)).toBeVisible();
  await expect(page.locator('[data-canonical-action-id="house:119:2:155"]')).toContainText(
    "Governed non-counting control",
  );
  await expect(page.locator('[data-canonical-action-id="house:119:2:278"]')).toContainText(
    "Governed non-counting control",
  );
});

test("standard rows omit review status and representative standalone actions use meaningful titles", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );
  while (await page.getByRole("button", { name: "Show more actions" }).count()) {
    await page.getByRole("button", { name: "Show more actions" }).click();
  }
  const expectedTitles = new Map([
    [218, "Fraud Prevention and Accountability Act"],
    [221, "To amend the FISA Amendments Act of 2008"],
    [227, "Financial Exploitation Prevention Act"],
    [234, "Weatherizing Infrastructure in the North and Terrorism Emergency Readiness Act"],
    [240, "Protecting Privacy in Purchases Act"],
  ]);
  for (const [roll, title] of expectedTitles) {
    const row = page.locator(`[data-canonical-action-id="house:119:2:${roll}"]`);
    await expect(row.getByRole("button")).toContainText(title);
    await expect(row.getByRole("button")).not.toContainText("Reviewed");
    await expect(row.getByRole("button")).not.toContainText(new RegExp(`(?:Passage|Suspension passage) · Roll ${roll}`));
  }
});

test("compact rows defer exact meaning to the expanded voter receipt and expose no internal metadata", async ({ page }) => {
  await page.goto(
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );
  const roll275 = page.locator('[data-canonical-action-id="house:119:2:275"]');
  await expect(roll275.getByRole("button")).toContainText(
    "Bar federal funding for automated speed-enforcement cameras",
  );
  await expect(roll275.getByRole("button")).not.toContainText(
    "The House choice was whether",
  );
  await roll275.getByRole("button").click();
  await expect(roll275).toContainText("Exact-action meaning");
  await expect(roll275).not.toContainText("Policy question");
  await expect(roll275).toContainText("Representative vote");
  await expect(roll275).toContainText("Chamber result: passed");
  await expect(roll275).not.toContainText("Policy-episode relationship");
  await expect(roll275).toContainText("Official vote");
  await expect(roll275).toContainText("Official bill or amendment material");

  const publicText = await page.locator("body").textContent();
  for (const forbidden of [
    "acceptance_receipt",
    "action-interpretation-decision-implementation",
    "delegated_acceptance",
    "delegated_episode",
    "launch_ratification",
    "implementation_id",
    "milestone",
    "M3BB",
    "M4B",
    "M5R1",
    "Interpretation digest",
    "Provenance references",
    "Human-reviewed",
    "About this interpretation",
    "candidate_content_sha256",
    "reviewed_at",
    "semantic_ir_acceptance",
    "SHA-256",
    "user_launch_ratification",
    "2026-08-04",
  ]) {
    expect(publicText).not.toContain(forbidden);
  }
  expect(publicText).not.toMatch(/docs[\\/]/i);
  expect(publicText).not.toMatch(/\b[a-f0-9]{40,}\b/i);
});
