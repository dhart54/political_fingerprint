import { expect, test } from "@playwright/test";

import { classifyZipLookupState } from "../lib/zipLookupState.mjs";
import { bean, foushee, installPassARoutes } from "./pass-a-fixtures.mjs";

const ross = {
  ...foushee,
  id: "leg_deborah_k_ross",
  bioguide_id: "R000305",
  name_display: "Deborah K. Ross",
  district: "02",
};
const senator = {
  id: "leg_ted_budd", name_display: "Ted Budd", chamber: "senate",
  state: "NC", district: "Statewide", party: "R",
};
const ready = {
  zip: "27701", state: "NC", district: "04", data_source: "database",
  lookup_metadata: { source_currentness: "current" },
  district_mappings: [{ zip: "27701", state: "NC", district: "04" }],
  house_rep: foushee, senators: [senator],
};
const cases = [
  ["ready", ready, "single_district_ready"],
  ["ambiguous", { ...ready, district_mappings: [
    ...ready.district_mappings, { zip: "27701", state: "NC", district: "02" },
  ] }, "ambiguous_zip"],
  ["multi-state", { ...ready, district_mappings: [
    ...ready.district_mappings, { zip: "27701", state: "VA", district: "01" },
  ] }, "multi_state_zip"],
  ["fixture", { ...ready, data_source: "fixtures" }, "fixture_sample_only"],
  ["stale", { ...ready, lookup_metadata: { source_currentness: "stale_or_unknown" } }, "stale_or_unknown_source"],
  ["unknown", { ...ready, lookup_metadata: {} }, "stale_or_unknown_source"],
  ["member-uncertain", { ...ready, lookup_metadata: {
    ...ready.lookup_metadata, member_metadata_uncertain: true,
  } }, "member_metadata_uncertain"],
  ["unsupported", { status: "unsupported_zip", zip: "27701" }, "unsupported_zip"],
  ["ambiguous sample", { ...ready, data_source: "fixtures", district_mappings: [
    ...ready.district_mappings, { zip: "27701", state: "NC", district: "02" },
  ] }, "ambiguous_zip"],
];

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page);
  await page.route(`**/legislators/${ross.id}/profile*`, (route) => route.fulfill({ json: ross }));
});

const finder = (page) => page.getByTestId("representative-finder");
const handoff = (page) => finder(page).getByRole("group", { name: "Verify representation on official sites", exact: true });
const officialLinks = [
  ["Open official House finder", "https://www.house.gov/representatives/find-your-representative"],
  ["Open official Senate directory", "https://www.senate.gov/senators/index.htm"],
];
const choice = (page, member) => finder(page).getByRole("button", { name: `Select ${member.name_display}`, exact: false });

async function submit(page, mode, query) {
  await finder(page).getByLabel(mode === "zip" ? "Search by ZIP" : "Search by name", { exact: true }).fill(query);
  await finder(page).getByRole("button", { name: mode === "zip" ? "Find by ZIP" : "Search names", exact: true }).click();
}

async function nameResult(page, member = ross) {
  await page.route("**/legislators/search?*", (route) => route.fulfill({ json: { results: [member] } }));
}

