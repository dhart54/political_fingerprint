import { expect, test } from "@playwright/test";

const unsafeTopLevelPhrases = [
  "this was a direct vote",
  "records a direct position",
  "the House voted on whether",
  "the Senate voted on whether",
  "whether to agree to",
  "Amendment No.",
  "the amendment decreases",
  "the amendment redirects",
  "source basis",
  "classification reason",
  "House amendment vote",
  "other reviewed policy measures",
  "has the clearest pattern: mostly",
  "mostly opposed in the reviewed sample",
  "mostly supported in the reviewed sample",
];

test("golden fixture renders profile, issue reads, receipts, and safe top-level copy", async ({ page }) => {
  await page.goto("/golden-render-fixture");

  const profile = page.getByTestId("golden-valerie-profile");
  await expect(profile.getByRole("heading", { exact: true, name: "Valerie P. Foushee" })).toBeVisible();
  await expect(profile.getByText("This reviewed sample shows mostly opposed reads")).toBeVisible();
  await expect(profile.getByText("Start with the issue cards below, then open representative votes")).toBeVisible();

  await expect(profile.getByText("National Security & Foreign PolicyMostly opposed in reviewed sample")).toBeVisible();
  await expect(profile.getByText("Economy & TaxesMostly opposed in reviewed sample")).toBeVisible();
  await expect(profile.getByText("Justice & Public SafetyMostly opposed in reviewed sample")).toBeVisible();
  await expect(profile.getByText(/Immigration & Border Policy\s*4 votes\s*Mixed but interpretable/)).toBeVisible();

  await expect(profile.getByText("Issue summary")).toBeVisible();
  await expect(profile.getByText("Foushee mostly opposed the reviewed National Security & Foreign Policy measures")).toBeVisible();

  await assertTopLevelCopyIsSafe(profile);

  await profile.getByRole("button", { name: "Inspect Economy & Taxes votes" }).click();
  await expect(profile.getByText("Foushee mostly opposed the reviewed Economy & Taxes measures")).toBeVisible();

  await profile.getByRole("button", { name: "Inspect Justice & Public Safety votes" }).click();
  await expect(profile.getByText("Foushee mostly opposed the reviewed Justice & Public Safety measures")).toBeVisible();

  await profile.getByRole("button", { name: "Inspect Immigration & Border Policy votes" }).click();
  await expect(profile.getByText("mixed rather than mostly support or mostly opposition")).toBeVisible();

  await profile.getByRole("button", { name: "Inspect National Security & Foreign Policy votes" }).click();
  await expect(profile.getByText("Representative votes", { exact: true })).toBeVisible();
  await expect(profile.getByText("Full reviewed vote list", { exact: true })).toBeVisible();
  await profile.getByRole("button", { name: "Show all reviewed votes" }).click();
  await expect(profile.getByRole("button", { name: "Hide full list" })).toBeVisible();

  await profile.locator("summary", { hasText: "Source, caveats, and full context" }).first().click();
  await expect(profile.getByText("this was a direct vote").first()).toBeVisible();
  await profile.locator("summary", { hasText: "Details" }).first().click();
  await expect(profile.getByText("source basis fixture").first()).toBeVisible();

  await expect(profile.getByTestId("record-across-congresses-panel")).toBeVisible();
  await profile.getByTestId("record-across-congresses-summary").click();
  await expect(profile.getByText("Reviewed House vote evidence exists in both the 118th and 119th Congresses")).toBeVisible();

  const limited = page.getByTestId("golden-limited-profile");
  await expect(limited.getByText("Limited reviewed evidence").first()).toBeVisible();
  await expect(limited.getByText("1 reviewed Yes/No vote is available out of 10 recorded votes")).toBeVisible();
  await expect(limited.getByText("2 reviewed Yes/No votes are available out of 10 recorded votes")).toBeVisible();
  await expect(limited.getByText(/has the clearest pattern:\s*mostly/i)).toHaveCount(0);
  await expect(limited.getByText(/Mostly opposed in reviewed sample|Mostly supported in reviewed sample/i)).toHaveCount(0);

  await assertNoInternalText(page);
  await assertNoHorizontalOverflow(page);
});

