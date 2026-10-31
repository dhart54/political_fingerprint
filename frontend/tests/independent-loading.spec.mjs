import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { expect, test } from "@playwright/test";
import { foushee } from "./pass-a-fixtures.mjs";
import { recordCardUrl } from "../lib/recordCard.mjs";

const candidate = JSON.parse(fs.readFileSync(new URL("../../docs/review_packets/record_at_a_glance_v1/candidate.json", import.meta.url)));
const snapshot = JSON.parse(gunzipSync(fs.readFileSync(new URL(`../../${candidate.source_snapshot}`, import.meta.url))));
const selected = "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119";
const education = candidate.entries.find(entry => entry.issue_id === "EDUCATION_WORKFORCE");
const sourceHash = candidate.sources.find(source => source.issue_id === education.issue_id).presentation_sha256["119"];
const linked = view => recordCardUrl("/", { legislatorId: foushee.id, scope: "119", issue: education.issue_id, findingId: education.finding_id, sourceHash, view, hash: view === "receipts" ? "vote-record" : "finding-detail" });
const massie = { id: "leg_thomas_massie", bioguide_id: "M001184", name_display: "Thomas Massie", chamber: "house", state: "KY", district: "04", party: "R" };

async function installSnapshot(page) {
  const calls = [];
  await page.route("http://localhost:8000/**", async route => {
    const url = new URL(route.request().url());
    const member = url.pathname.split("/")[2];
    if (url.pathname === "/legislators/search") return route.fulfill({ json: { results: [massie] } });
    const scope = url.searchParams.get("scope") || "all";
    const resource = url.pathname.endsWith("/profile") ? "profile" : url.pathname.endsWith("/editorial-presentations") ? "editorial" : url.pathname.endsWith("/evidence") ? url.pathname.split("/")[4] : "positions";
    calls.push({ member, scope, resource });
    if (resource === "profile") return route.fulfill({ json: member === massie.id ? massie : foushee });
    const supplied = snapshot[`${member}:${scope}:${resource}`];
    if (!supplied) throw Error(`Unexpected snapshot request: ${url.pathname}`);
    return route.fulfill({ status: supplied.status, json: supplied.body });
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  return calls;
}

async function hold(page, resource, scope = "119") {
  let release, arrived;
  const gate = new Promise(resolve => { release = resolve; });
  const pending = new Promise(resolve => { arrived = resolve; });
  await page.route(`**/${resource}?scope=${scope}`, async route => {
    arrived();
    await gate;
    await route.fallback();
  });
  return { release, pending };
}

test("available receipts do not wait for pending analysis", async ({ page }, testInfo) => {
  const calls = await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(selected);
    await analysis.pending;
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    expect(calls.some(call => call.resource === "EDUCATION_WORKFORCE")).toBe(true);
    await expect(page.locator("#issue-summary")).toContainText("Issue summary loading");
    await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
    await expect(page.getByText("8 additional recorded actions", { exact: false })).toHaveCount(0);
    await page.screenshot({ path: testInfo.outputPath("pending-analysis.png") });
    analysis.release();
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope · 3 findings supported by 6 votes");
    await expect(page.locator("#issue-summary")).toContainText("8 additional recorded actions");
  } finally { analysis.release(); }
});

test("analysis can settle before positions without exposing premature receipts", async ({ page }) => {
  const calls = await installSnapshot(page);
  const positions = await hold(page, "positions");
  try {
    await page.goto(selected);
    await positions.pending;
    await expect(page.getByTestId("record-card")).toBeVisible();
    await expect(page.getByText("Loading issue records…", { exact: true })).toBeVisible();
    await expect(page.locator("#issue-summary")).toHaveCount(0);
    expect(calls.some(call => call.resource === "EDUCATION_WORKFORCE")).toBe(false);
    positions.release();
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope");
  } finally { positions.release(); }
});

for (const resource of ["positions", "editorial-presentations"]) for (const failure of ["503", "network"]) {
  test(`${resource} ${failure} does not discard the other response`, async ({ page }) => {
    await installSnapshot(page);
    await page.route(`**/${resource}?scope=119`, route => failure === "503" ? route.fulfill({ status: 503, body: "unavailable" }) : route.abort("failed"));
    await page.goto(selected);
    if (resource === "positions") {
      await expect(page.locator("#issues").getByRole("alert")).toContainText("issue records are unavailable");
      await expect(page.getByTestId("record-card")).toBeVisible();
      await expect(page.locator("#vote-record")).toHaveCount(0);
    } else {
      await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
      await expect(page.locator("#issue-summary")).toContainText("Issue summary unavailable");
      await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
    }
  });
}

for (const mismatch of ["member", "scope", "incomplete", "source"]) {
  test(`analysis ${mismatch} preserves evidence and rejects invalid finding selection`, async ({ page }) => {
    await installSnapshot(page);
    await page.route("**/editorial-presentations?scope=119", route => {
      const body = structuredClone(snapshot[`${foushee.id}:119:editorial`].body);
      if (mismatch === "member") body.member_bioguide_id = "M001184";
      if (mismatch === "scope") body.scope = "118";
      if (mismatch === "incomplete") body.presentations.pop();
      if (mismatch === "source") body.presentations.find(p => p.issue_id === education.issue_id).provenance.test_revision = "unbound";
      return route.fulfill({ json: body });
    });
    await page.goto(linked("receipts"));
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await expect(page.getByTestId("card-finding-detail")).toHaveCount(0);
    await expect(page.getByText(/This finding link does not match/)).toBeVisible();
    if (mismatch !== "source") await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
  });
}

for (const field of ["legislator_id", "scope"]) test(`invalid positions ${field} cannot start receipts`, async ({ page }) => {
  const calls = await installSnapshot(page);
  await page.route("**/positions?scope=119", route => {
    const body = structuredClone(snapshot[`${foushee.id}:119:positions`].body);
    body[field] = field === "scope" ? "118" : massie.id;
    return route.fulfill({ json: body });
  });
  await page.goto(selected);
  await expect(page.locator("#issues").getByRole("alert")).toContainText("issue records are unavailable");
  await expect(page.getByTestId("record-card")).toBeVisible();
  expect(calls.some(call => call.resource === "EDUCATION_WORKFORCE")).toBe(false);
});

test("empty reviewed analysis is distinct from pending and failure", async ({ page }) => {
  await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations", "118");
  try {
    await page.goto(selected.replace("scope=119", "scope=118"));
    await analysis.pending;
    await expect(page.locator("#vote-record")).toBeAttached();
    await expect(page.locator("#issue-summary")).toContainText("Issue summary loading");
    await expect(page.getByText(/No reviewed findings are available/)).toHaveCount(0);
    analysis.release();
    await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
    await expect(page.locator("#issue-summary")).toContainText("No issue summary for this scope");
    await expect(page.getByText(/Issue summaries could not be verified/)).toHaveCount(0);
  } finally { analysis.release(); }
});

for (const width of [320, 390, 1440]) test(`late analysis preserves receipt controls, focus and links at ${width}px`, async ({ page }, testInfo) => {
  await installSnapshot(page);
  await page.setViewportSize({ width, height: 900 });
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(selected);
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    const filter = page.getByRole("searchbox", { name: "Filter loaded receipts by measure, roll or title" });
    await filter.fill("PROTECT Our Kids");
    const row = page.locator("[data-canonical-action-id]").first();
    const disclosure = row.locator(":scope > button");
    await disclosure.click();
    await expect(disclosure).toHaveAttribute("aria-expanded", "true");
    const before = await row.innerText();
    await filter.focus();
    const focusedY = await filter.evaluate(element => element.getBoundingClientRect().top);
    analysis.release();
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope");
    await expect(filter).toHaveValue("PROTECT Our Kids");
    await expect(filter).toBeFocused();
    await expect(disclosure).toHaveAttribute("aria-expanded", "true");
    expect(await row.innerText()).toBe(before);
    await expect(row.getByRole("link", { name: "Official vote", exact: true })).toHaveAttribute("href", "https://clerk.house.gov/Votes/2025313");
    await expect(row.getByRole("link", { name: "Original vote source (XML)" })).toHaveAttribute("href", "https://clerk.house.gov/evs/2025/roll313.xml");
    await expect.poll(() => filter.evaluate((element, before) => Math.abs(element.getBoundingClientRect().top - before), focusedY)).toBeLessThanOrEqual(5);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`independent-loading-${width}.png`) });
  } finally { analysis.release(); }
});

