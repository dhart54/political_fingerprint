import { expect, test } from "@playwright/test";

import {
  canonicalActionId,
  filterActionsByDimensions,
} from "../lib/frontendPassA.mjs";
import { installPassARoutes } from "./pass-a-fixtures.mjs";
import {
  selectedIssueEvidence118 as evidence118,
  selectedIssueEvidence119 as evidence119,
  selectedIssueEvidenceForScope as evidenceForScope,
  selectedIssueReview as fixture,
} from "./selected-issue-fixtures.mjs";

const selectedPath = "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY";

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page, {
    justiceEvidenceOverride: evidenceForScope,
    justicePresentationOverride: fixture.presentation,
  });
});

test("header and scope strip preserve one bounded selected-issue hierarchy", async ({ page }) => {
  expect(evidence119).toHaveLength(37);
  expect(evidence119.filter((row) => row.governed_receipt_projection)).toHaveLength(35);
  expect(evidence119.filter((row) => row.governed_receipt_control)).toHaveLength(2);
  expect(evidence118).toHaveLength(52);
  await page.goto(selectedPath);

  const header = page.locator("main > header");
  await expect(header.getByRole("link", { name: "Political Fingerprint" })).toBeVisible();
  await expect(header.getByRole("navigation", { name: "Selected issue sections" })).toContainText(
    "IssuesIssue summaryVote record",
  );
  await expect(header.getByRole("link", { name: "Valerie P. Foushee" })).toHaveAttribute(
    "href",
    "#representative-name",
  );
  for (const absent of ["About", "How it works", "Save", "Search"]) {
    await expect(header).not.toContainText(absent);
  }

  const summary = page.locator("#issue-summary");
  await expect(summary).toContainText("Recorded actions shown");
  await expect(summary).toContainText("All available Congresses");
  await expect(summary).toContainText("89 recorded actions currently visible");
  await expect(summary).toContainText("Issue summary covers");
  await expect(summary).toContainText("119th Congress");
  await expect(summary).toContainText("37 votes across 32 legislative episodes");
  await expect(page.getByTestId("reviewed-analysis")).not.toContainText("37 reviewed actions");
  await expect(page.getByRole("heading", { name: "Vote record" })).toBeVisible();
});

test("119th and 118th scope states remain distinct", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  await expect(page.locator("#issue-summary")).toContainText("37 recorded actions currently visible");
  await expect(page.locator("#issue-summary")).toContainText(
    "37 votes across 32 legislative episodes",
  );
  await expect(page.getByTestId("reviewed-analysis")).toBeVisible();

  await page.getByRole("button", { name: "118th Congress" }).click();
  await expect(page).toHaveURL(/scope=118/);
  const summary118 = page.locator("#issue-summary");
  await expect(summary118).toContainText("52 recorded actions currently visible");
  await expect(summary118).toContainText("No issue summary for this scope");
  await expect(summary118).toContainText("Vote receipts remain available");
  await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
  await expect(page.getByText(/52 recorded actions · Newest first/)).toBeVisible();
});

test("all governed patterns are visible with symbols, copy, counts, and one action", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  const analysis = page.getByTestId("reviewed-analysis");
  await expect(analysis).toContainText(
    "One meaningful contrast in the reviewed record is opposition to the reviewed displacement of D.C. public-safety rules alongside support for two terrorism-preparedness mandates; separate firearm-access and fraud-enforcement patterns remain primary findings.",
  );
  await expect(analysis).toContainText("Patterns in this issue record");
  await expect(analysis).not.toContainText("Read pattern explanation");
  await expect(analysis).not.toContainText("Bar length reflects");

  const patterns = [
    ["Opposition to displacing D.C. public-safety rules", "Opposition", "6 votes · 6 episodes", "−"],
    ["Opposition to reducing firearm-access barriers", "Opposition", "3 votes · 3 episodes", "−"],
    ["Opposition to expanding fraud-enforcement capacity", "Opposition", "2 votes · 2 episodes", "−"],
    ["Support for terrorism-preparedness mandates", "Support", "2 votes · 2 episodes", "+"],
    ["The HALT Fentanyl path is one mixed episode", "Mixed", "3 votes within 1 episode", "±"],
  ];
  for (const [heading, status, accounting, symbol] of patterns) {
    const row = analysis.locator("article").filter({ hasText: heading });
    await expect(row).toContainText(status);
    await expect(row).toContainText(symbol);
    await expect(row).toContainText(accounting);
    await expect(row.locator("p")).not.toBeEmpty();
    await expect(row.getByRole("button", { name: new RegExp(`View \\d+ votes for ${escapeRegex(heading)}`) })).toHaveCount(1);
  }
  await expect(analysis).toContainText(
    "Based on reviewed recorded actions; this does not infer motive, ideology, character, future behavior, or voting advice.",
  );
});

