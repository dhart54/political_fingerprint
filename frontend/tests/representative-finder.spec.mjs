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
  await finder(page).getByRole("button", { name: "Search by representative name", exact: true }).click();
  await expect(page.getByLabel("Search by name", { exact: true })).toBeFocused();
  await submit(page, "zip", "99999");
  await expect(finder(page).getByRole("alert")).toContainText("Try a name search");
  await submit(page, "name", "Deborah Ross");
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

// Hold the actual browser fetch. Release only after a newer result has rendered;
// wait until fetch/json settles before asserting the older completion is inert.
async function holdLookup(page, mode) {
  await page.addInitScript(() => {
    window.__finderCompletions = [];
    const original = window.fetch;
    window.fetch = async (...args) => {
      const url = String(args[0]);
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
        window.__finderCompletions.push(url);
        throw error;
      }
    };
  });
  let received;
  const pending = new Promise((resolve) => { received = resolve; });
  await page.route(mode === "zip" ? "**/lookup/zip/27701" : "**/legislators/search?q=Foushee", (route) => {
    received(route);
  });
  return {
    pending,
    async finish({ reject = false, status = 200 } = {}) {
      const route = await pending;
      const url = route.request().url();
      if (reject) await route.abort("failed");
      else await route.fulfill({ status, json: mode === "zip" ? ready : { results: [foushee] } });
      await page.waitForFunction((value) => window.__finderCompletions.includes(value), url);
      await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    },
  };
}

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
    await submit(page, newMode, newMode === "zip" ? "32003" : "Ross");
    const member = newMode === "zip" ? bean : ross;
    await expect(choice(page, member)).toBeVisible();
    await held.finish();
    await expect(choice(page, member)).toBeVisible();
    await expect(choice(page, foushee)).toHaveCount(0);
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
    await expect(finder(page).getByRole("alert")).toContainText(mode === "zip" ? "5-digit" : "at least two letters");
    await held.finish();
    await expect(finder(page).getByRole("alert")).toBeVisible();
    await expect(finder(page).getByRole("list")).toHaveCount(0);
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
  await held.finish();
  await expect(finder(page).getByRole("list")).toHaveCount(0);
  await page.goForward();
  await expect(page.locator("#representative-name")).toHaveText(foushee.name_display);
});

for (const width of [320, 390, 1440]) {
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
    await page.keyboard.press("Enter");
    await expect(finder(page).getByLabel("Search by name", { exact: true })).toBeFocused();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await finder(page).screenshot({ path: testInfo.outputPath(`finder-${width}.png`) });
    await choice(page, foushee).focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#representative-name")).toBeFocused();
    await page.getByRole("button", { name: "Switch representative" }).click();
    await expect.poll(() => finder(page).evaluate((node) => node.scrollWidth <= node.clientWidth)).toBe(true);
    await finder(page).getByRole("button", { name: "Close", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(finder(page)).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Switch representative" })).toBeFocused();
  });
}
