import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { gunzipSync } from "node:zlib";
import { foushee, installPassARoutes } from "./pass-a-fixtures.mjs";

const contact = {
  legislator_id: foushee.id, contact_status: "loaded", data_source: "database",
  phone: "(202) 225-1784", official_website_url: "https://foushee.house.gov/",
  contact_form_url: "https://foushee.house.gov/contact",
  source_url: "https://foushee.house.gov/", source_type: "official_house_website",
  source_retrieved_at: "2026-05-19",
};
const trigger = (receipt) => receipt.getByRole("button", { name: "Official contact information", exact: true });
const panel = (receipt) => receipt.getByRole("region", { name: "Official contact information", exact: true });
const close = (receipt) => panel(receipt).getByRole("button", { name: "Close contact information", exact: true });

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await installPassARoutes(page);
});

for (const width of [320, 390, 1440]) test(`optional contact keyboard flow restores focus and fits ${width}px`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 900 });
  await page.route("**/legislators/*/contact", (route) => route.fulfill({ json: contact }));
  const receipt = await selectedReceipt(page);
  await trigger(receipt).focus(); await page.keyboard.press("Enter");
  await expect(panel(receipt)).toContainText("Retrieved: 2026-05-19");
  await page.keyboard.press("Tab"); await expect(close(receipt)).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await receipt.screenshot({ path: testInfo.outputPath(`contact-${width}.png`) });
  await page.keyboard.press("Enter"); await expect(panel(receipt)).toHaveCount(0);
  await expect(trigger(receipt)).toBeFocused();
  await page.keyboard.press("Enter"); await expect(panel(receipt)).toContainText("Stored contact details");
});

const states = [
  ["curated fallback", { ...contact, data_source: "curated_fallback" }, "Curated fallback contact details", 4],
  ["missing", { legislator_id: foushee.id, contact_status: "not_loaded", data_source: "none" }, "Contact details are not loaded", 0],
  ["partial", { legislator_id: foushee.id, contact_status: "loaded", phone: contact.phone }, "Retrieval date not supplied", 1],
  ["unsafe", { ...contact, phone: "2022251784;ext=99", official_website_url: "javascript:alert(1)", contact_form_url: "https://foushee.house.gov/contact?vote=32", source_url: "https://foushee.house.gov.evil.example/" }, "Some supplied contact details could not be displayed", 0],
  ["wrong member", { ...contact, legislator_id: "leg_thomas_massie" }, "Contact information is unavailable right now", 0],
  ["invalid response", {}, "Contact information is unavailable right now", 0],
  ["HTTP error", contact, "Contact information is unavailable right now", 0, 503],
];
for (const [name, payload, message, linkCount, status = 200] of states) test(`contact ${name} state is truthful and keeps evidence usable`, async ({ page }) => {
  await page.route("**/legislators/*/contact", (route) => route.fulfill({ status, json: payload }));
  const receipt = await selectedReceipt(page);
  const before = await receipt.locator("div.grid").innerHTML();
  await trigger(receipt).click(); await expect(panel(receipt)).toContainText(message);
  await expect(panel(receipt).getByRole("link")).toHaveCount(linkCount);
  await expect(panel(receipt)).not.toContainText(/verified today|your representative|currently serves/i);
  expect(await receipt.locator("div.grid").innerHTML()).toBe(before);
  await close(receipt).click(); await expect(trigger(receipt)).toBeFocused();
});

async function holdContact(page, nextPayload = (id) => ({ ...contact, legislator_id: id, phone: "(202) 225-0000" })) {
  await page.addInitScript(() => {
    window.contactCompletions = 0;
    const fetch = window.fetch;
    window.fetch = async (...args) => {
      const response = await fetch(...args);
      if (String(args[0]).endsWith("/contact")) {
        if (!response.ok) window.contactCompletions += 1;
        const json = response.json.bind(response);
        response.json = async () => { try { return await json(); } finally { window.contactCompletions += 1; } };
      }
      return response;
    };
  });
  let received, count = 0;
  const pending = new Promise((resolve) => { received = resolve; });
  await page.route("**/legislators/*/contact", (route) => {
    if (++count === 1) { received(route); return; }
    const id = new URL(route.request().url()).pathname.split("/")[2];
    return route.fulfill({ json: nextPayload(id) });
  });
  return {
    pending,
    async finish(status = 200) {
      const completed = await page.evaluate(() => window.contactCompletions);
      await (await pending).fulfill({ status, json: contact });
      await page.waitForFunction((before) => window.contactCompletions > before, completed);
      await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    },
  };
}

