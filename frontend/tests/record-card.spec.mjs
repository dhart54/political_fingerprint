import fs from "node:fs";
import path from "node:path";
import { gunzipSync } from "node:zlib";
import { expect, test } from "@playwright/test";

const landing = "/review/record-card?representative=leg_valerie_p_foushee&scope=119";
const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/review_packets/record_at_a_glance_v1/candidate.json"), "utf8"));
const sourceSnapshot = JSON.parse(gunzipSync(fs.readFileSync(path.resolve("..", candidate.source_snapshot))));
test.beforeEach(async ({ page }) => { await page.emulateMedia({ reducedMotion: "reduce" }); });

test("reviewed Environment receipts label accepted passage types and retain exact official sources", async ({ page }) => {
  for (const scope of ["119", "all"]) for (const roll of [112, 114]) {
    await page.goto(`/review/record-card?representative=leg_valerie_p_foushee&scope=${scope}&issue=ENVIRONMENT_ENERGY#action-receipt-house-119-1-${roll}`);
    const receipt = page.locator(`[data-canonical-action-id="house:119:1:${roll}"]`);
    const button = receipt.getByRole("button");
    await expect(button).toBeFocused();
    await expect(button).toContainText(`Roll ${roll}`);
    await expect(button).toContainText("Final passage or suspension passage");
    await expect(button).not.toContainText(/Roll \d+.*Rule/);
    await expect(receipt.getByRole("link", { name: "Official vote" })).toHaveAttribute("href", `https://clerk.house.gov/evs/2025/roll${roll}.xml`);
    await expect(receipt.locator(".vote-pill").first()).toHaveText("Nay");
    await expect(receipt.locator("[data-action-status]")).toHaveCount(0);
  }
});

