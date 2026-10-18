import { expect, test } from "@playwright/test";
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { economyEvidence, foushee, installPassARoutes, justiceEvidence } from "./pass-a-fixtures.mjs";

const available = economyEvidence.map((row, index) => ({
  ...row,
  action_label: `Budget record ${row.rollcall_number}`,
  bill_title: index === 0 ? "H.R. 1" : index === 1 ? "H.R. 10" : `H.R. ${200 + index}`,
}));
const filter = (page) => page.getByRole("searchbox", { name: "Filter loaded receipts by measure, roll or title", exact: true });
const receiptIds = (page) => page.locator("[data-canonical-action-id]").evaluateAll((nodes) => nodes.map((node) => node.dataset.canonicalActionId));
const receipt = (page, roll) => page.locator(`[data-canonical-action-id="house:119:1:${roll}"]`);
const stableReceiptHtml = (target) => target.locator("div.grid").evaluate(element => {
  const clone = element.cloneNode(true);
  // Keyboard prefixes can legitimately exclude/remount a row. Normalize only
  // React-generated note IDs, while requiring each actual link/note binding.
  [...clone.querySelectorAll("a[aria-describedby]")].forEach((link, index) => {
    const supplied = link.getAttribute("aria-describedby");
    const note = [...clone.querySelectorAll("[id]")].find(node => node.id === supplied);
    if (!note) throw Error("Missing receipt source access-note binding");
    const id = `bound-source-note-${index}`;
    link.setAttribute("aria-describedby", id); note.id = id;
  });
  return clone.innerHTML;
});
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

for (const operation of ["show more", "collapse"]) test(`retained deep receipt commits the reveal budget before ${operation}`, async ({ page }, testInfo) => {
  const rows = Array.from({ length: 48 }, (_, index) => ({
    ...available[0],
    canonical_action_id: `house:119:1:${800 + index}`,
    roll_call_id: `house:119:1:${800 + index}`,
    rollcall_number: 800 + index,
    bill_id: `hr${800 + index}-119`,
    bill_title: `H.R. ${800 + index}`,
    action_label: `Budget record ${800 + index}`,
    vote_date: new Date(Date.UTC(2025, 0, index + 1)).toISOString().slice(0, 10),
  }));
  await installPassARoutes(page, { evidenceOverrides: { ECONOMY_TAXES: rows } });
  const requests = [];
  page.on("request", (request) => { if (request.url().startsWith("http://localhost:8000")) requests.push(request.url()); });
  await page.goto(economyUrl);
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  const url = page.url(), historyLength = await page.evaluate(() => history.length), initialRequests = [...requests];
  const chronologicalIds = [...rows].reverse().map((row) => row.canonical_action_id);
  const target = receipt(page, 817); // Index30 in the unfiltered48-row ledger.
  await filter(page).fill("roll817");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  await target.locator(":scope > button").click();
  const sources = await target.locator("div.grid").innerHTML();
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(31);
  expect(await receiptIds(page)).toEqual(chronologicalIds.slice(0, 31));
  expect(await target.locator("div.grid").innerHTML()).toBe(sources);
  if (operation === "show more") await page.getByRole("button", { name: "Show more votes", exact: true }).click();
  else await target.locator(":scope > button").click();
  const observedIds = await receiptIds(page);
  await testInfo.attach("deep-receipt-reveal-state", {
    contentType: "application/json",
    body: Buffer.from(JSON.stringify({ loaded: 48, selectedIndex: 30, afterClear: 31, operation, afterOperation: observedIds.length, selectedReceiptMounted: observedIds.includes("house:119:1:817"), ids: observedIds })),
  });
  expect(observedIds).toEqual(chronologicalIds.slice(0, operation === "show more" ? 43 : 31));
  if (operation === "show more") {
    expect(await target.locator("div.grid").innerHTML()).toBe(sources);
    await target.locator(":scope > button").click();
    expect(await receiptIds(page)).toEqual(chronologicalIds.slice(0, 43));
  }
  await expect(target.locator(":scope > button")).toHaveAttribute("aria-expanded", "false");
  await expect(target.locator(":scope > button")).toBeFocused();
  expect(requests).toEqual(initialRequests);
  expect(page.url()).toBe(url);
  expect(await page.evaluate(() => history.length)).toBe(historyLength);
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
  let requested;
  let release;
  const pendingEvidence = new Promise((resolve) => { requested = resolve; });
  const evidenceGate = new Promise((resolve) => { release = resolve; });
  await page.route("**/positions/JUSTICE_PUBLIC_SAFETY/evidence*", async (route) => {
    requested();
    await evidenceGate;
    await route.fulfill({ json: { domain: "JUSTICE_PUBLIC_SAFETY", evidence: justiceEvidence } });
  });
  await page.goto(`/?representative=${foushee.id}&scope=119&issue=JUSTICE_PUBLIC_SAFETY`);
  await pendingEvidence;
  await expect(page.locator("#issue-summary")).not.toContainText("7 recorded actions currently visible");
  release();
  await expect(page.locator("#issue-summary")).toContainText("7 recorded actions currently visible");
  await expect(page.locator("#issue-summary")).toContainText("7 recorded actions in scope");
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
async function releasedResponses(page, { omit = null, measureReferences = false, editorialGate = null } = {}) {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url()), member = url.pathname.split("/")[2];
    if (url.pathname.endsWith("/profile")) return route.fulfill({ json: [foushee, massie, senator].find((profile) => profile.id === member) });
    const resource = url.pathname.endsWith("/editorial-presentations") ? "editorial" : url.pathname.endsWith("/evidence") ? url.pathname.split("/")[4] : "positions";
    if (resource === "editorial" && editorialGate) await editorialGate;
    const supplied = snapshot[`${member}:${url.searchParams.get("scope") || "all"}:${resource}`];
    if (!supplied) throw Error(`Unexpected fixture read: ${url.pathname}`);
    let body = supplied.body.evidence && omit ? { ...supplied.body, evidence: supplied.body.evidence.filter((row) => row.canonical_action_id !== omit) } : supplied.body;
    if (measureReferences && body.evidence) {
      body = { ...body, evidence: body.evidence.map((row) => {
        const target = row.canonical_action_id === "house:119:2:282";
        if (target) expect(row.source_url).toBe("https://clerk.house.gov/evs/2026/roll282.xml");
        // Add the independently verified existing FK fact to a response copy;
        // the historical snapshot/presentation/finding hashes stay untouched.
        return { ...row, measure_reference: target ? { congress: 119, type: "hconres", number: 89 } : null };
      }) };
    }
    return route.fulfill({ status: supplied.status, json: body });
  });
}

