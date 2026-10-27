import fs from "node:fs";
import path from "node:path";
import { gunzipSync } from "node:zlib";
import { expect, test } from "@playwright/test";
import { foushee } from "./pass-a-fixtures.mjs";

const candidate = JSON.parse(fs.readFileSync(new URL("../../docs/review_packets/record_at_a_glance_v1/candidate.json", import.meta.url)));
const snapshot = JSON.parse(gunzipSync(fs.readFileSync(new URL(`../../${candidate.source_snapshot}`, import.meta.url))));
const budd = JSON.parse(fs.readFileSync(new URL("./fixtures/budd-justice-empty-scope.json", import.meta.url)));
const selected = "/?representative=leg_valerie_p_foushee&issue=EDUCATION_WORKFORCE&scope=119";

async function installSnapshot(page) {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const member = url.pathname.split("/")[2];
    const scope = url.searchParams.get("scope") || "all";
    const resource = url.pathname.endsWith("/profile") ? "profile" : url.pathname.endsWith("/editorial-presentations") ? "editorial" : url.pathname.endsWith("/evidence") ? url.pathname.split("/")[4] : "positions";
    if (member === budd.profile.id) return route.fulfill({ json: resource === "profile" ? budd.profile : budd.scopes[scope][resource === "JUSTICE_PUBLIC_SAFETY" ? "evidence" : resource] });
    if (resource === "profile") return route.fulfill({ json: foushee });
    const supplied = snapshot[`${member}:${scope}:${resource}`];
    if (!supplied) throw Error(`Unexpected snapshot request: ${url.pathname}`);
    return route.fulfill({ status: supplied.status, json: supplied.body });
  });
}

async function expectUnoccluded(page, selector) {
  await expect(page.locator(selector)).toBeInViewport();
  await expect.poll(() => page.locator(selector).evaluate((target) => {
    const header = document.querySelector("main > header").getBoundingClientRect();
    return target.getBoundingClientRect().top - header.bottom;
  })).toBeGreaterThanOrEqual(0);
}

async function expectCoverage(page) {
  await expect(page.locator("#issue-summary")).toContainText("25 recorded actions currently visible");
  await expect(page.locator("#issue-summary")).toContainText("17 recorded actions in scope · 3 findings supported by 6 votes");
  await expect(page.locator("#issue-summary")).toContainText("8 additional recorded actions");
}

test.beforeEach(async ({ page }) => {
  await installSnapshot(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
});

for (const reducedMotion of ["reduce", "no-preference"]) test(`history restores the representative anchor after cross-issue receipt settlement (${reducedMotion})`, async ({ page }) => {
  await page.goto(selected);
  await expectCoverage(page);
  await page.locator("main > header").getByRole("link", { name: "Valerie P. Foushee", exact: true }).click();
  await expectUnoccluded(page, "#representative-name");
  await page.emulateMedia({ reducedMotion });
  await page.getByRole("button", { name: "Explore Justice & Public Safety", exact: true }).click();
  await expect(page).toHaveURL(/issue=JUSTICE_PUBLIC_SAFETY/);
  await expect(page.locator("#selected-issue-heading")).toBeFocused();
  await expect(page.locator("#vote-record")).toBeAttached();
  await page.goBack();
  await expect(page).toHaveURL(`${selected}#representative-name`);
  await expectCoverage(page);
  await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
  await expectUnoccluded(page, "#representative-name");
});

test("history waits for a delayed section target after a scope remount", async ({ page }) => {
  await page.goto(selected);
  await expectCoverage(page);
  await page.locator("main > header").getByRole("link", { name: "Issue summary", exact: true }).click();
  await expectUnoccluded(page, "#issue-summary");
  await page.getByRole("button", { name: "118th Congress", exact: true }).click();
  await expect(page.locator("#issue-summary")).toBeAttached();
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route("**/positions?scope=119", async route => { await gate; await route.fallback(); });
  try {
    await page.goBack();
    await expect(page.locator("#issue-summary")).toHaveCount(0);
    release();
    await expectCoverage(page);
    await expectUnoccluded(page, "#issue-summary");
  } finally { release(); }
});

async function holdRequest(page, pattern) {
  let release, arrived;
  const gate = new Promise(resolve => { release = resolve; });
  const pending = new Promise(resolve => { arrived = resolve; });
  await page.route(pattern, async route => { arrived(); await gate; await route.fallback(); });
  return { release, pending };
}

for (const width of [390, 1440]) for (const resource of ["profile", "positions", "editorial-presentations", "evidence"]) {
  test(`explicit section anchor survives delayed ${resource} at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    const held = await holdRequest(page, `**/${resource}${resource === "profile" ? "" : "?*"}`);
    const id = resource === "profile" ? "representative-name" : "issue-summary";
    try {
      await page.goto(`${selected}#${id}`);
      await held.pending;
      held.release();
      await expectCoverage(page);
      await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
      await expectUnoccluded(page, `#${id}`);
      await expect(page.locator(id === "representative-name" ? "#representative-name" : "#selected-issue-heading")).toBeFocused();
      if (resource === "positions") {
        const screenshot = testInfo.outputPath(`restored-section-${width}.png`);
        await page.screenshot({ path: screenshot });
        await testInfo.attach(`restored-section-${width}`, { path: screenshot, contentType: "image/png" });
      }
    } finally { held.release(); }
  });
}