for (const [label, payload, state] of cases) {
  test(`${label} ZIP uses established qualifications and explicit record inspection on /`, async ({ page }) => {
    const classification = classifyZipLookupState(payload);
    expect(classification.state).toBe(state);
    await page.route("**/lookup/zip/27701", (route) => route.fulfill({ json: payload }));
    await page.goto("/");
    await submit(page, "zip", "27701");
    const status = finder(page).getByRole("status");
    await expect(status).toHaveAttribute("data-lookup-state", state);
    await expect(status).toContainText(classification.title);
    await expect(status).toContainText(classification.message);
    for (const caveat of classification.caveats) await expect(status).toContainText(caveat);
    await expect(status).not.toContainText("federal representatives for");
    await expect(status.getByRole("link")).toHaveCount(0);
    await expect(handoff(page)).toContainText("Enter any location details there yourself");
    await expect(handoff(page).getByRole("link")).toHaveCount(2);
    for (const [label, url] of officialLinks) {
      const link = handoff(page).getByRole("link", { name: label, exact: true });
      await expect(link).toHaveAttribute("href", url);
      await expect(link).toHaveAttribute("target", "_blank");
      await expect(link).toHaveAttribute("rel", "noopener noreferrer");
      await expect(link).toHaveAttribute("referrerpolicy", "no-referrer");
    }
    await expect(page).toHaveURL(/\/$/);
    await expect(page.locator("#representative-name")).toHaveCount(0);
    if (payload.house_rep) {
      await expect(choice(page, foushee)).toContainText("Inspect loaded record");
      await expect(choice(page, foushee)).toHaveAccessibleDescription(/not a confirmed address match/);
      await choice(page, foushee).click();
      await expect(page).toHaveURL(/representative=leg_valerie_p_foushee/);
      await expect(page.locator("#representative-name")).toHaveText(foushee.name_display);
    } else {
      await expect(finder(page).getByRole("list")).toHaveCount(0);
    }
  });
}

test("404 unsupported lookup keeps name fallback usable; server errors remain errors", async ({ page }) => {
  await page.route("**/lookup/zip/27701", (route) => route.fulfill({ status: 404, json: { detail: "ZIP code not found" } }));
  await page.route("**/lookup/zip/99999", (route) => route.fulfill({ status: 503, json: {} }));
  await nameResult(page);
  await page.goto("/");
  await submit(page, "zip", "27701");
  await expect(finder(page).getByRole("status")).toHaveAttribute("data-lookup-state", "unsupported_zip");
  await expect(handoff(page)).toBeVisible();
  await finder(page).getByRole("button", { name: "Search by representative name", exact: true }).click();
  await expect(page.getByLabel("Search by name", { exact: true })).toBeFocused();
  await submit(page, "zip", "99999");
  await expect(finder(page).getByRole("alert")).toContainText("Try a name search");
  await expect(handoff(page)).toHaveCount(0);
  await submit(page, "name", "Deborah Ross");
  await expect(choice(page, ross)).toBeVisible();
  await expect(handoff(page)).toHaveCount(0);
  await choice(page, ross).click();
  await expect(page.locator("#representative-name")).toHaveText(ross.name_display);
});

test("state-level senator remains explicitly inspectable with ZIP qualification", async ({ page }) => {
  await page.route("**/lookup/zip/27701", (route) => route.fulfill({ json: ready }));
  await page.route(`**/legislators/${senator.id}/profile*`, (route) => route.fulfill({ json: senator }));
  await page.goto("/");
  await submit(page, "zip", "27701");
  await expect(finder(page).getByRole("status")).toContainText("Senators represent the whole state");
  await expect(choice(page, senator)).toHaveAccessibleDescription(/not a confirmed address match/);
  await expect(choice(page, senator)).toContainText("U.S. Senate · NC, statewide");
  await choice(page, senator).click();
  await expect(page).toHaveURL(/representative=leg_ted_budd/);
  await expect(page.locator("#representative-name")).toHaveText(senator.name_display);
});

// Existing stale-callback challenges deliberately let transport ignore abort.
// Separate honorAbort tests exercise real browser fetch cancellation as well.
async function holdLookup(page, mode, { honorAbort = false } = {}) {
  await page.addInitScript(({ honorAbort }) => {
    window.__finderCompletions = [];
    window.__finderSignals = [];
    window.__finderErrors = [];
    const original = window.fetch;
    window.fetch = async (...args) => {
      const url = String(args[0]);
      if (/\/lookup\/zip\/|\/legislators\/search/.test(url)) {
        window.__finderSignals.push({ url, signal: args[1]?.signal });
        if (!honorAbort) args[1] = { ...args[1], signal: undefined };
      }
      try {
        const response = await original(...args);
        if (!response.ok) window.__finderCompletions.push(url);
        const json = response.json.bind(response);
        response.json = async () => {
          try { return await json(); }
          finally { window.__finderCompletions.push(url); }
        };
        return response;
      } catch (error) {
        window.__finderErrors.push({ url, name: error.name });
        window.__finderCompletions.push(url);
        throw error;
      }
    };
  }, { honorAbort });
  let received;
  const requests = [];
  const pending = new Promise((resolve) => { received = resolve; });
  await page.route(mode === "zip" ? "**/lookup/zip/27701" : "**/legislators/search?q=Foushee", (route) => {
    requests.push(route);
    received(route);
  });
  return {
    pending,
    requests,
    async aborted() {
      const url = (await pending).request().url();
      await expect.poll(() => page.evaluate((url) => window.__finderSignals.some((entry) => entry.url === url && entry.signal?.aborted), url)).toBe(true);
    },
    async finish({ reject = false, status = 200, index = 0, json = mode === "zip" ? ready : { results: [foushee] } } = {}) {
      await pending;
      const route = requests[index];
      const url = route.request().url();
      if (reject) await route.abort("failed");
      else await route.fulfill({ status, json });
      await page.waitForFunction((value) => window.__finderCompletions.includes(value), url);
      await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    },
  };
}

