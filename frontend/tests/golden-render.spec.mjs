import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

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
  await expect(profile.getByText(/Immigration & Border Policy\s*4 votes\s*Evidence in more than one direction/)).toBeVisible();

  await expect(profile.getByTestId("basic-evidence-summary").getByText("Vote evidence", { exact: true })).toBeVisible();
  await expect(profile.getByTestId("basic-evidence-summary").getByText(/These receipts show recorded actions; this basic view does not combine them into a broader issue conclusion/i)).toBeVisible();

  await assertTopLevelCopyIsSafe(profile);

  await profile.getByRole("button", { name: "Inspect Economy & Taxes votes" }).click();
  await expect(profile.getByTestId("basic-evidence-summary").getByText(/These receipts show recorded actions/i)).toBeVisible();

  await profile.getByRole("button", { name: "Inspect Justice & Public Safety votes" }).click();
  await expect(profile.getByTestId("basic-evidence-summary").getByText(/These receipts show recorded actions/i)).toBeVisible();

  await profile.getByRole("button", { name: "Inspect Immigration & Border Policy votes" }).click();
  await expect(profile.getByTestId("basic-evidence-summary").getByText(/does not combine them into a broader issue conclusion/i)).toBeVisible();

  await profile.getByRole("button", { name: "Inspect National Security & Foreign Policy votes" }).click();
  await expect(profile.getByText("Representative votes", { exact: true })).toBeVisible();
  await expect(profile.getByText("Full reviewed vote list", { exact: true })).toBeVisible();
  await profile.getByRole("button", { name: "Show all reviewed votes" }).click();
  await expect(profile.getByRole("button", { name: "Hide full list" })).toBeVisible();

  await profile.locator("summary", { hasText: "Source, caveats, and full context" }).first().click();
  await expect(profile.getByText("this was a direct vote").first()).toBeVisible();
  await profile.locator("summary", { hasText: "Details" }).first().click();
  await expect(profile.getByText("What this vote was", { exact: true }).first()).toBeVisible();

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
  await expect(page.getByTestId("foushee-economy-editorial-gold").locator('[data-review-harness-chrome="true"]')).toContainText("Unpublished review");
  await expect(slice.getByText(/In this sample, Foushee voted against specific proposals involving government funding/)).toBeVisible();
  await expect(slice.getByText(/six substantive votes represent four policy episodes/i)).toBeVisible();
  await expect(slice.getByText(/not yet broad enough to establish one overarching Economy & Taxes philosophy/i)).toBeVisible();

  await expect(slice.getByText("Patterns in the reviewed record", { exact: true })).toBeVisible();
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
  await expect(slice.getByText("How to read this conclusion", { exact: true })).toBeVisible();
  await expect(slice.getByText(/This sample covers 4 independent policy episodes and does not represent the member's complete record/i)).toBeVisible();
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
    await expect(slice.getByText("Patterns in the reviewed record", { exact: true })).toBeVisible();
    const revisedFramework = slice.getByTestId("editorial-record-roll-100");
    await revisedFramework.locator(":scope > h6 > button").click();
    await expect(revisedFramework.getByText("What changed", { exact: true })).toBeVisible();
    await expect(revisedFramework.getByText("Impact and outcome", { exact: true })).toBeVisible();
    await assertNoHorizontalOverflow(page);
  }
});

