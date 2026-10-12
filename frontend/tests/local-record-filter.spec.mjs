import { expect, test } from "@playwright/test";
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { economyEvidence, foushee, installPassARoutes } from "./pass-a-fixtures.mjs";

const available = economyEvidence.map((row, index) => ({
  ...row,
  action_label: `Budget record ${row.rollcall_number}`,
  bill_title: index === 0 ? "H.R. 1" : index === 1 ? "H.R. 10" : `H.R. ${200 + index}`,
}));
const filter = (page) => page.getByRole("searchbox", { name: "Filter loaded receipts by measure, roll or title", exact: true });
const receiptIds = (page) => page.locator("[data-canonical-action-id]").evaluateAll((nodes) => nodes.map((node) => node.dataset.canonicalActionId));
const receipt = (page, roll) => page.locator(`[data-canonical-action-id="house:119:1:${roll}"]`);
const economyUrl = `/?representative=${foushee.id}&scope=119&issue=ECONOMY_TAXES`;
const contact = { legislator_id: foushee.id, contact_status: "loaded", data_source: "database", phone: "(202) 225-1784", source_retrieved_at: "2026-05-19" };

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await installPassARoutes(page, { evidenceOverrides: { ECONOMY_TAXES: available } });
});

test("roll and literal title matching have truthful no-match, blank and Clear states", async ({ page }) => {
  await page.goto(economyUrl);
  await filter(page).fill("ROLL #0401");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  expect(await receiptIds(page)).toEqual(["house:119:1:401"]);
  await filter(page).fill("  BUDGET    record  412  ");
  await expect(receipt(page, 412)).toBeVisible();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  await filter(page).fill("Budget unmatched");
  await expect(page.getByText("No loaded receipts match this text and the current filters.", { exact: true })).toBeVisible();
  await expect(page.getByTestId("local-record-filter-status")).toContainText("0 of 13 loaded receipts");
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  await expect(filter(page)).toBeFocused();
  await expect(filter(page)).toHaveValue("");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  await filter(page).fill("  . ,  ");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  await expect(page.getByTestId("local-record-filter-status")).not.toContainText("Text filter matches");
});