test("golden fixture has no horizontal overflow at 390x844", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/golden-render-fixture");

  await expect(page.getByRole("heading", { name: "Golden public reads validation" })).toBeVisible();
  await expect(page.getByText("Valerie P. Foushee's clearest reviewed issue read")).toBeVisible();
  await expect(page.getByTestId("golden-limited-profile").getByText("Limited reviewed evidence").first()).toBeVisible();
  await assertNoInternalText(page);
  await assertNoHorizontalOverflow(page);
});

test("Foushee economy issue read is episode-aware and keeps secondary context bounded", async ({ page }) => {
  await page.goto("/golden-render-fixture");

  const slice = page.getByTestId("foushee-economy-editorial-gold").getByTestId("editorial-issue-experience");
  await expect(slice.getByTestId("editorial-review-label")).toContainText("not published");
  await expect(slice.getByText(/In this sample, Foushee voted against specific proposals involving government funding/)).toBeVisible();
  await expect(slice.getByText(/six substantive votes represent four policy episodes/i)).toBeVisible();
  await expect(slice.getByText(/not yet broad enough to establish one overarching Economy & Taxes philosophy/i)).toBeVisible();

  await expect(slice.getByText("Patterns in this sample", { exact: true })).toBeVisible();
  await expect(slice.getByText("Opposed both stages of the 2025 government-funding episode.")).toBeVisible();
  await expect(slice.getByText("Opposed both stages of the FY2025–FY2034 budget-framework episode.")).toBeVisible();
  await expect(slice.getByText("Opposed the House military-construction and veterans funding proposal.")).toBeVisible();
  await expect(slice.getByText("Opposed immigration-status restrictions on SBA-backed business loans.")).toBeVisible();

  for (const indicator of ["6 substantive votes", "4 policy episodes", "1 Not Voting", "2 context-only records"]) {
    await expect(slice.getByText(indicator, { exact: true })).toBeVisible();
  }
  await expect(slice.getByText("Voting context", { exact: true })).toBeVisible();
  await expect(slice.getByText(/with the majority of House Democrats on all 6 substantive roll calls in this sample/)).toBeVisible();
  await expect(slice.getByText(/does not explain why Foushee voted that way/)).toBeVisible();
  await expect(slice.getByText(/repeated stages are not separate policy positions/)).toBeVisible();
  await expect(slice.getByText("How to read this record", { exact: true })).toBeVisible();
  await expect(slice.getByText(/Repeated votes across independent policy episodes may support broader voting themes/)).toBeVisible();
  await expect(slice.getByText(/A voter who favored|A voter who opposed/)).toHaveCount(0);
});