for (const status of [200, 503]) test(`Close and reopen isolates late contact ${status === 200 ? "success" : "error"}`, async ({ page }) => {
  const held = await holdContact(page);
  const receipt = await selectedReceipt(page);
  await trigger(receipt).click(); await held.pending;
  await expect(panel(receipt).getByRole("status")).toHaveText("Loading contact information.");
  await close(receipt).click(); await expect(trigger(receipt)).toBeFocused();
  await trigger(receipt).press("Enter"); await expect(panel(receipt)).toContainText("225-0000");
  await held.finish(status);
  await expect(panel(receipt)).toContainText("225-0000");
  await expect(panel(receipt)).not.toContainText("225-1784");
  await expect(panel(receipt).getByRole("alert")).toHaveCount(0);
  await expect(trigger(receipt)).toBeFocused();
});

for (const change of ["issue", "scope"]) test(`${change} changes invalidate an open contact request`, async ({ page }) => {
  const held = await holdContact(page);
  const receipt = await selectedReceipt(page);
  await trigger(receipt).click(); await held.pending;
  if (change === "scope") await page.getByRole("button", { name: "All available Congresses", exact: true }).click();
  else await page.getByRole("button", { name: "Browse vote record for Economy & Taxes", exact: true }).click();
  await expect(page.getByRole("region", { name: "Official contact information", exact: true })).toHaveCount(0);
  const next = page.locator("[data-canonical-action-id]").first();
  await next.locator(":scope > button").click();
  await trigger(next).click(); await expect(panel(next)).toContainText("225-0000");
  await held.finish(); await expect(panel(next)).not.toContainText("225-1784");
});

test("collapsing a receipt ignores a pending contact response without changing receipt focus", async ({ page }) => {
  const held = await holdContact(page);
  const receipt = await selectedReceipt(page);
  await trigger(receipt).click(); await held.pending;
  await receipt.locator(":scope > button").click(); await held.finish();
  await expect(receipt.locator(":scope > button")).toBeFocused();
  await expect(trigger(receipt)).toHaveCount(0);
  await receipt.locator(":scope > button").click(); await trigger(receipt).click();
  await expect(panel(receipt)).toContainText("225-0000");
});

const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/review_packets/record_at_a_glance_v1/candidate.json")));
const snapshot = JSON.parse(gunzipSync(fs.readFileSync(path.resolve("..", candidate.source_snapshot))));
const massie = { id: "leg_thomas_massie", name_display: "Thomas Massie", chamber: "house", state: "KY", district: "04", party: "R", bioguide_id: "M001184" };
const senator = { id: "leg_angela_d_alsobrooks", name_display: "Angela D. Alsobrooks", chamber: "senate", state: "MD", party: "D", bioguide_id: "A000381" };
async function releasedResponses(page) {
  await page.route("http://localhost:8000/**", (route) => {
    const url = new URL(route.request().url()), member = url.pathname.split("/")[2];
    if (url.pathname.endsWith("/profile")) return route.fulfill({ json: [foushee, massie, senator].find((p) => p.id === member) });
    const resource = url.pathname.endsWith("/editorial-presentations") ? "editorial" : url.pathname.endsWith("/evidence") ? url.pathname.split("/")[4] : "positions";
    const supplied = snapshot[`${member}:${url.searchParams.get("scope") || "all"}:${resource}`];
    if (!supplied) throw Error(`Unexpected fixture read: ${url.pathname}`);
    return route.fulfill({ status: supplied.status, json: supplied.body });
  });
}