const slowGuidance = "This search is taking longer than expected. You can keep waiting, cancel it, or try a different search.";
const searchInput = (page, mode) => finder(page).getByLabel(mode === "zip" ? "Search by ZIP" : "Search by name", { exact: true });
const queryFor = (mode) => mode === "zip" ? "27701" : "Foushee";

async function focusCancelWithKeyboard(page) {
  await searchInput(page, "name").focus();
  await page.keyboard.press("Tab");
  await expect(finder(page).getByRole("button", { name: "Search names", exact: true })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(finder(page).getByRole("button", { name: "Cancel search", exact: true })).toBeFocused();
}

const settlementCases = [
  ["zip", "success", {}], ["name", "success", {}],
  ["zip", "404", { status: 404 }], ["name", "empty", { json: { results: [] } }],
  ["zip", "network", { reject: true }], ["name", "network", { reject: true }],
  ["zip", "503", { status: 503 }], ["name", "503", { status: 503 }],
];

for (const [mode, outcome, options] of settlementCases) {
  for (const moved of [false, true]) {
    test(`settled ${mode} ${outcome} ${moved ? "preserves moved focus" : "restores owned Cancel focus"}`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width: mode === "zip" ? 390 : 1440, height: 900 });
      const held = await holdLookup(page, mode, { honorAbort: true });
      await page.goto("/");
      const url = page.url(), historyLength = await page.evaluate(() => history.length);
      await submit(page, mode, queryFor(mode)); await held.pending;
      await focusCancelWithKeyboard(page);
      // Move away using Shift+Tab to a stable submit control.
      const otherButton = finder(page).getByRole("button", { name: "Search names", exact: true });
      if (moved) {
        await page.keyboard.press("Shift+Tab");
        await expect(otherButton).toBeFocused();
      }
      await held.finish(options);
      await expect(finder(page).getByRole("button", { name: "Cancel search", exact: true })).toHaveCount(0);
      await expect(moved ? otherButton : searchInput(page, mode)).toBeFocused();
      if (outcome === "network" || outcome === "503") {
        await expect(finder(page).getByRole("alert")).toContainText("unavailable right now");
        await expect(handoff(page)).toHaveCount(0);
      } else if (outcome === "404") {
        await expect(finder(page).getByRole("status")).toHaveAttribute("data-lookup-state", "unsupported_zip");
        await expect(handoff(page)).toBeVisible();
        await expect(finder(page).getByRole("list")).toHaveCount(0);
      } else if (outcome === "empty") {
        await expect(finder(page).getByRole("status")).toContainText("No representatives matched");
        await expect(finder(page).getByRole("list")).toHaveCount(0);
      } else await expect(choice(page, foushee)).toBeVisible();
      await expect(searchInput(page, mode)).toHaveValue(queryFor(mode));
      expect(page.url()).toBe(url);
      expect(await page.evaluate(() => history.length)).toBe(historyLength);
      expect(held.requests).toHaveLength(1);
      if (!moved && (outcome === "success" || outcome === "network")) {
        await finder(page).screenshot({ path: testInfo.outputPath(`settled-${mode}-${outcome}-focus.png`) });
      }
    });
  }
}