test("Foushee economy vote accordion preserves approved copy and compact disclosure", async ({ page }) => {
  await page.goto("/golden-render-fixture");

  const slice = page.getByTestId("foushee-economy-editorial-gold").getByTestId("editorial-issue-experience");
  const notVoting = slice.getByTestId("editorial-record-roll-310");
  await expect(notVoting.getByText("Did not vote on proposed cap on net costs from SBA rules")).toBeVisible();
  await expect(notVoting.getByText("Foushee did not vote. The bill passed the House but had not become law.")).toBeVisible();

  const parentButtons = slice.locator('[data-testid^="editorial-record-"] > h6 > button');
  await expect(parentButtons).toHaveCount(9);
  for (let index = 0; index < 9; index += 1) {
    await expect(parentButtons.nth(index)).toHaveAttribute("aria-expanded", "false");
  }

  const houseProposal = slice.getByTestId("editorial-record-roll-182");
  const collapsedText = await houseProposal.innerText();
  expect(collapsedText).not.toContain("$17.509 billion");
  const houseButton = houseProposal.locator(":scope > h6 > button");
  await houseButton.click();
  await expect(houseButton).toHaveAttribute("aria-expanded", "true");
  await expect(houseProposal.getByText("What changed", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Before this vote", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Change at stake", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Impact and outcome", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Who it affected", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Scale and timing", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Outcome", { exact: true })).toBeVisible();
  for (const oldLabel of ["Prior baseline", "Mechanism", "Affected", "Scale or timing", "Next"]) {
    await expect(houseProposal.getByText(oldLabel, { exact: true })).toHaveCount(0);
  }
  await expect(houseProposal.getByText(/\$17\.509 billion/)).toBeVisible();

  const deeperSummary = houseProposal.getByText("Arguments, context, and sources", { exact: true });
  await expect(houseProposal.getByText("Supporters argued", { exact: true })).not.toBeVisible();
  await deeperSummary.click();
  await expect(houseProposal.getByText("Supporters argued", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Opponents argued", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Important context", { exact: true })).toBeVisible();
  const sourceDisclosure = houseProposal.getByText(/Official sources \(\d+\)/);
  await sourceDisclosure.click();
  await expect(houseProposal.getByText("Vote and legislative status", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Competing arguments", { exact: true })).toBeVisible();

  const revisedFramework = slice.getByTestId("editorial-record-roll-100");
  await expect(revisedFramework.getByText(/did not itself change taxes, benefits, annual funding, or the debt limit/)).toBeVisible();
  const revisedFrameworkButton = revisedFramework.locator(":scope > h6 > button");
  await revisedFrameworkButton.click();
  await expect(revisedFrameworkButton).toHaveAttribute("aria-expanded", "true");
  await expect(houseButton).toHaveAttribute("aria-expanded", "false");
  await expect(houseProposal.getByText("What changed", { exact: true })).not.toBeVisible();

  const initialFramework = slice.getByTestId("editorial-record-roll-50");
  await expect(initialFramework.getByText(/did not itself change taxes, benefits, annual funding, or the debt limit/)).toBeVisible();

  const control = slice.getByTestId("editorial-record-context-263");
  await expect(control).toContainText("nonbinding request");
  await control.locator(":scope > h6 > button").focus();
  await page.keyboard.press("Enter");
  await expect(control.locator(":scope > h6 > button")).toHaveAttribute("aria-expanded", "true");
  await expect(revisedFrameworkButton).toHaveAttribute("aria-expanded", "false");
  await expect(slice.getByTestId("editorial-record-context-180")).toContainText("package of seven different amendments");

  const publicText = await slice.innerText();
  expect(publicText).not.toMatch(/claim_id|source_id|human_approval_pending|gold_benchmark|agent_confidence|review question/i);
  await assertNoHorizontalOverflow(page);
});

test("Foushee economy read remains usable across wide, laptop, tablet, and mobile widths", async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 1000 },
    { width: 1024, height: 768 },
    { width: 768, height: 1024 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/golden-render-fixture");

    const slice = page.getByTestId("foushee-economy-editorial-gold").getByTestId("editorial-issue-experience");
    await expect(slice.getByText("Patterns in this sample", { exact: true })).toBeVisible();
    const revisedFramework = slice.getByTestId("editorial-record-roll-100");
    await revisedFramework.locator(":scope > h6 > button").click();
    await expect(revisedFramework.getByText("What changed", { exact: true })).toBeVisible();
    await expect(revisedFramework.getByText("Impact and outcome", { exact: true })).toBeVisible();
    await assertNoHorizontalOverflow(page);
  }
});

test("pending editorial slice uses the basic representative fallback in production mode", async ({ page }) => {
  await page.goto("/golden-render-fixture#foushee-production-gate-fixture");
  const fixture = page.getByTestId("foushee-production-gate-fixture");
  await expect(fixture.getByRole("heading", { name: "Production-mode representative issue evidence" })).toBeVisible();
  await expect(fixture.getByTestId("editorial-issue-experience")).toHaveCount(0);
  await expect(fixture.getByText("Issue summary", { exact: true })).toBeVisible();
  await expect(fixture.getByText("Representative votes", { exact: true })).toBeVisible();
  await expect(fixture.getByText("Full reviewed vote list", { exact: true })).toBeVisible();
  await expect(fixture.getByRole("button", { name: "Show all reviewed votes" })).toBeVisible();
});