for (const movement of ["keyboard", "wheel", "new section"]) test(`delayed restoration yields to ${movement}`, async ({ page }) => {
  const held = await holdRequest(page, "**/positions?scope=119");
  try {
    await page.goto(`${selected}#issue-summary`);
    await held.pending;
    if (movement === "keyboard") {
      await page.getByRole("button", { name: "119th Congress", exact: true }).focus();
      await page.keyboard.press("Tab");
    } else if (movement === "wheel") await page.mouse.wheel(0, 200);
    else {
      await page.locator("main > header").getByRole("link", { name: "Valerie P. Foushee", exact: true }).click();
      await expectUnoccluded(page, "#representative-name");
    }
    const focus = await page.evaluate(() => document.activeElement.id);
    held.release();
    await expectCoverage(page);
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    expect(await page.evaluate(() => document.activeElement.id)).toBe(focus);
    if (movement === "new section") await expectUnoccluded(page, "#representative-name");
    else await expect(page.locator("#selected-issue-heading")).not.toBeFocused();
  } finally { held.release(); }
});

test("clicking the current section hash reasserts intent while its target is loading", async ({ page }) => {
  const held = await holdRequest(page, "**/positions?scope=119");
  try {
    await page.goto(`${selected}#issue-summary`);
    await held.pending;
    await expect(page.locator("#issue-summary")).toHaveCount(0);
    await page.locator("main > header").getByRole("link", { name: "Issue summary", exact: true }).click();
    held.release();
    await expectCoverage(page);
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
    await expectUnoccluded(page, "#issue-summary");
    await expect(page.locator("#selected-issue-heading")).toBeFocused();
  } finally { held.release(); }
});

test("rapid Back Forward across members discards an obsolete pending restoration", async ({ page }) => {
  await page.route("**/legislators/search?*", route => route.fulfill({ json: { results: [budd.profile] } }));
  await page.goto(`${selected}#representative-name`);
  await expectCoverage(page);
  await expectUnoccluded(page, "#representative-name");
  await page.getByRole("button", { name: "Switch representative", exact: true }).click();
  await page.getByLabel("Search by name", { exact: true }).fill("Budd");
  await page.getByRole("button", { name: "Search names", exact: true }).click();
  await page.getByRole("button", { name: /^Select Ted Budd,/ }).click();
  await expect(page.locator("#representative-name")).toHaveText("Ted Budd");
  const held = await holdRequest(page, "**/legislators/leg_valerie_p_foushee/profile");
  try {
    await page.goBack();
    await held.pending;
    await expect(page.locator("#representative-name")).toHaveCount(0);
    await page.goForward();
    await expect(page.locator("#representative-name")).toHaveText("Ted Budd");
    held.release();
    await expectUnoccluded(page, "#representative-name");
    await page.goBack();
    await expectCoverage(page);
    await expect(page.locator("#representative-name")).toHaveText("Valerie P. Foushee");
    await expectUnoccluded(page, "#representative-name");
    await expect(page.locator("#representative-name")).toBeFocused();
  } finally { held.release(); }
});

test("no-hash Back Forward retains native scroll policy and queues no section restoration", async ({ page }) => {
  await page.addInitScript(() => {
    window.sectionScrollCalls = [];
    const original = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function(options) {
      window.sectionScrollCalls.push(this.id);
      return original.call(this, options);
    };
  });
  await page.goto(selected);
  await expectCoverage(page);
  await expect(page.locator("#selected-issue-heading")).toBeFocused();
  await page.getByRole("button", { name: "Explore Justice & Public Safety", exact: true }).click();
  await expect(page.locator("#selected-issue-heading")).toBeFocused();
  await expect(page.locator("#vote-record")).toBeAttached();
  await page.evaluate(() => { window.sectionScrollCalls = []; });
  await page.goBack();
  await expectCoverage(page);
  await page.goForward();
  await expect(page.locator("#vote-record")).toBeAttached();
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  expect(await page.evaluate(() => ({ hash: location.hash, policy: history.scrollRestoration, calls: window.sectionScrollCalls })))
    .toEqual({ hash: "", policy: "auto", calls: [] });
});