for (const [mode, reject] of [["zip", false], ["zip", true], ["name", false], ["name", true]]) {
  test(`superseded ${mode} late ${reject ? "error" : "success"} cannot move newer Cancel focus`, async ({ page }) => {
    const held = await holdLookup(page, mode);
    const newMode = mode === "zip" ? "name" : "zip";
    let newRoute;
    await page.route(newMode === "zip" ? "**/lookup/zip/32003" : "**/legislators/search?q=Bean", (route) => { newRoute = route; });
    await page.goto("/");
    await submit(page, mode, queryFor(mode)); await held.pending;
    await focusCancelWithKeyboard(page);
    await submit(page, newMode, newMode === "zip" ? "32003" : "Bean");
    await expect.poll(() => Boolean(newRoute)).toBe(true);
    await held.aborted();
    await focusCancelWithKeyboard(page);
    await held.finish({ reject });
    await expect(finder(page).getByRole("button", { name: "Cancel search", exact: true })).toBeFocused();
    await newRoute.fulfill({ json: newMode === "zip" ? {
      ...ready, zip: "32003", state: "FL", district_mappings: [{ state: "FL", district: "04" }], house_rep: bean, senators: [],
    } : { results: [bean] } });
    await expect(searchInput(page, newMode)).toBeFocused();
    await expect(choice(page, bean)).toBeVisible();
    expect(held.requests).toHaveLength(1);
    expect(await page.evaluate(() => window.__finderSignals.length)).toBe(2);
  });
}