test("Foushee Justice read preserves episodes, optional arguments, controls, and empty additional list", async ({ page }) => {
  await page.goto("/golden-render-fixture#foushee-justice-editorial-gold");
  const fixture = page.getByTestId("foushee-justice-editorial-gold");
  const slice = fixture.getByTestId("editorial-issue-experience");
  await expect(fixture.locator('[data-review-harness-chrome="true"]')).toContainText("Unpublished review");
  for (const indicator of ["7 substantive votes", "5 policy episodes", "0 Not Voting", "6 context-only records"]) {
    await expect(slice.getByText(indicator, { exact: true })).toBeVisible();
  }
  await expect(slice.getByText(/selective, guardrail-oriented approach/i)).toBeVisible();
  await expect(slice.getByText("A selective pattern in the reviewed record", { exact: true })).toBeVisible();
  await expect(slice.getByText(/Across one fentanyl episode/i)).toBeVisible();
  await expect(slice.getByText(/Across independent reporting and fentanyl episodes/i)).toBeVisible();
  const publicText = await slice.innerText();
  expect(publicText).not.toMatch(/bounded conditional|bounded selective|\bcandidate\b|\binference\b|annotations|immutable|bounded_selective_pattern|bounded_repeated_pattern|bounded_conditional_boundary|contested_candidate|insufficient_evidence|human_approval_pending|not_promoted|productionEligible|production eligible/i);
  await expect(slice.getByText("Later support for a permanent enforcement framework means the record is not blanket opposition to fentanyl enforcement.", { exact: true })).toBeVisible();
  await expect(slice.getByText("The substitute included risk and effectiveness exceptions, so it was not an unconditional pursuit mandate.", { exact: true })).toBeVisible();
  await expect(slice.getByText("The substitute retained exceptions and did not repeal every provision of the D.C. law.", { exact: true })).toBeVisible();
  await expect(fixture.getByText("Additional reviewed vote list", { exact: true })).toHaveCount(0);

  const reporting = slice.getByTestId("editorial-record-roll-131");
  await reporting.locator(":scope > h6 > button").click();
  await reporting.getByText("Arguments, context, and sources", { exact: true }).click();
  await expect(reporting.getByText("Supporters argued", { exact: true })).toBeVisible();
  await expect(reporting.getByText("Opponents argued", { exact: true })).toHaveCount(0);
  await expect(reporting.getByText(/No adequate stage-specific opposing argument/)).toBeVisible();
  await reporting.getByText(/Official sources \(4\)/).click();
  await expect(reporting.getByText("Vote and legislative status", { exact: true })).toBeVisible();
  await expect(reporting.getByText("Competing arguments", { exact: true })).toBeVisible();

  const dc = slice.getByTestId("editorial-record-roll-299");
  await dc.locator(":scope > h6 > button").click();
  await expect(dc.locator(":scope > h6 > button")).toHaveAttribute("aria-expanded", "true");
  await expect(reporting.locator(":scope > h6 > button")).toHaveAttribute("aria-expanded", "false");
  await expect(dc).toContainText("most of D.C.'s 2022 policing reform law");
  await expect(slice.getByTestId("editorial-record-context-160")).toHaveAttribute("data-inclusion-class", "context_only");
  await assertNoHorizontalOverflow(page);
});

test("Foushee Justice read is responsive and falls back in production mode", async ({ page }) => {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 1024, height: 768 }, { width: 768, height: 1024 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.goto(`/golden-render-fixture?justiceViewport=${viewport.width}#foushee-justice-editorial-gold`);
    const slice = page.getByTestId("foushee-justice-editorial-gold").getByTestId("editorial-issue-experience");
    await expect(slice.getByText("Patterns in the reviewed record", { exact: true })).toBeVisible();
    await slice.getByTestId("editorial-record-roll-275").locator(":scope > h6 > button").click();
    await expect(slice.getByTestId("editorial-record-roll-275").getByText("What changed", { exact: true })).toBeVisible();
    await assertNoHorizontalOverflow(page);
  }
  const fallback = page.getByTestId("foushee-justice-production-gate-fixture");
  await expect(fallback.getByTestId("editorial-issue-experience")).toHaveCount(0);
  await expect(fallback.getByTestId("basic-evidence-summary").getByText("Vote evidence", { exact: true })).toBeVisible();
  await expect(fallback.getByTestId("basic-evidence-summary").getByText("7 substantive Yes/No votes", { exact: true })).toBeVisible();
  await expect(fallback.getByTestId("basic-evidence-summary").getByText("6 procedural records", { exact: true })).toBeVisible();
});

test("Justice cross-member profiles render distinct conclusions through the generic harness", async ({ page }) => {
  await page.goto("/golden-render-fixture#justice-cross-member-A000370");

  const adams = page.getByTestId("justice-cross-member-A000370").getByTestId("editorial-issue-experience");
  await expect(page.getByTestId("justice-cross-member-A000370").locator('[data-review-harness-chrome="true"]')).toContainText("review only");
  await expect(adams.getByText(/selective boundary: support for evidence or reporting conditions/i)).toBeVisible();
  await expect(adams.getByText(/matched the majority of House Democrats/i)).toBeVisible();

  const aderholt = page.getByTestId("justice-cross-member-A000055").getByTestId("editorial-issue-experience");
  await expect(aderholt.getByText(/repeated support for the reviewed enforcement, police-tool, and authority expansions/i)).toBeVisible();
  await expect(aderholt.getByText(/selective boundary: support for evidence or reporting conditions/i)).toHaveCount(0);
  const aderholtCondition = aderholt.getByTestId("editorial-record-roll-32");
  await expect(aderholtCondition.getByText(/Opposed a certification condition/i)).toBeVisible();
  await aderholtCondition.locator(":scope > h6 > button").click();
  await expect(aderholtCondition.getByText(/Aderholt voted Nay/i)).toBeVisible();

  const massie = page.getByTestId("justice-cross-member-M001184").getByTestId("editorial-issue-experience");
  await expect(massie.getByText("A mixed record with a clear boundary", { exact: true })).toBeVisible();
  await expect(massie.getByText(/policy-specific divide between support for reviewed police tools or authority and opposition within the fentanyl scheduling episode/i)).toBeVisible();
  for (const indicator of ["7 substantive votes", "5 policy episodes", "0 Not Voting", "6 context-only records"]) {
    await expect(massie.getByText(indicator, { exact: true })).toBeVisible();
  }
  await assertNoHorizontalOverflow(page);
});