test("late analysis failure preserves available receipt state", async ({ page }) => {
  await installSnapshot(page);
  await page.route("**/editorial-presentations?scope=119", route => route.fulfill({ status: 503, body: "unavailable" }));
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(selected);
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    const filter = page.getByRole("searchbox", { name: "Filter loaded receipts by measure, roll or title" });
    await filter.fill("PROTECT Our Kids");
    analysis.release();
    await expect(page.locator("#issue-summary")).toContainText("Issue summary unavailable");
    await expect(filter).toHaveValue("PROTECT Our Kids");
    await expect(filter).toBeFocused();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
  } finally { analysis.release(); }
});

test("receipt failure and retry remain independent of pending analysis", async ({ page }) => {
  await installSnapshot(page);
  let fail = true;
  await page.route("**/positions/EDUCATION_WORKFORCE/evidence?*", route => fail ? route.fulfill({ status: 503, body: "unavailable" }) : route.fallback());
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(selected);
    await expect(page.locator("#issue-detail").getByRole("alert")).toContainText("exact vote receipts");
    fail = false;
    await page.getByRole("button", { name: "Retry vote receipts", exact: true }).click();
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await expect(page.locator("#issue-summary")).toContainText("Issue summary loading");
    analysis.release();
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope");
  } finally { analysis.release(); }
});