for (const mode of ["zip", "name"]) {
  for (const width of [320, 390, 768, 1440]) {
    test(`held ${mode} at ${width} offers guidance with one GET and eventually succeeds`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width, height: 900 });
      const held = await holdLookup(page, mode, { honorAbort: true });
      await page.goto("/");
      await page.clock.install();
      const url = page.url(), historyLength = await page.evaluate(() => history.length);
      await submit(page, mode, queryFor(mode));
      await held.pending;
      const status = finder(page).getByRole("status");
      await expect(status).toHaveAttribute("aria-live", "polite");
      await expect(status).toHaveAttribute("aria-atomic", "true");
      await expect(status).not.toContainText(slowGuidance);
      await page.clock.runFor(4_000);
      if (mode === "name") await searchInput(page, mode).fill("  Foushee  ");
      // Same-turn submissions challenge the synchronous guard before rerender.
      await searchInput(page, mode).evaluate((input) => {
        input.form.requestSubmit(); input.form.requestSubmit(); input.form.requestSubmit();
      });
      await page.clock.runFor(4_001);
      await expect(status).toContainText(slowGuidance);
      await page.clock.fastForward(60_000);
      await expect(status).toContainText(slowGuidance);
      expect(held.requests).toHaveLength(1);
      expect(held.requests[0].request().method()).toBe("GET");
      const cancel = finder(page).getByRole("button", { name: "Cancel search", exact: true });
      await focusCancelWithKeyboard(page);
      expect(await cancel.evaluate((node) => getComputedStyle(node).outlineStyle)).not.toBe("none");
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await finder(page).screenshot({ path: testInfo.outputPath(`slow-${mode}-${width}.png`) });
      await held.finish();
      await expect(choice(page, foushee)).toBeVisible();
      await expect(status).not.toContainText(slowGuidance);
      await expect(cancel).toHaveCount(0);
      await testInfo.attach("finder-completion-focus", {
        body: JSON.stringify(await page.evaluate(() => ({ tag: document.activeElement.tagName, id: document.activeElement.id }))),
        contentType: "application/json",
      });
      await expect(searchInput(page, mode)).toBeFocused();
      await page.clock.fastForward(60_000);
      await expect(choice(page, foushee)).toBeVisible();
      expect(page.url()).toBe(url);
      expect(await page.evaluate(() => history.length)).toBe(historyLength);
      expect(held.requests).toHaveLength(1);
      await finder(page).screenshot({ path: testInfo.outputPath(`completed-${mode}-${width}.png`) });
    });
  }

  test(`Cancel search aborts real ${mode} fetch, preserves inputs and permits explicit resubmission`, async ({ page }, testInfo) => {
    const held = await holdLookup(page, mode, { honorAbort: true });
    await page.goto("/");
    await page.clock.install();
    await searchInput(page, mode === "zip" ? "name" : "zip").fill(mode === "zip" ? "Ross" : "32003");
    const url = page.url(), historyLength = await page.evaluate(() => history.length);
    await submit(page, mode, queryFor(mode));
    await held.pending;
    await page.clock.runFor(4_000);
    const cancel = finder(page).getByRole("button", { name: "Cancel search", exact: true });
    await cancel.focus(); await cancel.press("Enter");
    await held.aborted();
    await expect.poll(() => page.evaluate(() => window.__finderErrors.map((error) => error.name))).toContain("AbortError");
    await expect(searchInput(page, mode)).toBeFocused();
    await expect(searchInput(page, mode)).toHaveValue(queryFor(mode));
    await expect(searchInput(page, mode === "zip" ? "name" : "zip")).toHaveValue(mode === "zip" ? "Ross" : "32003");
    await page.clock.fastForward(60_000);
    await expect(finder(page).getByRole("status")).toContainText("Search cancelled");
    await expect(finder(page).getByRole("alert")).toHaveCount(0);
    await expect(cancel).toHaveCount(0);
    expect(held.requests).toHaveLength(1);
    await finder(page).screenshot({ path: testInfo.outputPath(`cancelled-${mode}.png`) });
    await searchInput(page, mode).press("Enter");
    await expect.poll(() => held.requests.length).toBe(2);
    await page.clock.runFor(4_000);
    await expect(finder(page).getByRole("status")).not.toContainText(slowGuidance);
    await held.finish({ index: 1 });
    await expect(choice(page, foushee)).toBeVisible();
    await held.finish(); // A response released after abort is still inert.
    await page.clock.fastForward(60_000);
    await expect(choice(page, foushee)).toBeVisible();
    expect(held.requests).toHaveLength(2);
    expect(page.url()).toBe(url);
    expect(await page.evaluate(() => history.length)).toBe(historyLength);
  });

  for (const reject of [false, true]) {
    test(`cancelled ${mode} late ${reject ? "error" : "success"} cannot settle an identical new search`, async ({ page }) => {
      const held = await holdLookup(page, mode);
      await page.goto("/");
      await page.clock.install();
      await submit(page, mode, queryFor(mode));
      await held.pending;
      await page.clock.runFor(4_000);
      await finder(page).getByRole("button", { name: "Cancel search" }).click();
      await held.aborted();
      await searchInput(page, mode).press("Enter");
      await expect.poll(() => held.requests.length).toBe(2);
      await held.finish({ reject });
      // Obsolete finally/timer callbacks must not clear the new pending guard.
      await page.clock.runFor(4_001);
      await expect(finder(page).getByRole("status")).not.toContainText(slowGuidance);
      await searchInput(page, mode).press("Enter");
      await page.clock.runFor(4_000);
      await expect(finder(page).getByRole("status")).toContainText(slowGuidance);
      expect(held.requests).toHaveLength(2);
      await expect(finder(page).getByRole("list")).toHaveCount(0);
      await expect(finder(page).getByRole("alert")).toHaveCount(0);
      await held.finish({ index: 1 });
      await expect(choice(page, foushee)).toBeVisible();
    });
  }
}