test("text intersects Vote and Type without changing nondirectional or procedural evidence", async ({ page }) => {
  const rows = available.slice(0, 4).map((row, index) => ({
    ...row, position: ["yea", "nay", "present", "not_voting"][index],
    interpretation_status: index < 2 ? "interpreted" : "procedural",
    vote_type: index < 2 ? "final_passage" : "procedural",
    vote_context: { ...row.vote_context, vote_type: index < 2 ? "final_passage" : "procedural" },
  }));
  await installPassARoutes(page, { evidenceOverrides: { ECONOMY_TAXES: rows } });
  await page.goto(economyUrl);
  await filter(page).fill("Budget");
  await page.getByRole("group", { name: "Vote", exact: true }).getByRole("button", { name: "Yea", exact: true }).click();
  expect(await receiptIds(page)).toEqual(["house:119:1:400"]);
  await expect(filter(page)).toHaveValue("Budget");
  await page.getByRole("group", { name: "Type", exact: true }).getByRole("button", { name: "Procedural / context", exact: true }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(0);
  await page.getByRole("group", { name: "Vote", exact: true }).getByRole("button", { name: "Present / Not voting", exact: true }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  expect(await receiptIds(page)).toEqual(["house:119:1:403", "house:119:1:402"]);
  await expect(receipt(page, 402).locator(".vote-pill")).toHaveText("Present");
  await expect(receipt(page, 403).locator(".vote-pill")).toHaveText("Not Voting");
  await expect(page.getByTestId("local-record-filter-status")).toContainText("2 of 2 loaded receipts after Vote/Type filters");
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  await expect(page.getByRole("button", { name: "Present / Not voting", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Procedural / context", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
});

test("progressive reveal and text clearing preserve chronology and reveal budget", async ({ page }) => {
  await page.goto(economyUrl);
  await filter(page).fill("budget");
  await expect(page.getByTestId("local-record-filter-status")).toContainText("13 of 13 loaded receipts");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  await page.getByRole("button", { name: "Show more votes", exact: true }).click();
  const orderedIds = [...available].reverse().map((row) => row.roll_call_id);
  expect(await receiptIds(page)).toEqual(orderedIds);
  await filter(page).fill("hr1");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  expect(await receiptIds(page)).toEqual(orderedIds);
  await expect(page.getByRole("button", { name: "Show more votes", exact: true })).toHaveCount(0);
});

test("a selected unrevealed receipt stays expanded when clearing text", async ({ page }) => {
  await page.goto(economyUrl);
  await filter(page).fill("hr1");
  const target = receipt(page, 400);
  await target.locator(":scope > button").click();
  const sourceMarkup = await target.locator("div.grid").innerHTML();
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  await expect(target.locator(":scope > button")).toHaveAttribute("aria-expanded", "true");
  expect(await target.locator("div.grid").innerHTML()).toBe(sourceMarkup);
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(13);
});

test("matching text preserves an open contact disclosure when a related group shrinks to one", async ({ page }) => {
  await installPassARoutes(page, { evidenceOverrides: { ECONOMY_TAXES: available.slice(0, 2).map((row) => ({ ...row, bill_id: "hr27-119", bill_title: "H.R. 27" })) } });
  let contactReads = 0;
  await page.route("**/legislators/*/contact", (route) => { contactReads += 1; return route.fulfill({ json: contact }); });
  await page.goto(economyUrl);
  const target = receipt(page, 401);
  await target.locator(":scope > button").click();
  const sources = await target.locator("div.grid").innerHTML();
  await target.getByRole("button", { name: "Official contact information", exact: true }).click();
  const panel = target.getByRole("region", { name: "Official contact information", exact: true });
  await expect(panel).toContainText("225-1784");
  const id = await panel.getAttribute("id");
  await filter(page).fill("roll401");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  await expect(panel).toHaveAttribute("id", id);
  await expect(panel).toContainText("225-1784");
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  await expect(panel).toHaveAttribute("id", id);
  expect(await target.locator("div.grid").innerHTML()).toBe(sources);
  expect(contactReads).toBe(1);
});

test("excluding a selected receipt invalidates pending contact and Clear restores only receipt selection", async ({ page }) => {
  await page.addInitScript(() => {
    window.contactDone = 0;
    const original = window.fetch;
    window.fetch = async (...args) => {
      const response = await original(...args);
      if (String(args[0]).endsWith("/contact")) {
        const json = response.json.bind(response);
        response.json = async () => { try { return await json(); } finally { window.contactDone += 1; } };
      }
      return response;
    };
  });
  let resolvePending, contactReads = 0;
  const pending = new Promise((resolve) => { resolvePending = resolve; });
  await page.route("**/legislators/*/contact", (route) => { contactReads += 1; resolvePending(route); });
  await page.goto(economyUrl);
  const target = receipt(page, 412);
  await target.locator(":scope > button").click();
  const sources = await target.locator("div.grid").innerHTML();
  await target.getByRole("button", { name: "Official contact information", exact: true }).click();
  const held = await pending;
  await filter(page).fill("hr1");
  await expect(target).toHaveCount(0);
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  await expect(target.locator(":scope > button")).toHaveAttribute("aria-expanded", "true");
  await held.fulfill({ json: contact });
  await page.waitForFunction(() => window.contactDone === 1);
  await expect(page.getByRole("region", { name: "Official contact information", exact: true })).toHaveCount(0);
  expect(await target.locator("div.grid").innerHTML()).toBe(sources);
  expect(contactReads).toBe(1);
});

test("explicit receipt anchor clears an excluding query and reaches the exact receipt", async ({ page }) => {
  await page.goto(economyUrl);
  await filter(page).fill("hr1");
  await page.evaluate(() => { location.hash = "action-receipt-house-119-1-412"; });
  await expect(filter(page)).toHaveValue("");
  await expect(receipt(page, 412).locator(":scope > button")).toHaveAttribute("aria-expanded", "true");
  await expect(receipt(page, 412).locator(":scope > button")).toBeFocused();
});

test("new finding navigation clears text while filtering retains accepted linked accounting", async ({ page }) => {
  await page.goto(`/?representative=${foushee.id}&scope=119&issue=JUSTICE_PUBLIC_SAFETY`);
  const coverage = await page.locator("#issue-summary").innerText();
  await filter(page).fill("unmatched");
  await page.getByRole("button", { name: /View 3 votes for Certification, fentanyl research provisions/ }).click();
  await expect(filter(page)).toHaveValue("");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(3);
  const accounting = await page.locator(".pattern-strip").innerText();
  await filter(page).fill("roll32");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  await expect(page.getByTestId("local-record-filter-status")).toContainText("1 of 3 loaded linked receipts");
  expect(await page.locator(".pattern-strip").innerText()).toBe(accounting);
  expect(await page.locator("#issue-summary").innerText()).toBe(coverage);
  await page.getByRole("button", { name: /View 3 votes for Retired-service firearm access/ }).click();
  await expect(filter(page)).toHaveValue("");
  expect(await receiptIds(page)).toEqual(["house:119:1:299", "house:119:1:275", "house:119:1:130"]);
});

test("empty scoped ledger stays explicit instead of claiming text or historical completeness", async ({ page }) => {
  await installPassARoutes(page, { evidenceOverrides: { ECONOMY_TAXES: [] } });
  await page.goto(economyUrl);
  await expect(page.locator("#local-record-filter-help")).toContainText("0 receipts loaded for this issue and scope");
  await filter(page).fill("hr1");
  await expect(page.getByText("No recorded actions are available for this issue in the selected scope.", { exact: true })).toBeVisible();
  await expect(page.getByTestId("local-record-filter-status")).toContainText("0 of 0 loaded receipts");
});

const candidate = JSON.parse(fs.readFileSync("../docs/review_packets/record_at_a_glance_v1/candidate.json"));
const snapshot = JSON.parse(gunzipSync(fs.readFileSync(`../${candidate.source_snapshot}`)));
const warPowers = candidate.entries.find((entry) => entry.finding_id.includes("war-powers"));
const massie = { id: "leg_thomas_massie", name_display: "Thomas Massie", chamber: "house", state: "KY", district: "04", party: "R", bioguide_id: "M001184" };
const senator = { id: "leg_angela_d_alsobrooks", name_display: "Angela D. Alsobrooks", chamber: "senate", state: "MD", party: "D", bioguide_id: "A000382" };
async function releasedResponses(page, { omit = null } = {}) {
  await page.route("http://localhost:8000/**", (route) => {
    const url = new URL(route.request().url()), member = url.pathname.split("/")[2];
    if (url.pathname.endsWith("/profile")) return route.fulfill({ json: [foushee, massie, senator].find((profile) => profile.id === member) });
    const resource = url.pathname.endsWith("/editorial-presentations") ? "editorial" : url.pathname.endsWith("/evidence") ? url.pathname.split("/")[4] : "positions";
    const supplied = snapshot[`${member}:${url.searchParams.get("scope") || "all"}:${resource}`];
    if (!supplied) throw Error(`Unexpected fixture read: ${url.pathname}`);
    const body = supplied.body.evidence && omit ? { ...supplied.body, evidence: supplied.body.evidence.filter((row) => row.canonical_action_id !== omit) } : supplied.body;
    return route.fulfill({ status: supplied.status, json: body });
  });
}

for (const partial of [false, true]) test(`released finding ${partial ? "partial" : "complete"} response keeps source identity, coverage and history`, async ({ page }) => {
  await releasedResponses(page, { omit: partial ? warPowers.action_ids[0] : null });
  await page.goto(`/?representative=${foushee.id}&scope=all`);
  const cards = await page.getByTestId("record-card-entry").evaluateAll((nodes) => nodes.map((node) => ({ id: node.id, href: node.getAttribute("href"), text: node.textContent })));
  await page.locator(`#${warPowers.id}`).click();
  await page.getByRole("navigation", { name: "Selected issue sections" }).getByRole("link", { name: "Vote record", exact: true }).click();
  const count = partial ? 8 : 9;
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(count);
  const ids = await receiptIds(page), url = page.url(), historyLength = await page.evaluate(() => history.length);
  const accounting = await page.locator(".pattern-strip").innerText();
  const target = page.locator("[data-canonical-action-id]").first();
  const sources = await target.locator("div.grid").innerHTML();
  const roll = ids[0].split(":").at(-1);
  await filter(page).fill(`roll${roll}`);
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  expect(await target.locator("div.grid").innerHTML()).toBe(sources);
  expect(await page.locator(".pattern-strip").innerText()).toBe(accounting);
  await expect(page.getByTestId("local-record-filter-status")).toContainText(`1 of ${count} loaded linked receipts`);
  if (partial) await expect(page.getByText("Showing 8 of 9 linked vote receipts. The remaining linked receipt is unavailable in this response.", { exact: true })).toBeVisible();
  expect(page.url()).toBe(url); expect(await page.evaluate(() => history.length)).toBe(historyLength);
  await page.reload();
  await expect(filter(page)).toHaveValue("");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(count);
  expect(page.url()).toBe(url);
  await page.goBack(); await expect(page.getByTestId("card-finding-detail")).toBeVisible();
  await page.goForward(); await expect(page.locator("[data-canonical-action-id]")).toHaveCount(count);
  await page.goto(`/?representative=${foushee.id}&scope=all`);
  expect(await page.getByTestId("record-card-entry").evaluateAll((nodes) => nodes.map((node) => ({ id: node.id, href: node.getAttribute("href"), text: node.textContent })))).toEqual(cards);
});

test("receipts-only and sparse members keep their existing evidence boundary", async ({ page }) => {
  await releasedResponses(page);
  await page.goto(`/?representative=${massie.id}&scope=119&issue=ECONOMY_TAXES`);
  await expect(page.getByTestId("record-card")).toHaveCount(0);
  await expect(filter(page)).toBeVisible();
  const first = page.locator("[data-canonical-action-id]").first();
  const id = await first.getAttribute("data-canonical-action-id");
  await filter(page).fill(`roll${id.split(":").at(-1)}`);
  await expect(page.locator(`[data-canonical-action-id="${id}"]`)).toBeVisible();
  await page.goto(`/?representative=${senator.id}&scope=119`);
  await expect(page.getByTestId("record-card")).toHaveCount(0);
  await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
  await expect(filter(page)).toHaveCount(0);
});

for (const width of [320, 390, 1440]) test(`local text filter supports keyboard and readable layout at ${width}px`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(economyUrl);
  await filter(page).focus(); await page.keyboard.type("H.R. 1");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  await expect(filter(page)).toBeFocused();
  const bounds = await filter(page).boundingBox();
  expect(bounds.height).toBeGreaterThanOrEqual(44);
  expect(bounds.width).toBeGreaterThan(100);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Clear text filter", exact: true })).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator("#vote-record").screenshot({ path: testInfo.outputPath(`local-filter-${width}.png`) });
  await page.keyboard.press("Enter"); await expect(filter(page)).toBeFocused();
  await expect(filter(page)).toHaveValue("");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
});

test("local filter reaches an unrevealed exact identifier without remote search or history changes", async ({ page }) => {
  const requests = [];
  page.on("request", (request) => { if (request.url().startsWith("http://localhost:8000")) requests.push(request.url()); });
  await page.goto(`/?representative=${foushee.id}&scope=119&issue=ECONOMY_TAXES`);
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  const beforeRequests = [...requests], url = page.url(), historyLength = await page.evaluate(() => history.length);
  await filter(page).fill("  h. r.  1  ");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  expect(await receiptIds(page)).toEqual(["house:119:1:400"]);
  await expect(page.getByTestId("local-record-filter-status")).toContainText("1 of 13 loaded receipts");
  expect(requests).toEqual(beforeRequests); expect(page.url()).toBe(url);
  expect(await page.evaluate(() => history.length)).toBe(historyLength);
});