test("summary-only discovery distinguishes pending from unavailable", async ({ page }) => {
  await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(selected);
    await expect(page.locator("#vote-record")).toBeAttached();
    await page.getByRole("button", { name: "Issue summaries", exact: true }).click();
    await expect(page.getByText("Issue summaries are still loading. Browse recorded votes using the other views.")).toBeVisible();
    await expect(page.getByText(/No plain-language issue summary is available/)).toHaveCount(0);
    analysis.release();
    await expect(page.getByRole("button", { name: "Explore Education & Workforce", exact: true })).toBeVisible();
  } finally { analysis.release(); }
});

for (const view of [null, "receipts"]) test(`pending finding ${view || "detail"} is not reported as mismatched`, async ({ page }) => {
  const calls = await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(linked(view));
    await expect(page.getByText("The linked reviewed finding is still loading.")).toBeVisible();
    await expect.poll(() => calls.some(call => call.resource === "EDUCATION_WORKFORCE")).toBe(true);
    await expect(page.getByText(/This finding link does not match/)).toHaveCount(0);
    await expect(page.locator("#vote-record")).toHaveCount(0);
    analysis.release();
    await expect(page.getByTestId("card-finding-detail")).toBeVisible();
    if (view === "receipts") await expect(page.locator("#vote-record")).toContainText("Showing 2 of 2 matching votes");
    else await expect(page.locator("#finding-detail-heading")).toBeFocused();
  } finally { analysis.release(); }
});

test("leaving a pending finding for the complete record survives late analysis and Back/Forward", async ({ page }) => {
  await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(linked("receipts"));
    const fallback = page.getByRole("link", { name: "Browse the complete issue record", exact: true });
    await fallback.focus();
    await page.keyboard.press("Enter");
    await expect(page).not.toHaveURL(/finding=/);
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    const filter = page.getByRole("searchbox", { name: "Filter loaded receipts by measure, roll or title" });
    await filter.focus();
    analysis.release();
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope");
    await expect(filter).toBeFocused();
    await expect(page.getByTestId("card-finding-detail")).toHaveCount(0);
    await page.goBack();
    await expect(page.locator("#vote-record")).toContainText("Showing 2 of 2 matching votes");
    await page.goForward();
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
  } finally { analysis.release(); }
});