test("selected Justice cross-member profiles remain usable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/golden-render-fixture#justice-cross-member-M001184");
  for (const memberId of ["A000370", "A000055", "M001184"]) {
    const profile = page.getByTestId(`justice-cross-member-${memberId}`).getByTestId("editorial-issue-experience");
    await expect(profile.getByText("Patterns in the reviewed record", { exact: true })).toBeVisible();
    await profile.getByTestId("editorial-record-roll-275").locator(":scope > h6 > button").click();
    await expect(profile.getByTestId("editorial-record-roll-275").getByText("What changed", { exact: true })).toBeVisible();
    await assertNoHorizontalOverflow(page);
  }
});

test("pending editorial slice uses the basic representative fallback in production mode", async ({ page }) => {
  await page.goto("/golden-render-fixture#foushee-production-gate-fixture");
  const fixture = page.getByTestId("foushee-production-gate-fixture");
  await expect(fixture.getByRole("heading", { name: "Production-mode representative issue evidence" })).toBeVisible();
  await expect(fixture.getByTestId("editorial-issue-experience")).toHaveCount(0);
  await expect(fixture.getByTestId("basic-evidence-summary").getByText("Vote evidence", { exact: true })).toBeVisible();
  await expect(fixture.getByText("Representative votes", { exact: true })).toBeVisible();
  await expect(fixture.getByText("Full reviewed vote list", { exact: true })).toBeVisible();
  await expect(fixture.getByRole("button", { name: "Show all reviewed votes" })).toBeVisible();
});

test("synthetic fixture proves generic identity, mixed actions, optional omission, source counts, and accessibility", async ({ page }) => {
  await page.goto("/golden-render-fixture#synthetic-editorial-fixture");

  const fixture = page.getByTestId("synthetic-editorial-fixture");
  const slice = fixture.getByTestId("editorial-issue-experience");
  await expect(slice.getByRole("heading", { name: "Jordan Example \u2014 Energy & Infrastructure" })).toBeVisible();
  await expect(slice.getByText(/one infrastructure proposal was supported/i)).toBeVisible();
  for (const indicator of ["2 substantive votes", "2 policy episodes", "1 Not Voting", "1 context-only record"]) {
    await expect(slice.getByText(indicator, { exact: true })).toBeVisible();
  }
  await expect(slice.getByText("Voting context", { exact: true })).toHaveCount(0);
  await expect(slice.getByText("How to read this conclusion", { exact: true })).toBeVisible();
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
    await expect(fixture.getByText("A mixed or conditional pattern", { exact: true })).toBeVisible();
    await fixture.getByTestId("editorial-record-roll-57").locator(":scope > h6 > button").click();
    await expect(fixture.getByText("What changed", { exact: true })).toBeVisible();
    await assertNoHorizontalOverflow(page);
  }
});

test("public coverage states do not force conclusions and procedural-only evidence stays distinct", async ({ page }) => {
  await page.goto("/golden-render-fixture#public-developing-record");

  const developing = page.getByTestId("public-developing-record").getByTestId("editorial-issue-experience");
  await expect(developing.locator('[data-coverage-state="developing_record"]')).toBeVisible();
  await expect(developing.getByText("Developing record", { exact: true })).toBeVisible();
  await expect(developing.getByText(/repeated pattern is still developing/i)).toBeVisible();
  await expect(developing.getByText(/does not yet support a stable cross-episode conclusion/i)).toHaveCount(0);

  const limited = page.getByTestId("public-limited-evidence").getByTestId("editorial-issue-experience");
  await expect(limited.locator('[data-coverage-state="limited_evidence"]')).toBeVisible();
  await expect(limited.getByText("Not enough reviewed evidence yet", { exact: true })).toBeVisible();
  await expect(limited.getByText(/Too few independent episodes/i)).toBeVisible();
  await expect(limited.getByText("A single reviewed episode is available.", { exact: true })).toHaveCount(0);

  const procedural = page.getByTestId("public-procedural-only").getByTestId("basic-evidence-summary");
  await expect(procedural).toHaveAttribute("data-coverage-state", "procedural_context_only");
  await expect(procedural.getByText("Procedural context only", { exact: true })).toBeVisible();
  await expect(procedural.getByText(/do not establish a direct position/i)).toBeVisible();
});