test("member switching cannot render late contact details in another member's record", async ({ page }) => {
  await releasedResponses(page);
  await page.route("**/legislators/search?*", (route) => route.fulfill({ json: { results: [massie] } }));
  const held = await holdContact(page, (id) => ({ legislator_id: id, contact_status: "not_loaded", data_source: "none" }));
  const receipt = await selectedReceipt(page, "119", "ENVIRONMENT_ENERGY", "house:119:1:112");
  await trigger(receipt).click(); await held.pending;
  await page.getByRole("button", { name: "Switch representative", exact: true }).click();
  await page.getByLabel("Search by name", { exact: true }).fill("Massie");
  await page.getByLabel("Search by name", { exact: true }).press("Enter");
  await page.getByRole("button", { name: /^Select Thomas Massie/ }).click();
  await expect(page.locator("#representative-name")).toBeFocused();
  await page.getByRole("button", { name: "Browse vote record for Economy & Taxes", exact: true }).click();
  const next = page.locator("[data-canonical-action-id]").first(); await next.locator(":scope > button").click();
  await trigger(next).click(); await expect(panel(next)).toContainText("Contact details are not loaded");
  await held.finish(); await expect(panel(next)).not.toContainText("225-1784");
  await expect(panel(next)).toContainText("Thomas Massie");
});

test("contact preserves all six cards, finding/source hash, history and exact source markup in both scopes", async ({ page }) => {
  test.setTimeout(60_000);
  await releasedResponses(page);
  await page.route("**/legislators/*/contact", (route) => route.fulfill({ json: contact }));
  for (const scope of ["all", "119"]) {
    await page.goto(`/?representative=${foushee.id}&scope=${scope}`);
    const cards = page.getByTestId("record-card-entry"); await expect(cards).toHaveCount(6);
    const readCards = () => cards.evaluateAll((nodes) => nodes.map((node) => ({
      id: node.querySelector("a[id]").id, href: node.querySelector("a[id]").getAttribute("href"), text: node.textContent,
    }))); const beforeCards = await readCards();
    await page.locator("#record-card-wording-synthesis-war-powers").click();
    const detailUrl = page.url();
    await page.getByRole("navigation", { name: "Selected issue sections" }).getByRole("link", { name: "Vote record", exact: true }).click();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(9);
    const receipt = page.locator("[data-canonical-action-id]").first();
    await expect(receipt.locator(":scope > button")).toHaveAttribute("aria-expanded", "true");
    const before = await receipt.locator("div.grid").innerHTML(), url = page.url();
    await trigger(receipt).click(); await expect(panel(receipt)).toContainText("Stored contact details");
    await close(receipt).click(); expect(page.url()).toBe(url);
    expect(await receipt.locator("div.grid").innerHTML()).toBe(before);
    await page.goBack(); await expect(page).toHaveURL(detailUrl);
    await page.goForward(); await expect(page).toHaveURL(url);
    await page.reload(); await expect(page.locator("[data-canonical-action-id]")).toHaveCount(9);
    await page.getByRole("link", { name: /Return to record at a glance/ }).click();
    await expect(cards).toHaveCount(6); expect(await readCards()).toEqual(beforeCards);
  }
});

for (const position of ["present", "not_voting"]) test(`contact does not reinterpret a ${position} receipt`, async ({ page }) => {
  await installPassARoutes(page, { evidenceOverrides: { EDUCATION_WORKFORCE: [{
    roll_call_id: "house:119:1:500", rollcall_number: 500, congress: 119, chamber: "house",
    vote_date: "2025-03-20", position, description: "Education record", source_url: "https://clerk.house.gov/evs/2025/roll500.xml",
  }] } });
  await page.route("**/legislators/*/contact", (route) => route.fulfill({ json: contact }));
  const receipt = await selectedReceipt(page, "119", "EDUCATION_WORKFORCE", "house:119:1:500");
  const before = await receipt.locator("div.grid").innerHTML();
  await trigger(receipt).click(); await expect(panel(receipt)).toContainText("Stored contact details");
  expect(await receipt.locator("div.grid").innerHTML()).toBe(before);
});