for (const width of [1440, 1024, 390, 320]) test(`sticky anchors and readable sources preserve Education coverage at ${width}px`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: width < 500 ? 844 : 1000 });
  await page.goto(selected);
  await expectCoverage(page);
  await expect(page.locator("#selected-issue-heading")).toBeFocused();
  await expectUnoccluded(page, "#issue-summary");
  const header = page.locator("main > header");
  for (const [name, id] of [["Vote record", "vote-record"], ["Valerie P. Foushee", "representative-name"], ["Issues", "issues"], ["Issue summary", "issue-summary"]]) {
    await header.getByRole("link", { name, exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(new RegExp(`#${id}$`));
    await expectUnoccluded(page, `#${id}`);
  }
  await page.getByRole("button", { name: /View supporting votes for Opposed two China-linked education funding restrictions/ }).click();
  await expectUnoccluded(page, "#vote-record");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  const roll = page.locator('[data-canonical-action-id="house:119:1:313"]');
  const toggle = roll.locator(":scope > button");
  if (await toggle.getAttribute("aria-expanded") !== "true") await toggle.click();
  await expect(roll.getByRole("link", { name: "Official vote", exact: true })).toHaveAttribute("href", "https://clerk.house.gov/Votes/2025313");
  await expect(roll.getByRole("link", { name: "Original vote source (XML)" })).toHaveAttribute("href", "https://clerk.house.gov/evs/2025/roll313.xml");
  await expectCoverage(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await roll.scrollIntoViewIfNeeded();
  const screenshot = await page.screenshot();
  await testInfo.attach(`education-receipt-${width}`, { body: screenshot, contentType: "image/png" });
  if (process.env.FRONTEND_PASS_SCREENSHOT_DIR) {
    fs.mkdirSync(process.env.FRONTEND_PASS_SCREENSHOT_DIR, { recursive: true });
    fs.writeFileSync(path.join(process.env.FRONTEND_PASS_SCREENSHOT_DIR, `education-receipt-${width}.png`), screenshot);
    await roll.getByRole("link", { name: "Official vote", exact: true }).scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(process.env.FRONTEND_PASS_SCREENSHOT_DIR, `official-sources-${width}.png`) });
    await header.getByRole("link", { name: "Valerie P. Foushee" }).click();
    await page.screenshot({ path: path.join(process.env.FRONTEND_PASS_SCREENSHOT_DIR, `representative-anchor-${width}.png`) });
  }
});

test("header offset adapts to resizing and 200 percent zoom, including direct receipt hashes", async ({ page }) => {
  await page.goto(selected);
  await expectCoverage(page);
  for (const [width, zoom] of [[1440, 1], [390, 1], [1440, 2]]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.evaluate((value) => { document.documentElement.style.zoom = String(value); }, zoom);
    for (const [name, selector] of [["Valerie P. Foushee", "#representative-name"], ["Issue summary", "#issue-summary"], ["Vote record", "#vote-record"]]) {
      await page.locator("main > header").getByRole("link", { name, exact: true }).click();
      await expectUnoccluded(page, selector);
    }
  }
  const id = await page.locator("[data-canonical-action-id]").first().getAttribute("id");
  await page.goto(`${selected}#${id}`);
  await expect(page.locator(`#${id} > button`)).toHaveAttribute("aria-expanded", "true");
  await expectUnoccluded(page, `#${id}`);
});

test("unverified Senate mapping retains its exact supplied source without a guessed page", async ({ page }) => {
  await page.goto("/?representative=leg_ted_budd&issue=JUSTICE_PUBLIC_SAFETY&scope=119");
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  for (const row of await page.locator("[data-canonical-action-id]").all()) {
    await row.locator(":scope > button").click();
    const id = await row.getAttribute("data-canonical-action-id");
    const supplied = budd.scopes["119"].evidence.evidence.find(item => item.canonical_action_id === id);
    await expect(row.getByRole("link", { name: "Official vote", exact: true })).toHaveAttribute("href", supplied.source_url);
    await expect(row.getByRole("link", { name: "Original vote source (XML)" })).toHaveCount(0);
  }
});

test("delayed loading completes without losing the selected route or coverage", async ({ page }) => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route("**/positions?scope=119", async route => { await gate; await route.fallback(); });
  try {
    await page.goto(selected);
    await expect(page.getByText("Loading issue records…", { exact: true })).toBeVisible();
    await expect(page.locator("#issue-summary")).toHaveCount(0);
    await page.getByRole("button", { name: "119th Congress", exact: true }).focus();
    release();
    await expectCoverage(page);
    await expect(page.getByRole("button", { name: "119th Congress", exact: true })).toBeFocused();
    await expect(page).toHaveURL(selected);
  } finally { release(); }
});

for (const resource of ["profile", "positions", "editorial-presentations"]) test(`${resource} failure exposes the current recovery path without changing coverage`, async ({ page }) => {
  let fail = true;
  await page.route(`**/${resource}${resource === "profile" ? "" : "?*"}`, route => fail ? route.fulfill({ status: 503, body: "unavailable" }) : route.fallback());
  await page.goto(selected);
  if (resource === "profile") {
    await expect(page.getByRole("alert").filter({ hasText: "Search again to continue" })).toBeVisible();
    await expect(page.getByTestId("representative-finder")).toBeVisible();
  } else if (resource === "positions") {
    await expect(page.getByRole("alert").filter({ hasText: "issue records are unavailable" })).toBeVisible();
  } else {
    await expect(page.getByText("Issue summaries could not be verified. Recorded vote evidence remains available.")).toBeVisible();
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
  }
  fail = false;
  if (resource === "positions") {
    await page.getByRole("button", { name: "118th Congress", exact: true }).click();
    await page.getByRole("button", { name: "119th Congress", exact: true }).click();
  } else await page.reload();
  await expectCoverage(page);
  await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
});