test("issue navigation distinguishes analysis, receipts, and limited records in reader language", async ({ page }) => {
  await page.goto("/golden-render-fixture#public-mixed-availability");
  const fixture = page.getByTestId("public-mixed-availability");
  const navigation = fixture.getByRole("navigation", { name: "Issue evidence navigation" });
  await expect(navigation.getByRole("button", { name: /Environment & Energy.*Reviewed analysis/i })).toBeVisible();
  await expect(navigation.getByRole("button", { name: /Health & Social Services.*Vote evidence/i })).toBeVisible();
  await expect(navigation.getByRole("button", { name: /Education.*Limited record/i })).toBeVisible();
});

test("public surfaces exclude internal editorial workflow terminology", async ({ page }) => {
  await page.goto("/golden-render-fixture");
  const forbidden = /synthetic|fixture|gold standard|\bgold\b|benchmark|candidate|inference|annotations|human_approval_pending|not_promoted|productionEligible|production eligible|review packet|staged|rerun this inference|support balance|bounded_selective_pattern|bounded_repeated_pattern|bounded_conditional_boundary|contested_candidate|insufficient_evidence/i;
  const surfaces = page.locator('[data-public-surface]');
  await expect(surfaces).not.toHaveCount(0);
  for (let index = 0; index < await surfaces.count(); index += 1) {
    expect(await surfaces.nth(index).innerText()).not.toMatch(forbidden);
  }
  await expect(page.locator('[data-review-harness-chrome="true"]').first()).toBeVisible();
  await expect(page.locator("body")).toContainText("Synthetic fixture");
});

test("capture public editorial frontend review bundle", async ({ page }) => {
  test.skip(process.env.CAPTURE_PUBLIC_EDITORIAL_SCREENSHOTS !== "1", "review bundle capture is opt-in");
  const outputDirectory = path.resolve(process.cwd(), "..", "review_bundle_public_editorial_product_frontend_v1", "screenshots");
  await mkdir(outputDirectory, { recursive: true });
  const capture = async (locator, name) => locator.screenshot({ path: path.join(outputDirectory, name) });

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/golden-render-fixture#justice-cross-member-A000055");
  await capture(page.getByTestId("justice-cross-member-A000055").getByTestId("editorial-issue-experience"), "01-strong-repeated-pattern.png");
  await capture(page.getByTestId("foushee-justice-editorial-gold").getByTestId("editorial-issue-experience"), "02-selective-conditional-pattern.png");
  await capture(page.getByTestId("justice-cross-member-M001184").getByTestId("editorial-issue-experience"), "03-mixed-contested-record.png");
  await capture(page.getByTestId("public-developing-record").getByTestId("editorial-issue-experience"), "04-developing-record.png");
  await capture(page.getByTestId("foushee-economy-editorial-gold").getByTestId("editorial-issue-experience"), "05-not-voting-coverage.png");
  await capture(page.getByTestId("foushee-production-gate-fixture").getByTestId("basic-evidence-summary"), "06-no-editorial-slice-fallback.png");
  await capture(page.getByTestId("public-procedural-only").getByTestId("basic-evidence-summary"), "07-procedural-context-only.png");
  await capture(page.getByTestId("public-mixed-availability").getByRole("navigation", { name: "Issue evidence navigation" }), "08-mixed-availability-navigation.png");

  const economyCard = page.getByTestId("foushee-economy-editorial-gold").getByTestId("editorial-record-roll-182");
  await economyCard.locator(":scope > h6 > button").click();
  await capture(economyCard, "09-expanded-vote-card.png");
  await economyCard.getByText("Arguments, context, and sources", { exact: true }).click();
  await capture(economyCard, "10-arguments-and-important-context.png");
  await economyCard.getByText(/Official sources \(\d+\)/).click();
  await capture(economyCard, "11-grouped-official-sources.png");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/golden-render-fixture#foushee-justice-editorial-gold");
  await capture(page.getByTestId("foushee-justice-editorial-gold").getByTestId("editorial-issue-experience"), "12-mobile-public-summary.png");
  const mobileVote = page.getByTestId("foushee-justice-editorial-gold").getByTestId("editorial-record-roll-275");
  await mobileVote.locator(":scope > h6 > button").click();
  await capture(mobileVote, "13-mobile-expanded-vote.png");

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/golden-render-fixture#foushee-justice-editorial-gold");
  const reviewFrame = page.getByTestId("foushee-justice-editorial-gold");
  await reviewFrame.scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outputDirectory, "14-outer-review-harness.png") });
  const productionFallback = page.getByTestId("foushee-justice-production-gate-fixture");
  await productionFallback.scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outputDirectory, "15-production-mode-pending-fallback.png") });
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