test("exceptional action states render distinct symbols with text while substantive actions stay plain", async ({ page }) => {
  await page.unrouteAll({ behavior: "wait" });
  const base = evidence119.find((row) => !row.governed_receipt_control);
  const rows = [
    exceptionalRow(base, 901, { interpretation_status: "interpreted" }),
    exceptionalRow(base, 902, {
      vote_type: "procedural",
      interpretation_status: "procedural_context",
    }),
    exceptionalRow(base, 903, {
      governed_receipt_control: { status: "noncounting_control" },
    }),
    exceptionalRow(base, 904, { interpretation_status: "ambiguous" }),
    exceptionalRow(base, 905, { interpretation_status: "insufficient_evidence" }),
  ];
  await installPassARoutes(page, {
    justiceEvidenceOverride: rows,
    justicePresentationOverride: fixture.presentation,
  });
  await page.goto(`${selectedPath}&scope=119`);

  const expectations = [
    [902, "procedural", "Procedural / context", "↪"],
    [903, "noncounting", "Non-counting control", "○"],
    [904, "limited", "Limited context", "?"],
    [905, "unresolved", "Unresolved evidence", "!"],
  ];
  for (const [roll, kind, label, symbol] of expectations) {
    const receipt = page.locator(`[data-canonical-action-id="house:119:2:${roll}"]`);
    const status = receipt.locator(`[data-action-status="${kind}"]`);
    await expect(status).toContainText(label);
    await expect(status).toContainText(symbol);
    await expect(receipt.locator("[data-action-status]")).toHaveCount(1);
  }
  await expect(
    page.locator('[data-canonical-action-id="house:119:2:901"] [data-action-status]'),
  ).toHaveCount(0);
});

test("pattern navigation alone creates the compact selected-pattern strip and clears", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  const action = page.getByRole("button", {
    name: /View 3 votes for The HALT Fentanyl path is one mixed episode/,
  });
  await action.focus();
  await page.keyboard.press("Enter");
  const strip = page.locator(".pattern-strip");
  await expect(strip).toContainText("Mixed");
  await expect(strip).toContainText("3 votes within 1 legislative episode");
  await expect(strip).not.toContainText("bounded evidence");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
  await expect(page.getByRole("heading", { name: "Vote record" })).toBeFocused();

  await strip.getByRole("button", { name: "Show all 37 votes" }).click();
  await expect(strip).toHaveCount(0);
  await expect(page.getByRole("button", { name: "All", exact: true }).first()).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});

test("every pattern action resolves its exact canonical identities", async ({ page }) => {
  await page.goto(selectedPath);
  await expect(page.getByTestId("issue-detail")).toBeVisible();
  const patterns = [
    ...(fixture.presentation.repeated_patterns || []),
    ...(fixture.presentation.policy_trajectories || []),
  ];
  for (const pattern of patterns) {
    await page.getByRole("button", {
      name: new RegExp(`View ${pattern.action_ids.length} votes for ${escapeRegex(pattern.heading)}`),
    }).click();
    await expect(page.locator(".pattern-strip")).toBeVisible();
    const actual = await page.locator("[data-canonical-action-id]").evaluateAll(
      (elements) => elements.map((element) => element.dataset.canonicalActionId).sort(),
    );
    expect(actual).toEqual([...pattern.action_ids].sort());
    await page.getByRole("button", { name: "Show all 89 votes" }).click();
  }
});

test("ordinary Nay expansion and Nay filtering never create Opposition state", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  const roll240 = page.locator('[data-canonical-action-id="house:119:2:240"]');
  await roll240.getByRole("button").click();
  await expect(roll240.getByRole("button")).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator(".pattern-strip")).toHaveCount(0);

  const voteFilters = page.getByRole("group", { name: "Vote" });
  await voteFilters.getByRole("button", { name: "Nay" }).click();
  await expect(page.locator(".pattern-strip")).toHaveCount(0);
  await expect(voteFilters.getByRole("button", { name: "Nay" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});

test("Vote and Type filters combine over exact production-shaped actions", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  const expectedIds = filterActionsByDimensions(evidence119, {
    vote: "nay",
    type: "substantive",
  }).map(canonicalActionId).sort();
  await page.getByRole("group", { name: "Vote" }).getByRole("button", { name: "Nay" }).click();
  await page.getByRole("group", { name: "Type" }).getByRole("button", { name: "Substantive" }).click();
  while (await page.getByRole("button", { name: "Show more votes" }).count()) {
    await page.getByRole("button", { name: "Show more votes" }).click();
  }
  const actualIds = await page.locator("[data-canonical-action-id]").evaluateAll(
    (elements) => elements.map((element) => element.dataset.canonicalActionId).sort(),
  );
  expect(actualIds).toEqual(expectedIds);
  await expect(page.locator(".pattern-strip")).toHaveCount(0);
});

