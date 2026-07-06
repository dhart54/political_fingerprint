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