async function releasedCardSnapshot(page, options = {}) {
  const entries = page.getByTestId("record-card-entry");
  // evaluateAll reads immediately; both snapshots require the full bound list.
  await expect(entries).toHaveCount(candidate.entries.length, options);
  return entries.evaluateAll((nodes) => nodes.map((node) => ({ id: node.id, href: node.getAttribute("href"), text: node.textContent })));
}

test("released card snapshot waits for a held editorial response", async ({ page }) => {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  await releasedResponses(page, { editorialGate: gate });
  try {
    await page.goto(`/?representative=${foushee.id}&scope=all`);
    const captured = releasedCardSnapshot(page);
    await expect(page.getByRole("region", { name: "Reviewed findings status" })).toContainText("Loading reviewed findings");
    await expect(page.getByTestId("record-card-entry")).toHaveCount(0);
    release();
    expect(await captured).toHaveLength(candidate.entries.length);
  } finally {
    release();
  }
});

test("released card snapshot rejects unavailable findings instead of accepting an empty baseline", async ({ page }) => {
  await releasedResponses(page);
  await page.route(/\/editorial-presentations(?:\?|$)/, (route) => route.fulfill({ status: 503, json: { detail: "Unavailable" } }));
  await page.goto(`/?representative=${foushee.id}&scope=all`);
  await expect(page.getByRole("region", { name: "Reviewed findings status" })).toContainText("Reviewed findings are unavailable right now.");
  await expect(releasedCardSnapshot(page, { timeout: 500 })).rejects.toThrow(/toHaveCount/);
});