test("already queued slow callbacks cannot overwrite a cancelled or newer ready search", async ({ page }) => {
  await page.addInitScript(() => {
    window.__slowCallbacks = [];
    const original = window.setTimeout;
    window.setTimeout = (callback, delay, ...args) => {
      if (delay === 8_000) window.__slowCallbacks.push(callback);
      return original(callback, delay, ...args);
    };
  });
  const held = await holdLookup(page, "zip");
  let newRoute;
  await page.route("**/legislators/search?q=Bean", (route) => { newRoute = route; });
  await page.goto("/");
  await submit(page, "zip", "27701"); await held.pending;
  await finder(page).getByRole("button", { name: "Cancel search" }).click();
  await page.evaluate(() => window.__slowCallbacks.forEach((callback) => callback()));
  await expect(finder(page).getByRole("status")).toContainText("Search cancelled");
  await expect(finder(page).getByRole("status")).not.toContainText(slowGuidance);
  await submit(page, "name", "Bean");
  await expect.poll(() => Boolean(newRoute)).toBe(true);
  await page.evaluate(() => window.__slowCallbacks[0]());
  await expect(finder(page).getByRole("status")).not.toContainText(slowGuidance);
  await expect(finder(page).getByRole("status")).toContainText("Searching representative records");
  await newRoute.fulfill({ json: { results: [bean] } });
  await expect(choice(page, bean)).toBeVisible();
  await held.finish();
  await page.evaluate(() => window.__slowCallbacks.forEach((callback) => callback()));
  await expect(choice(page, bean)).toBeVisible();
  await expect(finder(page).getByRole("status")).not.toContainText(slowGuidance);
});

for (const exit of ["Close", "Back"]) {
  test(`${exit} aborts real pending switch transport and isolates history/remount`, async ({ page }) => {
    const held = await holdLookup(page, "zip", { honorAbort: true });
    await page.goto("/");
    await submit(page, "name", "Foushee");
    await choice(page, foushee).click();
    await page.getByRole("button", { name: "Switch representative" }).click();
    await submit(page, "zip", "27701"); await held.pending;
    if (exit === "Close") {
      await finder(page).getByRole("button", { name: "Close", exact: true }).click();
      await expect(page.getByRole("button", { name: "Switch representative" })).toBeFocused();
      await page.getByRole("button", { name: "Switch representative" }).click();
    } else await page.goBack();
    await held.aborted();
    await expect.poll(() => page.evaluate(() => window.__finderErrors.map((error) => error.name))).toContain("AbortError");
    await held.finish();
    await expect(finder(page).getByRole("status")).toHaveText("Search by ZIP code or representative name.");
    await expect(finder(page).getByRole("list")).toHaveCount(0);
    if (exit === "Back") await page.goForward();
    await expect(page.locator("#representative-name")).toHaveText(foushee.name_display);
  });
}

test("empty name results and transport errors keep their distinct established messages", async ({ page }) => {
  await page.route("**/legislators/search?*", (route) => new URL(route.request().url()).searchParams.get("q") === "Nobody"
    ? route.fulfill({ json: { results: [] } }) : route.abort("failed"));
  await page.goto("/");
  await submit(page, "name", "Nobody");
  await expect(finder(page).getByRole("status")).toContainText("No representatives matched “Nobody.”");
  await expect(finder(page).getByRole("list")).toHaveCount(0);
  await submit(page, "name", "Ross");
  await expect(finder(page).getByRole("alert")).toContainText("Name search is unavailable right now");
  await expect(handoff(page)).toHaveCount(0);
});

for (const [oldMode, newMode] of [["zip", "name"], ["name", "zip"], ["zip", "zip"], ["name", "name"]]) {
  test(`latest ${newMode} submission wins over late ${oldMode} success`, async ({ page }) => {
    await nameResult(page);
    await page.route("**/lookup/zip/32003", (route) => route.fulfill({ json: {
      ...ready, zip: "32003", state: "FL", district_mappings: [{ state: "FL", district: "04" }], house_rep: bean, senators: [],
    } }));
    const held = await holdLookup(page, oldMode);
    await page.goto("/");
    await submit(page, oldMode, oldMode === "zip" ? "27701" : "Foushee");
    await held.pending;
    await expect(finder(page).getByRole("status")).toContainText(oldMode === "zip" ? "Looking up representatives" : "Searching representative records");
    await expect(handoff(page)).toHaveCount(0);
    await submit(page, newMode, newMode === "zip" ? "32003" : "Ross");
    await held.aborted();
    const member = newMode === "zip" ? bean : ross;
    await expect(choice(page, member)).toBeVisible();
    await held.finish();
    await expect(choice(page, member)).toBeVisible();
    await expect(choice(page, foushee)).toHaveCount(0);
    await expect(handoff(page)).toHaveCount(newMode === "zip" ? 1 : 0);
    await expect(page).toHaveURL(/\/$/);
  });
}