test("related actions use a non-collapsible parent and keep every child independently usable", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  const group = page.getByTestId("related-action-group").filter({
    hasText: "National Defense Authorization Act for Fiscal Year 2027",
  });
  await expect(group).toContainText("· 5 votes");
  await expect(group).toContainText("5 Nay · 1 non-counting control");
  await expect(group.locator("summary")).toHaveCount(0);
  await expect(group).not.toContainText("navigation group");
  await expect(group).not.toContainText("Parent measure:");
  await expect(group.locator("[data-canonical-action-id]")).toHaveCount(5);

  for (const receipt of await group.locator("[data-canonical-action-id]").all()) {
    const button = receipt.getByRole("button");
    await button.focus();
    await expect(button).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(button).toHaveAttribute("aria-expanded", "true");
    await expect(receipt.getByRole("link").first()).toBeVisible();
  }
  await expect(group.locator('[data-canonical-action-id="house:119:2:278"]')).toContainText(
    "Non-counting control",
  );
});

test("an NDAA action filtered out of its group retains parent-measure context", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  await page.getByRole("button", {
    name: "View 3 votes for Opposition to reducing firearm-access barriers",
  }).click();

  const strip = page.locator(".pattern-strip");
  await expect(strip).toContainText("Opposition");
  await expect(strip).toContainText("reducing firearm-access barriers");
  await expect(strip).toContainText("3 matching votes");
  await expect(strip.getByRole("button", { name: "Show all 37 votes" })).toBeVisible();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
  await expect(
    page.locator('[data-canonical-action-id="house:119:2:265"]'),
  ).toContainText("Parent measure: National Defense Authorization Act for Fiscal Year 2027");
});

test("pagination reaches all 89 unique actions without group omissions", async ({ page }) => {
  await page.goto(selectedPath);
  await expect(page.getByTestId("issue-detail")).toBeVisible();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  while (await page.getByRole("button", { name: "Show more votes" }).count()) {
    await page.getByRole("button", { name: "Show more votes" }).click();
  }
  const ids = await page.locator("[data-canonical-action-id]").evaluateAll(
    (elements) => elements.map((element) => element.dataset.canonicalActionId),
  );
  expect(ids).toHaveLength(89);
  expect(new Set(ids).size).toBe(89);
});

test("expanded receipts use voter-facing organization and remain metadata-clean", async ({ page }) => {
  await page.goto(`${selectedPath}&scope=119`);
  const roll275 = page.locator('[data-canonical-action-id="house:119:2:275"]');
  await expect(roll275.getByRole("button")).not.toContainText("Chamber result");
  await roll275.getByRole("button").click();
  for (const label of [
    "What this vote was about",
    "How Valerie P. Foushee voted",
    "Result",
    "Important context",
    "Official sources",
  ]) {
    await expect(roll275).toContainText(label);
  }
  await expect(roll275).not.toContainText("What the proposal would do");
  await expect(roll275).toContainText("Passed in the House");
  await expect(roll275).toContainText("Official vote");
  await expect(roll275).toContainText(/Bill or amendment text|Official report/);
  for (const oldLabel of [
    "Exact-action meaning",
    "Policy question",
    "Material context or limitations",
    "Representative vote",
    "Result and current status",
  ]) {
    await expect(roll275).not.toContainText(oldLabel);
  }
  await expect(roll275).not.toContainText(/candidate|does not establish motive/i);

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

test("keyboard, reduced motion, mobile reflow, and 200 percent zoom remain bounded", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${selectedPath}&scope=119`);
  await expect(page.getByRole("group", { name: "Vote" })).toBeVisible();
  await expect(page.getByRole("group", { name: "Type" })).toBeVisible();
  const scopeCells = await page.locator("#issue-summary dl > div").evaluateAll((cells) => (
    cells.map((cell) => cell.getBoundingClientRect().top)
  ));
  expect(scopeCells[1]).toBeGreaterThan(scopeCells[0]);
  await assertNoHorizontalOverflow(page);

  const roll275 = page.locator('[data-canonical-action-id="house:119:2:275"]');
  await roll275.getByRole("button").focus();
  await page.keyboard.press("Enter");
  await expect(roll275.getByRole("button")).toHaveAttribute("aria-expanded", "true");
  await expect(roll275.getByRole("link", { name: "Official vote" })).toBeVisible();
  await assertNoHorizontalOverflow(page);

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => { document.documentElement.style.zoom = "2"; });
  await assertNoHorizontalOverflow(page);
  await expect(page.getByRole("heading", { name: "Vote record" })).toBeVisible();
});

async function assertNoHorizontalOverflow(page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
}

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function exceptionalRow(base, roll, overrides = {}) {
  return {
    ...base,
    canonical_action_id: `house:119:2:${roll}`,
    rollcall_number: roll,
    vote_date: `2026-07-${String(roll - 900).padStart(2, "0")}`,
    vote_type: "passage",
    description: `Exceptional action fixture ${roll}`,
    interpretation_status: "interpreted",
    bill_title: undefined,
    amendment_purpose: undefined,
    governed_receipt_projection: undefined,
    governed_receipt_control: undefined,
    ...overrides,
  };
}