for (const resource of ["positions", "editorial-presentations"]) test(`late ${resource} from abandoned scope cannot replace current evidence`, async ({ page }) => {
  await installSnapshot(page);
  const held = await hold(page, resource);
  try {
    await page.goto(selected);
    await held.pending;
    await page.getByRole("button", { name: "118th Congress", exact: true }).click();
    await expect(page.locator("#vote-record")).toBeAttached();
    await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
    const before = await page.locator("#issue-detail").innerText();
    const settled = page.waitForResponse(response => response.url().includes(`/${resource}?scope=119`));
    held.release();
    await settled;
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    expect(await page.locator("#issue-detail").innerText()).toBe(before);
    await expect(page).toHaveURL(/scope=118/);
    await expect(page.getByTestId("record-card")).toHaveCount(0);
    await page.goBack();
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope");
  } finally { held.release(); }
});

test("a representative switch ignores old analysis and retains the new empty state", async ({ page }) => {
  await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations");
  // The hold applies only to the original member; allow the new member through.
  await page.route(`**/legislators/${massie.id}/editorial-presentations?*`, route => route.fulfill({ json: snapshot[`${massie.id}:${new URL(route.request().url()).searchParams.get("scope") || "all"}:editorial`].body }));
  try {
    await page.goto(selected);
    await analysis.pending;
    await page.getByRole("button", { name: "Switch representative", exact: true }).click();
    await page.getByLabel("Search by name", { exact: true }).fill("Thomas Massie");
    await page.getByRole("button", { name: "Search names", exact: true }).click();
    await page.getByRole("button", { name: /^Select Thomas Massie,/ }).click();
    await expect(page.locator("#representative-name")).toHaveText("Thomas Massie");
    await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
    const settled = page.waitForResponse(response => response.url().includes(`${foushee.id}/editorial-presentations`));
    analysis.release();
    await settled;
    await expect(page.getByTestId("record-card")).toHaveCount(0);
    await expect(page.locator("#representative-name")).toHaveText("Thomas Massie");
  } finally { analysis.release(); }
});

for (const view of [null, "receipts"]) for (const control of ["scope", "fallback"]) test(`late linked ${view || "detail"} preserves ${control} focus`, async ({ page }) => {
  await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(linked(view));
    await expect(page.getByText("The linked reviewed finding is still loading.")).toBeVisible();
    const target = control === "scope" ? page.getByRole("button", { name: "119th Congress", exact: true }) : page.getByRole("link", { name: "Browse the complete issue record", exact: true });
    await target.focus();
    analysis.release();
    await expect(page.getByTestId("card-finding-detail")).toBeVisible();
    await expect(target).toBeFocused();
  } finally { analysis.release(); }
});

for (const width of [390, 1440]) test(`restores section while analysis is pending at ${width}px`, async ({ page }) => {
  await installSnapshot(page);
  await page.setViewportSize({ width, height: 900 });
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(`${selected}#issue-summary`);
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await expect(page.locator("#selected-issue-heading")).toBeFocused();
    const offset = () => page.locator("#issue-summary").evaluate(element => element.getBoundingClientRect().top - document.querySelector("main > header").getBoundingClientRect().bottom);
    await expect.poll(offset).toBeGreaterThanOrEqual(0);
    await expect.poll(offset).toBeLessThan(30);
    analysis.release();
    await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope");
    await expect(page.locator("#selected-issue-heading")).toBeFocused();
    await expect.poll(offset).toBeGreaterThanOrEqual(0);
    await expect.poll(offset).toBeLessThan(30);
  } finally { analysis.release(); }
});

for (const width of [1440, 1024]) test(`initial issue landing stays visible when analysis precedes receipts at ${width}px`, async ({ page }) => {
  await installSnapshot(page);
  await page.setViewportSize({ width, height: 1000 });
  const analysis = await hold(page, "editorial-presentations");
  const receipts = await hold(page, "evidence");
  try {
    await page.goto(selected);
    await expect(page.locator("#selected-issue-heading")).toBeFocused();
    analysis.release();
    await expect(page.getByTestId("record-card")).toBeVisible();
    receipts.release();
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await expect(page.locator("#selected-issue-heading")).toBeFocused();
    await expect.poll(() => page.locator("#issue-summary").evaluate(element =>
      element.getBoundingClientRect().top - document.querySelector("main > header").getBoundingClientRect().bottom,
    )).toBeGreaterThanOrEqual(0);
  } finally { analysis.release(); receipts.release(); }
});