for (const oldMode of ["zip", "name"]) {
  for (const rejection of ["network", "HTTP"]) {
    test(`stale ${oldMode} ${rejection} rejection cannot replace a newer success`, async ({ page }) => {
      await nameResult(page, bean);
      const held = await holdLookup(page, oldMode);
      await page.goto("/");
      await submit(page, oldMode, oldMode === "zip" ? "27701" : "Foushee");
      await held.pending;
      await submit(page, "name", "Bean");
      await held.aborted();
      await expect(choice(page, bean)).toBeVisible();
      await held.finish({ reject: rejection === "network", status: 503 });
      await expect(choice(page, bean)).toBeVisible();
      await expect(finder(page).getByRole("alert")).toHaveCount(0);
    });
  }
}

for (const mode of ["zip", "name"]) {
  test(`invalid ${mode} submission supersedes pending requests and announces validation`, async ({ page }) => {
    const held = await holdLookup(page, "zip");
    await page.goto("/");
    await submit(page, "zip", "27701");
    await held.pending;
    await submit(page, mode, mode === "zip" ? "27" : "R");
    await held.aborted();
    await expect(finder(page).getByRole("alert")).toContainText(mode === "zip" ? "5-digit" : "at least two letters");
    await held.finish();
    await expect(finder(page).getByRole("alert")).toBeVisible();
    await expect(finder(page).getByRole("list")).toHaveCount(0);
    await expect(handoff(page)).toHaveCount(0);
  });
}

for (const reject of [false, true]) {
  test(`close and reopen isolates pending ${reject ? "error" : "success"} from a fresh finder`, async ({ page }) => {
    await nameResult(page, bean);
    const held = await holdLookup(page, "zip");
    await page.goto(`/?representative=${foushee.id}`);
    await page.getByRole("button", { name: "Switch representative" }).click();
    await submit(page, "zip", "27701");
    await held.pending;
    await finder(page).getByRole("button", { name: "Close", exact: true }).click();
    await held.aborted();
    await expect(finder(page)).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Switch representative" })).toBeFocused();
    await page.getByRole("button", { name: "Switch representative" }).click();
    await submit(page, "name", "Bean");
    await expect(choice(page, bean)).toBeVisible();
    await held.finish({ reject });
    await expect(choice(page, bean)).toBeVisible();
    await expect(page.locator("#representative-name")).toHaveText(foushee.name_display);
    await expect(page).toHaveURL(new RegExp(`representative=${foushee.id}`));
  });
}

test("explicit selection while an older lookup is pending survives reopen and Back/Forward", async ({ page }) => {
  await nameResult(page, bean);
  const held = await holdLookup(page, "zip");
  await page.goto("/");
  await submit(page, "zip", "27701");
  await held.pending;
  await submit(page, "name", "Bean");
  await choice(page, bean).click();
  await held.aborted();
  await expect(page.locator("#representative-name")).toHaveText(bean.name_display);
  await expect(page.locator("#representative-name")).toBeFocused();
  await page.getByRole("button", { name: "Switch representative" }).click();
  await held.finish();
  await expect(finder(page).getByRole("status")).toHaveText("Search by ZIP code or representative name.");
  await expect(finder(page).getByRole("list")).toHaveCount(0);
  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  await expect(finder(page)).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(/representative=leg_aaron_bean/);
  await expect(page.locator("#representative-name")).toHaveText(bean.name_display);
  await expect(finder(page)).toHaveCount(0);
});

test("Back unmounts a pending switch lookup; Forward restores the selected record", async ({ page }) => {
  const held = await holdLookup(page, "zip");
  await page.goto("/");
  await submit(page, "name", "Foushee");
  await choice(page, foushee).click();
  await page.getByRole("button", { name: "Switch representative" }).click();
  await submit(page, "zip", "27701");
  await held.pending;
  await page.goBack();
  await expect(finder(page).getByRole("status")).toHaveText("Search by ZIP code or representative name.");
  await held.aborted();
  await held.finish();
  await expect(finder(page).getByRole("list")).toHaveCount(0);
  await page.goForward();
  await expect(page.locator("#representative-name")).toHaveText(foushee.name_display);
});