test("complete candidate, lazy ledgers, specific finding, receipts, history, refresh and return", async ({ page }) => {
  const requests = [];
  page.on("request", (request) => { if (request.url().includes("resource=evidence")) requests.push(request.url()); });
  await page.goto(landing);
  await expect(page.getByTestId("record-card-entry")).toHaveCount(candidate.entries.length);
  expect(requests).toHaveLength(0);
  const entry = page.getByRole("link", { name: /Compare the proposals: College foreign-gift/ });
  await entry.focus(); await page.keyboard.press("Enter");
  await expect(page.getByTestId("card-finding-detail")).toContainText("The final vote does not identify which part she opposed.");
  await expect(page.locator("#finding-detail-heading")).toBeFocused();
  await expect(page).toHaveURL(/finding=m14f/);
  expect(requests.every((r) => r.includes("domain=EDUCATION_WORKFORCE"))).toBe(true);
  await page.getByRole("link", { name: /^See 2 House votes:/ }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
  for (const id of ["house:119:1:79", "house:119:1:83"]) await expect(page.locator(`[data-canonical-action-id="${id}"]`)).toBeVisible();
  await page.reload();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  await page.goBack();
  await expect(page.locator("#finding-detail-heading")).toBeFocused();
  await expect(page.locator("#vote-record")).toHaveCount(0);
  await page.goForward();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  await page.getByRole("link", { name: "Complete issue record / all votes" }).click();
  await expect(page).not.toHaveURL(/finding=/);
  await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
  await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
  await expect(page.getByText(/8 additional recorded actions/)).toBeVisible();
  await page.goBack();
  await page.getByRole("link", { name: "Return to record at a glance" }).click();
  await expect(page.locator(`#${candidate.entries.find((e) => e.finding_id === "m14f:notable:hr1048_substitute_final").id}`)).toBeFocused();
  await expect(page.locator(`#${candidate.entries.find((e) => e.finding_id === "m14f:notable:hr1048_substitute_final").id}`)).toBeInViewport();
  await expect(page).not.toHaveURL(/issue=/);
});

test("Back returns keyboard focus to the originating card entry", async ({ page }) => {
  await page.goto(landing);
  const link = page.locator(`#${candidate.entries[0].id}`);
  await link.click();
  await expect(page.locator("#finding-detail-heading")).toBeFocused();
  await page.goBack();
  await expect(link).toBeFocused();
  await expect(link).toBeInViewport();
});

test("every selected finding resolves the whole exact support set", async ({ page }) => {
  for (const entry of candidate.entries) {
    await page.goto(landing);
    await page.locator(`#${entry.id}`).click();
    await page.getByRole("link", { name: `See ${entry.action_ids.length} House votes: ${entry.headline}` }).click();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(entry.action_ids.length);
    const ids = await page.locator("[data-canonical-action-id]").evaluateAll((els) => els.map((el) => el.dataset.canonicalActionId).sort());
    expect(ids).toEqual([...entry.action_ids].sort());
    await expect(page.locator('[data-canonical-action-id] button[aria-expanded="true"]').first()).toBeVisible();
  }
});

test("real sparse member and receipts-only scope remain useful without invented cards", async ({ page }) => {
  await page.goto("/review/record-card?representative=leg_thomas_massie&scope=119");
  await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
  await expect(page.getByTestId("record-card")).toHaveCount(0);
  await expect(page.getByTestId("issue-card")).toHaveCount(8);
  await page.getByRole("button", { name: "Browse vote record for Economy & Taxes" }).click();
  await expect(page.locator("#vote-record")).toContainText("recorded actions");
  await page.goto(landing);
  await page.getByLabel("Recorded votes", { exact: true }).selectOption("118");
  await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
  await expect(page.getByTestId("record-card")).toHaveCount(0);
  await page.getByRole("button", { name: "Browse vote record for Justice & Public Safety" }).click();
  await expect(page.locator("#vote-record")).toContainText("recorded actions");
});

test("failure, loading, incomplete inputs and identity mismatch are not no-summary", async ({ page }) => {
  await page.route("**/api/review/record-card?resource=editorial*", (route) => route.fulfill({ status: 503, body: "unavailable" }));
  await page.goto(landing);
  await expect(page.getByText(/Reviewed findings are unavailable right now/)).toBeVisible();
  await expect(page.getByText(/No reviewed findings/)).toHaveCount(0);
  await expect(page.getByTestId("issue-card")).toHaveCount(8);
  await page.unrouteAll();
  for (const kind of ["incomplete", "identity"]) {
    await page.route("**/api/review/record-card?resource=editorial*", async (route) => {
      const response = await route.fetch(), body = await response.json();
      if (kind === "incomplete") body.presentations.pop(); else body.member_bioguide_id = "SYNTHETIC_MISMATCH";
      await route.fulfill({ json: body });
    });
    await page.goto(landing);
    await expect(page.getByText(kind === "incomplete" ? /reviewed finding inputs are incomplete/ : /returned findings do not match/)).toBeVisible();
    await expect(page.getByTestId("record-card")).toHaveCount(0);
    await page.unrouteAll();
  }
});

test("delayed old requests cannot populate a new scope or representative", async ({ page }) => {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  await page.route("**/api/review/record-card?resource=editorial*scope=119", async (route) => { const response = await route.fetch(); await gate; await route.fulfill({ response }); });
  await page.goto(landing);
  await expect(page.getByText("Loading reviewed findings…", { exact: true })).toBeVisible();
  await page.getByLabel("Recorded votes", { exact: true }).selectOption("118");
  release();
  await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
  await expect(page.getByTestId("record-card-entry")).toHaveCount(0);
  await page.unrouteAll();
  await page.goto(landing);
  await expect(page.getByTestId("record-card-entry")).toHaveCount(candidate.entries.length);
  await page.getByRole("button", { name: "Switch representative" }).click();
  await page.getByRole("button", { name: "Thomas Massie", exact: true }).click();
  await expect(page.getByTestId("record-card-entry")).toHaveCount(0);
  await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
});

test("direct issue and exact receipt links honor their destinations", async ({ page }) => {
  await page.goto(`${landing}&issue=EDUCATION_WORKFORCE`);
  await expect(page.locator("#selected-issue-heading")).toBeFocused();
  await page.goto(`${landing}&issue=EDUCATION_WORKFORCE#action-receipt-house-119-1-79`);
  const receipt = page.locator("#action-receipt-house-119-1-79");
  await expect(receipt.locator("button").first()).toHaveAttribute("aria-expanded", "true");
  await expect(receipt.locator("button").first()).toBeFocused();
});

test("all scope is bounded, the whole card is actionable and layouts do not overflow", async ({ page }) => {
  const output = process.env.RECORD_CARD_SCREENSHOT_DIR;
  if (output) fs.mkdirSync(output, { recursive: true });
  for (const [name, width, height] of [["desktop", 1440, 900], ["mobile", 390, 844], ["narrow", 360, 800]]) {
    await page.setViewportSize({ width, height });
    await page.goto(landing.replace("scope=119", "scope=all"));
    await expect(page.getByTestId("record-card-entry")).toHaveCount(candidate.entries.length);
    await expect(page.getByTestId("record-card")).toContainText("119th Congress · Recorded-vote scope: All available Congresses");
    await expect(page.getByText("Selected findings · Reviewed coverage in 4 of 8 issues.")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Mixed choices", exact: true })).toBeVisible();
    for (const entry of candidate.entries) await expect(page.locator(`#${entry.id}`)).toHaveAccessibleName(`${entry.link_label}: ${entry.headline}`);
    await expect(page.getByTestId("record-card")).not.toContainText("supporting House votes");
    // Font metrics vary by OS. The release contract preserves complete readable
    // entries and normal scrolling, rather than forcing a link above the fold.
    for (const entry of candidate.entries) {
      const link = page.locator(`#${entry.id}`);
      expect((await link.boundingBox()).height).toBeGreaterThanOrEqual(44);
      await link.scrollIntoViewIfNeeded();
      await expect(link).toBeInViewport({ ratio: 1 });
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (output) {
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
      await page.screenshot({ path: path.join(output, `${name}-landing.png`) });
      await page.screenshot({ path: path.join(output, `${name}-complete-journey.png`), fullPage: true });
    }
    await page.getByText("Coverage and review details", { exact: true }).click();
    await expect(page.getByTestId("record-card")).toContainText("National Security & Foreign Policy: through July 23, 2026.");
    await expect(page.getByText("a precise cutoff is not specified in the bound review scope.", { exact: false })).toHaveCount(3);
    if (output) {
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
      await page.screenshot({ path: path.join(output, `${name}-coverage-details.png`), fullPage: true });
    }
  }
});

test("review packet captures finding, paired receipts, complete record, sparse and unavailable states", async ({ page }) => {
  const output = process.env.RECORD_CARD_SCREENSHOT_DIR;
  if (!output) return;
  fs.mkdirSync(output, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(landing);
  await page.locator(`#${candidate.entries.find((e) => e.finding_id === "m14f:notable:hr1048_substitute_final").id}`).click();
  await expect(page.locator("#finding-detail-heading")).toBeFocused();
  await page.screenshot({ path: path.join(output, "mobile-specific-finding.png") });
  await page.getByRole("link", { name: /^See 2 House votes:/ }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
  await page.screenshot({ path: path.join(output, "mobile-supporting-receipts.png") });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("link", { name: "Complete issue record / all votes" }).click();
  await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
  await page.screenshot({ path: path.join(output, "desktop-complete-record.png") });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/review/record-card?representative=leg_thomas_massie&scope=119");
  await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
  await page.screenshot({ path: path.join(output, "mobile-no-summary.png") });
  await page.route("**/api/review/record-card?resource=editorial*", (route) => route.fulfill({ status: 503, body: "unavailable" }));
  await page.goto(landing);
  await expect(page.getByText(/Reviewed findings are unavailable right now/)).toBeVisible();
  await page.screenshot({ path: path.join(output, "mobile-unavailable.png") });
});

test("API-only amendment source has an accessible disclosure and preserves accepted receipt text", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const row = sourceSnapshot["leg_valerie_p_foushee:119:NATIONAL_SECURITY_FOREIGN"].body.evidence.find((r) => r.canonical_action_id === "house:119:2:264");
  const url = row.governed_receipt_projection.action_meaning_sources[0].url;
  // Fault response reproduces unauthenticated navigation without accessing credentials.
  await page.context().route("https://api.congress.gov/**", (route) => route.fulfill({ status: 403, json: { error: { code: "API_KEY_MISSING" } } }));
  await page.goto(`${landing}&issue=NATIONAL_SECURITY_FOREIGN#action-receipt-house-119-2-264`);
  const receipt = page.locator('[data-canonical-action-id="house:119:2:264"]');
  await expect(receipt.getByText(row.governed_receipt_projection.exact_action_meaning, { exact: true })).toBeVisible();
  const link = receipt.getByRole("link", { name: "Amendment description (Congress API)", exact: true });
  const note = "This Congress API link requires an API key and may not open directly in your browser.";
  await expect(link).toHaveAttribute("href", url);
  await expect(link).toHaveAccessibleDescription(note);
  await expect(receipt.getByText(note, { exact: true })).toBeVisible();
  await expect(receipt.getByRole("link", { name: "Bill or amendment text", exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  const devPortal = page.locator("nextjs-portal");
  if (await devPortal.count()) await devPortal.evaluate((element) => element.remove());
  await receipt.locator("section").filter({ has: page.getByRole("heading", { name: "Official sources", exact: true }) }).screenshot({ path: "test-results/source-access-mobile.png" });
  await link.focus();
  const popupPromise = page.waitForEvent("popup");
  await page.keyboard.press("Enter");
  const popup = await popupPromise;
  await expect(popup).toHaveURL(url);
  await popup.close();
  await expect(receipt.getByText(row.governed_receipt_projection.exact_action_meaning, { exact: true })).toBeVisible();
});

test("API legislative actions and public version XML retain distinct labels and access notes", async ({ page }) => {
  await page.goto(`${landing}&issue=NATIONAL_SECURITY_FOREIGN#action-receipt-house-119-2-48`);
  const receipt = page.locator('[data-canonical-action-id="house:119:2:48"]');
  const actions = receipt.getByRole("link", { name: "Legislative actions (Congress API)", exact: true });
  const xml = receipt.getByRole("link", { name: "Bill or amendment text", exact: true });
  await expect(actions).toHaveAttribute("href", "https://api.congress.gov/v3/bill/119/hconres/68/actions");
  await expect(actions).toHaveAccessibleDescription(/requires an API key/);
  await expect(xml).toHaveAttribute("href", "https://www.congress.gov/119/bills/hconres68/BILLS-119hconres68ih.xml");
  await expect(xml).not.toHaveAttribute("aria-describedby");
  await expect(receipt.getByText(/This Congress API link requires/)).toHaveCount(1);
});
