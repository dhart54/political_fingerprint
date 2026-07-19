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

test("Foushee economy editorial cards preserve the approved disclosure hierarchy", async ({ page }) => {
  await page.goto("/golden-render-fixture");

  const section = page.getByTestId("foushee-economy-editorial-gold");
  await expect(section.getByRole("heading", { name: "Valerie P. Foushee — Economy & Taxes" })).toBeVisible();
  await expect(section.getByText("Six substantive votes cover four policy episodes.")).toBeVisible();

  const notVoting = section.getByTestId("approved-editorial-roll-310");
  await expect(notVoting.getByText("Did not vote on proposed cap on net costs from SBA rules")).toBeVisible();
  await expect(notVoting.getByText("Foushee did not vote. The bill passed the House but had not become law.")).toBeVisible();

  const houseProposal = section.getByTestId("approved-editorial-roll-182");
  const collapsedText = await houseProposal.innerText();
  expect(collapsedText).not.toContain("$17.509 billion");
  await expect(houseProposal.getByText("Before this vote")).not.toBeVisible();
  const houseSummary = houseProposal.locator(":scope > summary");
  await expect(houseSummary).toHaveCount(1);
  await houseSummary.click();
  await expect(houseProposal.getByText("Before this vote")).toBeVisible();
  await expect(houseProposal.getByText(/\$17\.509 billion/)).toBeVisible();

  const deeperSummary = houseProposal.getByText("Arguments, history, caveats, and sources", { exact: true });
  await deeperSummary.click();
  await expect(houseProposal.getByText("Supporters argued", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Opponents argued", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Evidence boundary", { exact: true })).toBeVisible();
  await expect(houseProposal.getByText("Official sources", { exact: true })).toBeVisible();

  const revisedFramework = section.getByTestId("approved-editorial-roll-100");
  await expect(revisedFramework.getByText(/did not itself change taxes, benefits, annual funding, or the debt limit/)).toBeVisible();
  const initialFramework = section.getByTestId("approved-editorial-roll-50");
  await expect(initialFramework.getByText(/did not itself change taxes, benefits, annual funding, or the debt limit/)).toBeVisible();

  await expect(section.getByTestId("approved-editorial-control-263")).toContainText("nonbinding request");
  await expect(section.getByTestId("approved-editorial-control-180")).toContainText("package of seven different amendments");

  const publicText = await section.innerText();
  expect(publicText).not.toMatch(/claim_id|human_approval_pending|gold_benchmark|agent_confidence|review question/i);
  await assertNoHorizontalOverflow(page);
});

test("Foushee economy editorial cards remain scannable at 390x844", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/golden-render-fixture");

  const section = page.getByTestId("foushee-economy-editorial-gold");
  await expect(section.getByText("Key Economy & Taxes votes, explained in layers")).toBeVisible();
  const revisedFramework = section.getByTestId("approved-editorial-roll-100");
  await revisedFramework.locator(":scope > summary").click();
  await expect(revisedFramework.getByText("Before this vote")).toBeVisible();
  await expect(revisedFramework.getByText("Scale or timing")).toBeVisible();
  await assertNoHorizontalOverflow(page);
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