test("a sparse Senate receipt has the same optional honest missing-contact disclosure", async ({ page }) => {
  await releasedResponses(page);
  await page.route("**/legislators/*/contact", (route) => route.fulfill({ json: { legislator_id: senator.id, contact_status: "not_loaded", data_source: "none" } }));
  await page.goto(`/?representative=${senator.id}&scope=119&issue=EDUCATION_WORKFORCE`);
  const receipt = page.locator("[data-canonical-action-id]").first(); await receipt.locator(":scope > button").click();
  await trigger(receipt).click(); await expect(panel(receipt)).toContainText("Contact details are not loaded");
  await expect(panel(receipt)).toContainText(senator.name_display); await expect(panel(receipt).getByRole("link")).toHaveCount(0);
});

test("the recorded-snapshot review route stays isolated from live contact metadata", async ({ page }) => {
  const reads = [];
  page.on("request", (request) => { if (request.url().endsWith("/contact")) reads.push(request.url()); });
  await page.goto(`/review/record-card?representative=${foushee.id}&scope=119&issue=ENVIRONMENT_ENERGY#action-receipt-house-119-1-112`);
  const receipt = page.locator('[data-canonical-action-id="house:119:1:112"]');
  await expect(receipt.getByRole("button")).toBeFocused();
  await expect(trigger(receipt)).toHaveCount(0); expect(reads).toEqual([]);
});

async function selectedReceipt(page, scope = "119", issue = "JUSTICE_PUBLIC_SAFETY", action = "house:119:1:32") {
  await page.goto(`/?representative=${foushee.id}&scope=${scope}&issue=${issue}#action-receipt-${action.replaceAll(":", "-")}`);
  const receipt = page.locator(`[data-canonical-action-id="${action}"]`);
  await expect(receipt.locator(":scope > button")).toBeFocused();
  return receipt;
}

test("contact is lazy, preserves exact receipt/history, and external navigation sends no referrer or query", async ({ page, context }) => {
  const requests = [], outbound = [];
  await page.route("**/legislators/*/contact", (route) => {
    requests.push({ method: route.request().method(), url: route.request().url() });
    return route.fulfill({ json: contact });
  });
  await context.route("https://foushee.house.gov/**", (route) => {
    outbound.push({ url: route.request().url(), referrer: route.request().headers().referer });
    return route.fulfill({ contentType: "text/html", body: "<p>Intercepted official-site navigation</p>" });
  });
  const receipt = await selectedReceipt(page);
  const meaning = await receipt.locator("div.grid").innerHTML();
  const url = page.url(), historyLength = await page.evaluate(() => history.length);
  expect(requests).toEqual([]);
  await trigger(receipt).focus(); await trigger(receipt).press("Enter");
  await expect(panel(receipt)).toContainText("Stored contact details");
  await expect(panel(receipt)).toContainText("Retrieved: 2026-05-19");
  await expect(panel(receipt).getByRole("link", { name: /225-1784/ })).toHaveAttribute("href", "tel:2022251784");
  expect(requests).toEqual([{ method: "GET", url: `http://localhost:8000/legislators/${foushee.id}/contact` }]);
  expect(outbound).toEqual([]);
  expect(await receipt.locator("div.grid").innerHTML()).toBe(meaning);
  expect(page.url()).toBe(url); expect(await page.evaluate(() => history.length)).toBe(historyLength);
  const form = panel(receipt).getByRole("link", { name: "Contact form", exact: true });
  await expect(form).toHaveAttribute("rel", "noopener noreferrer");
  await expect(form).toHaveAttribute("referrerpolicy", "no-referrer");
  const popupEvent = page.waitForEvent("popup");
  await form.click(); const popup = await popupEvent; await popup.waitForLoadState();
  expect(outbound).toEqual([{ url: contact.contact_form_url, referrer: undefined }]);
  await popup.close(); await close(receipt).click();
  await expect(trigger(receipt)).toBeFocused();
  expect(await receipt.locator("div.grid").innerHTML()).toBe(meaning);
  expect(page.url()).toBe(url);
});