for (const width of [320, 390, 768, 1440]) test(`sourced H.Con.Res.89 finds the released Roll282 receipt at ${width}px without changing evidence or history`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 900 });
  await releasedResponses(page, { measureReferences: true });
  await page.route("**/legislators/*/contact", route => route.fulfill({ json: contact }));
  await page.goto(`/?representative=${foushee.id}&scope=119`);
  await expect(page.locator(`#${warPowers.id}`)).toBeVisible();
  const cards = await page.getByTestId("record-card-entry").evaluateAll(nodes => nodes.map(node => ({ id: node.id, href: node.getAttribute("href"), text: node.textContent })));
  await page.locator(`#${warPowers.id}`).click();
  await page.getByRole("navigation", { name: "Selected issue sections" }).getByRole("link", { name: "Vote record", exact: true }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(9);
  const target = page.locator('[data-canonical-action-id="house:119:2:282"]');
  await expect(target).toContainText("Associated measure: H.Con.Res. 89 (Congress 119)");
  await expect(target.locator(":scope > button")).toHaveAccessibleName(/associated measure H\.Con\.Res\. 89/);
  if (await target.locator(":scope > button").getAttribute("aria-expanded") !== "true") await target.locator(":scope > button").click();
  const sources = await stableReceiptHtml(target);
  const ids = await receiptIds(page), accounting = await page.locator(".pattern-strip").innerText();
  const coverage = await page.locator("#issue-summary").innerText();
  const url = page.url(), historyLength = await page.evaluate(() => history.length);
  const requests = [];
  page.on("request", request => requests.push(request.url()));
  await filter(page).focus();
  await page.keyboard.type("H.Con.Res. 89");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  expect(await receiptIds(page)).toEqual(["house:119:2:282"]);
  await expect(filter(page)).toBeFocused();
  await expect(page.getByTestId("local-record-filter-status")).toContainText("1 of 9 loaded linked receipts");
  expect(await stableReceiptHtml(target)).toBe(sources);
  expect(await page.locator(".pattern-strip").innerText()).toBe(accounting);
  expect(await page.locator("#issue-summary").innerText()).toBe(coverage);
  expect(page.url()).toBe(url); expect(await page.evaluate(() => history.length)).toBe(historyLength);
  expect(requests).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Clear text filter", exact: true }).click();
  expect(await receiptIds(page)).toEqual(ids);
  await target.getByRole("button", { name: "Official contact information", exact: true }).click();
  await expect(target.getByRole("region", { name: "Official contact information", exact: true })).toContainText("Stored contact details");
  await filter(page).fill("hconres89");
  await expect(target.getByRole("region", { name: "Official contact information", exact: true })).toBeVisible();
  await target.screenshot({ path: testInfo.outputPath(`measure-reference-${width}.png`) });
  await page.reload(); await expect(filter(page)).toHaveValue("");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(9);
  await expect(target).toContainText("Associated measure: H.Con.Res. 89 (Congress 119)");
  expect(page.url()).toBe(url);
  await page.goBack(); await expect(page.getByTestId("card-finding-detail")).toBeVisible();
  await page.goForward(); await expect(page.locator("[data-canonical-action-id]")).toHaveCount(9);
  await page.goto(`/?representative=${foushee.id}&scope=119`);
  await expect(page.locator(`#${warPowers.id}`)).toBeVisible();
  expect(await page.getByTestId("record-card-entry").evaluateAll(nodes => nodes.map(node => ({ id: node.id, href: node.getAttribute("href"), text: node.textContent })))).toEqual(cards);
});

test("amendment receipt keeps its exact action and meaning beside its associated measure", async ({ page }) => {
  const amendment = { ...available[0], action_label: "Exact reporting deadline amendment", vote_type: "amendment",
    vote_context: { ...available[0].vote_context, vote_type: "amendment" },
    plain_english_summary: "Only the stated reporting deadlines would change.",
    measure_reference: { congress: 119, type: "hr", number: 7148 } };
  await installPassARoutes(page, { evidenceOverrides: { ECONOMY_TAXES: [amendment] } });
  await page.goto(economyUrl);
  const target = receipt(page, amendment.rollcall_number);
  await expect(target).toContainText("Exact reporting deadline amendment");
  await expect(target).toContainText("Associated measure: H.R. 7148 (Congress 119)");
  await expect(target).toContainText("Amendment");
  await target.locator(":scope > button").click();
  await expect(target).toContainText("Only the stated reporting deadlines would change.");
  const sources = await target.locator("div.grid").innerHTML();
  await filter(page).fill("hr7148");
  await expect(target).toBeVisible();
  expect(await target.locator("div.grid").innerHTML()).toBe(sources);
});

for (const partial of [false, true]) test(`released finding ${partial ? "partial" : "complete"} response keeps source identity, coverage and history`, async ({ page }) => {
  await releasedResponses(page, { omit: partial ? warPowers.action_ids[0] : null });
  await page.goto(`/?representative=${foushee.id}&scope=all`);
  const cards = await releasedCardSnapshot(page);
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
  expect(await releasedCardSnapshot(page)).toEqual(cards);
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
  if (width === 320) {
    await page.evaluate(() => {
      const group = document.getElementById("local-record-filter").parentElement.parentElement;
      const header = document.querySelector("header.sticky");
      window.scrollBy({ top: group.getBoundingClientRect().top - header.getBoundingClientRect().bottom - 16, behavior: "instant" });
    });
    await expectFilterUnobscured(page);
    await expect(page.getByRole("button", { name: "Clear text filter", exact: true })).toBeFocused();
    await page.screenshot({ path: testInfo.outputPath("local-filter-320.png") });
  } else await page.locator("#vote-record").screenshot({ path: testInfo.outputPath(`local-filter-${width}.png`) });
  await page.keyboard.press("Enter"); await expect(filter(page)).toBeFocused();
  await expect(filter(page)).toHaveValue("");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(12);
  if (width === 320) await expectFilterUnobscured(page);
});

async function expectFilterUnobscured(page) {
  for (const target of [filter(page), page.locator("#local-record-filter-help"), page.getByTestId("local-record-filter-status")]) {
    await expect(target).toBeInViewport({ ratio: 1 });
    const visibility = await target.evaluate((node) => {
      const rect = node.getBoundingClientRect(), header = document.querySelector("header.sticky").getBoundingClientRect();
      const covering = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
      return { top: rect.top, headerBottom: header.bottom, unobscured: node === covering || node.contains(covering) };
    });
    expect(visibility.top).toBeGreaterThanOrEqual(visibility.headerBottom);
    expect(visibility.unobscured).toBe(true);
  }
}

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