test("late analysis preserves a focused discovery control at scroll zero", async ({ page }) => {
  await installSnapshot(page);
  await page.setViewportSize({ width: 1440, height: 1600 });
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto("/?representative=leg_valerie_p_foushee&scope=119");
    const control = page.getByRole("button", { name: "Issue summaries", exact: true });
    await expect(control).toBeVisible();
    await control.evaluate(element => element.focus({ preventScroll: true }));
    expect(await page.evaluate(() => scrollY)).toBe(0);
    const before = await control.evaluate(element => element.getBoundingClientRect().top);
    analysis.release();
    await expect(page.getByTestId("record-card")).toBeVisible();
    await expect(control).toBeFocused();
    await expect.poll(() => control.evaluate((element, top) => Math.abs(element.getBoundingClientRect().top - top), before)).toBeLessThanOrEqual(5);
  } finally { analysis.release(); }
});


test("deliberate receipt navigation still focuses after a late finding preserved reader focus", async ({ page }) => {
  await installSnapshot(page);
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto(linked(null));
    const fallback = page.getByRole("link", { name: "Browse the complete issue record", exact: true });
    await fallback.focus();
    analysis.release();
    await expect(page.getByTestId("card-finding-detail")).toBeVisible();
    await expect(fallback).toBeFocused();
    await page.getByRole("link", { name: /^See 2 House votes:/ }).focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#vote-record")).toContainText("Showing 2 of 2 matching votes");
    await expect(page.locator("#vote-record").getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
    await page.goBack();
    await expect(page.locator("#finding-detail-heading")).toBeFocused();
  } finally { analysis.release(); }
});

test("pending section restoration yields to a newly focused header control", async ({ page }) => {
  await installSnapshot(page);
  const positions = await hold(page, "positions");
  try {
    await page.goto(`${selected}#issue-summary`);
    await positions.pending;
    const voteLink = page.locator("main > header").getByRole("link", { name: "Vote record", exact: true });
    await voteLink.focus();
    positions.release();
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await expect(voteLink).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/#vote-record$/);
    await expect(page.locator("#vote-record").getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
  } finally { positions.release(); }
});

test("late presentation sizing yields after the reader chooses another control", async ({ page }) => {
  await installSnapshot(page);
  await page.setViewportSize({ width: 1440, height: 1600 });
  const analysis = await hold(page, "editorial-presentations");
  try {
    await page.goto("/?representative=leg_valerie_p_foushee&scope=119");
    // Isolate application anchoring from the browser's optional native anchoring.
    await page.evaluate(() => { document.documentElement.style.overflowAnchor = "none"; });
    const original = page.getByRole("button", { name: "Issue summaries", exact: true });
    await original.focus();
    const initialTop = await original.evaluate(element => element.getBoundingClientRect().top);
    analysis.release();
    const card = page.getByTestId("record-card");
    await expect(card).toBeVisible();
    const growCard = () => card.evaluate(element => {
      element.style.paddingBottom = `${parseFloat(getComputedStyle(element).paddingBottom) + 32}px`;
    });
    await growCard();
    await expect.poll(() => original.evaluate((element, top) => Math.abs(element.getBoundingClientRect().top - top), initialTop)).toBeLessThanOrEqual(5);
    await page.keyboard.press("Tab");
    const next = page.getByRole("button", { name: "A–Z", exact: true });
    await expect(next).toBeFocused();
    const readerTop = await next.evaluate(element => element.getBoundingClientRect().top);
    await growCard();
    // Let a queued resize callback run before proving it cannot restore the old anchor.
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await expect.poll(() => next.evaluate((element, top) => Math.abs(element.getBoundingClientRect().top - top - 32), readerTop)).toBeLessThanOrEqual(5);
    await expect(next).toBeFocused();
  } finally { analysis.release(); }
});