test("synthetic fixture proves generic identity, mixed actions, optional omission, source counts, and accessibility", async ({ page }) => {
  await page.goto("/golden-render-fixture#synthetic-editorial-fixture");

  const fixture = page.getByTestId("synthetic-editorial-fixture");
  const slice = fixture.getByTestId("editorial-issue-experience");
  await expect(slice.getByRole("heading", { name: "Jordan Example \u2014 Synthetic Energy Choices" })).toBeVisible();
  await expect(slice.getByText(/deliberately mixed/i)).toBeVisible();
  for (const indicator of ["2 substantive votes", "2 policy episodes", "1 Not Voting", "1 context-only record"]) {
    await expect(slice.getByText(indicator, { exact: true })).toBeVisible();
  }
  await expect(slice.getByText("Voting context", { exact: true })).toHaveCount(0);
  await expect(slice.getByText("How to read this record", { exact: true })).toHaveCount(0);
  await expect(fixture.getByText("Additional reviewed vote list", { exact: true })).toHaveCount(0);
  await expect(fixture.getByText("0 reviewed votes", { exact: true })).toHaveCount(0);
  await expect(fixture.getByText("0 evidence groups", { exact: true })).toHaveCount(0);

  const supported = slice.getByTestId("editorial-record-roll-41");
  const opposed = slice.getByTestId("editorial-record-roll-57");
  const notVoting = slice.getByTestId("editorial-record-roll-63");
  const context = slice.getByTestId("editorial-record-context-72");
  await expect(notVoting).toHaveAttribute("data-inclusion-class", "not_voting");
  await expect(context).toHaveAttribute("data-inclusion-class", "context_only");

  const supportedButton = supported.locator(":scope > h6 > button");
  const opposedButton = opposed.locator(":scope > h6 > button");
  await supportedButton.focus();
  await page.keyboard.press("Enter");
  await expect(supportedButton).toHaveAttribute("aria-expanded", "true");
  await supported.getByText("Arguments, context, and sources", { exact: true }).click();
  await supported.getByText("Official sources (2)", { exact: true }).click();
  await expect(supported.getByText("Vote and legislative status", { exact: true })).toBeVisible();
  await expect(supported.getByText("Bill or resolution text", { exact: true })).toBeVisible();

  await opposedButton.click();
  await expect(opposedButton).toHaveAttribute("aria-expanded", "true");
  await expect(supportedButton).toHaveAttribute("aria-expanded", "false");
  await opposedButton.click();
  await supportedButton.click();
  await expect(supported.getByText("Supporters argued", { exact: true })).not.toBeVisible();
  await assertNoHorizontalOverflow(page);
});

test("Foushee review renders a generic additional list only for uncovered evidence", async ({ page }) => {
  await page.goto("/golden-render-fixture#foushee-economy-editorial-gold");
  const fixture = page.getByTestId("foushee-economy-editorial-gold");
  await expect(fixture.getByText("Additional reviewed vote list", { exact: true })).toBeVisible();
  await expect(fixture.getByText("1 reviewed votes", { exact: true })).toBeVisible();
  await expect(fixture.getByText("1 evidence groups", { exact: true })).toBeVisible();
  await expect(fixture.getByText(/remaining receipts stay available here/i)).toBeVisible();
  await expect(fixture).not.toContainText("nine records");
});

test("synthetic generic fixture renders without overflow on mobile and tablet", async ({ page }) => {
  for (const viewport of [{ width: 768, height: 1024 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.goto(`/golden-render-fixture?viewport=${viewport.width}#synthetic-editorial-fixture`);
    const fixture = page.getByTestId("synthetic-editorial-fixture");
    await expect(fixture.getByText("Synthetic mixed pattern", { exact: true })).toBeVisible();
    await fixture.getByTestId("editorial-record-roll-57").locator(":scope > h6 > button").click();
    await expect(fixture.getByText("What changed", { exact: true })).toBeVisible();
    await assertNoHorizontalOverflow(page);
  }
});

async function assertTopLevelCopyIsSafe(profile) {
  const text = await profile.innerText();
  const receiptHeading = text.match(/\nRepresentative votes\n/i);
  const topLevelText = receiptHeading ? text.slice(0, receiptHeading.index) : text;
  for (const phrase of unsafeTopLevelPhrases) {
    expect(topLevelText.toLowerCase(), `top-level copy should not include ${phrase}`).not.toContain(phrase.toLowerCase());
  }
}

async function assertNoInternalText(page) {
  const text = await page.locator("body").innerText();
  expect(text).not.toMatch(/INTERNAL_API_TOKEN|X-Internal-API-Token|\/internal\/record-across-congresses/);
}

async function assertNoHorizontalOverflow(page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(overflow).toBe(false);
}