for (const width of [320, 390, 768, 1440]) {
  test(`keyboard lookup, status and qualified selection fit width ${width}`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    const payload = cases[1][1];
    await page.route("**/lookup/zip/27701", (route) => route.fulfill({ json: payload }));
    await page.goto("/");
    const input = finder(page).getByLabel("Search by ZIP", { exact: true });
    await input.fill("27701");
    await input.press("Enter");
    const status = finder(page).getByRole("status");
    await expect(status).toHaveAttribute("aria-live", "polite");
    await expect(status).toHaveAttribute("aria-atomic", "true");
    await expect(status).toContainText("multiple districts");
    const fallback = finder(page).getByRole("button", { name: "Search by representative name", exact: true });
    await input.press("Tab");
    await expect(finder(page).getByRole("button", { name: "Find by ZIP", exact: true })).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(finder(page).getByLabel("Search by name", { exact: true })).toBeFocused();
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await expect(fallback).toBeFocused();
    await page.keyboard.press("Tab");
    const house = handoff(page).getByRole("link", { name: officialLinks[0][0], exact: true });
    await expect(house).toBeFocused();
    expect(await house.evaluate((node) => getComputedStyle(node).outlineStyle)).not.toBe("none");
    await page.keyboard.press("Tab");
    await expect(handoff(page).getByRole("link", { name: officialLinks[1][0], exact: true })).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await handoff(page).screenshot({ path: testInfo.outputPath(`finder-link-focus-${width}.png`) });
    await page.keyboard.press("Shift+Tab");
    await expect(fallback).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(finder(page).getByLabel("Search by name", { exact: true })).toBeFocused();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await finder(page).screenshot({ path: testInfo.outputPath(`finder-${width}.png`) });
    await choice(page, foushee).focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#representative-name")).toBeFocused();
    await page.getByRole("button", { name: "Switch representative" }).click();
    await expect(handoff(page)).toHaveCount(0);
    await expect.poll(() => finder(page).evaluate((node) => node.scrollWidth <= node.clientWidth)).toBe(true);
    await finder(page).getByRole("button", { name: "Close", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(finder(page)).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Switch representative" })).toBeFocused();
  });
}

test("official ZIP handoff opens only on activation with literal URLs, no referrer and no opener", async ({ page, context }) => {
  const outbound = [];
  await context.route(/^https:\/\/.*(?:house|senate)\.gov\//, (route) => {
    outbound.push({ url: route.request().url(), method: route.request().method(), referrer: route.request().headers().referer });
    return route.fulfill({ contentType: "text/html", body: "<p>Intercepted official navigation</p>" });
  });
  await page.route("**/lookup/zip/27701", (route) => route.fulfill({ json: cases[1][1] }));
  await page.goto("/"); await expect(handoff(page)).toHaveCount(0);
  await submit(page, "zip", "27701"); await expect(handoff(page)).toBeVisible();
  const url = page.url(), historyLength = await page.evaluate(() => history.length);
  for (const [index, [label, destination]] of officialLinks.entries()) {
    const link = handoff(page).getByRole("link", { name: label, exact: true });
    await link.hover(); await link.focus(); expect(outbound).toHaveLength(index);
    const popupEvent = page.waitForEvent("popup");
    if (index === 0) await link.press("Enter"); else await link.click();
    const popup = await popupEvent; await popup.waitForLoadState();
    expect(outbound[index]).toEqual({ url: destination, method: "GET", referrer: undefined });
    expect(await popup.evaluate(() => window.opener === null && document.referrer === "")).toBe(true);
    await popup.close();
    expect(page.url()).toBe(url); expect(await page.evaluate(() => history.length)).toBe(historyLength);
    await expect(page.locator("#representative-name")).toHaveCount(0);
  }
  expect(outbound).toHaveLength(2);
});
