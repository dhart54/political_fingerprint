import fs from "node:fs";
import path from "node:path";
import { gunzipSync } from "node:zlib";
import { expect, test } from "@playwright/test";

const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/review_packets/record_at_a_glance_v1/candidate.json")));
const snapshot = JSON.parse(gunzipSync(fs.readFileSync(path.resolve("..", candidate.source_snapshot))));
const assistance = candidate.entries.find((e) => e.finding_id === "wording:synthesis:security-assistance");
const education = candidate.entries.find((e) => e.issue_id === "EDUCATION_WORKFORCE");
const profiles = [
  { id: "leg_valerie_p_foushee", bioguide_id: "F000477", name_display: "Valerie P. Foushee", chamber: "house", state: "NC", district: "04", party: "D" },
  { id: "leg_thomas_massie", bioguide_id: "M001184", name_display: "Thomas Massie", chamber: "house", state: "KY", district: "04", party: "R" },
  { id: "leg_angela_d_alsobrooks", bioguide_id: "A000381", name_display: "Angela D. Alsobrooks", chamber: "senate", state: "MD", party: "D" },
];

// Test-only responses at the real read-interface URLs. The ordinary app must
// request these interfaces, never the opt-in snapshot replay API.
async function liveInterfaceResponses(page) {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const member = url.pathname.split("/")[2];
    if (url.pathname.endsWith("/profile")) return route.fulfill({ json: profiles.find((p) => p.id === member) });
    const scope = url.searchParams.get("scope") || "all";
    const resource = url.pathname.endsWith("/editorial-presentations") ? "editorial" : url.pathname.endsWith("/evidence") ? url.pathname.split("/")[4] : "positions";
    const supplied = snapshot[`${member}:${scope}:${resource}`];
    if (!supplied) throw Error(`Unexpected live-interface request: ${url.pathname}`);
    await route.fulfill({ status: supplied.status, json: supplied.body });
  });
}

for (const width of [390, 1440]) test(`explicit Close returns keyboard focus without changing the released journey at width ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await liveInterfaceResponses(page);
  const trigger = page.getByRole("button", { name: "Switch representative", exact: true });
  const cards = page.getByTestId("record-card-entry");
  const readCards = () => cards.evaluateAll((nodes) => nodes.map((node) => ({
    id: node.querySelector("a[id]").id,
    href: node.querySelector("a[id]").getAttribute("href"),
    text: node.textContent,
  })));
  async function closeWithKeyboard() {
    const url = page.url();
    const historyLength = await page.evaluate(() => history.length);
    await trigger.focus();
    await trigger.press("Enter");
    const finder = page.getByTestId("representative-finder");
    await expect(finder).toBeVisible();
    await page.keyboard.press("Tab");
    await expect(finder.getByRole("button", { name: "Close", exact: true })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(finder).toHaveCount(0);
    await expect(trigger).toBeFocused();
    expect(page.url()).toBe(url);
    expect(await page.evaluate(() => history.length)).toBe(historyLength);
    await expect(page.locator("#representative-name")).toHaveText("Valerie P. Foushee");
  }
  for (const scope of ["all", "119"]) {
    await page.goto(`/?representative=leg_valerie_p_foushee&scope=${scope}`);
    await expect(cards).toHaveCount(6);
    const before = await readCards();
    expect(before.map((entry) => entry.id).sort()).toEqual(candidate.entries.map((entry) => entry.id).sort());
    await closeWithKeyboard();
    expect(await readCards()).toEqual(before);
    await page.keyboard.press("Tab");
    await expect(page.getByRole("button", { name: "All available Congresses", exact: true })).toBeFocused();
    // Close is not navigation, including when a finding/source is selected.
    await page.locator(`#${assistance.id}`).click();
    await expect(page.locator("#finding-detail-heading")).toBeFocused();
    const detailUrl = page.url();
    await closeWithKeyboard();
    await page.goBack();
    await expect(cards).toHaveCount(6);
    expect(await readCards()).toEqual(before);
    await page.goForward();
    await expect(page).toHaveURL(detailUrl);
    await expect(page.locator("#finding-detail-heading")).toBeVisible();
  }
});

async function holdInitialIssueFocus(page) {
  await page.addInitScript(() => {
    const scroll = Element.prototype.scrollIntoView;
    const frame = window.requestAnimationFrame.bind(window);
    let hold = false;
    window.initialFocusEvents = [];
    const record = (event, target) => window.initialFocusEvents.push({ event, target: target?.slice(0, 80), time: performance.now() });
    window.addEventListener("keydown", (event) => record(`keydown:${event.key}`, document.activeElement?.textContent));
    window.addEventListener("focusin", (event) => record("focusin", event.target?.id || event.target?.textContent));
    Element.prototype.scrollIntoView = function (...args) {
      if (this.id === "issue-summary") { hold = true; record("initial-scroll", this.id); }
      return scroll.apply(this, args);
    };
    window.requestAnimationFrame = (callback) => {
      if (!hold) return frame(callback);
      hold = false;
      return frame((time) => {
        record("focus-frame-held");
        window.releaseInitialIssueFocus = () => { record("release-initial-focus"); callback(time); };
      });
    };
  });
}

for (const surface of ["ordinary", "review"]) test.describe(surface, () => {
  const routePath = surface === "ordinary" ? "/" : "/review/record-card";
  const landing = `${routePath}?representative=leg_valerie_p_foushee&scope=119`;
  const editorialUrl = surface === "ordinary" ? "**/editorial-presentations*" : "**/api/review/record-card?resource=editorial*";
  async function selectScope(page, scope) {
    if (surface === "review") await page.getByLabel("Recorded votes", { exact: true }).selectOption(scope);
    else await page.getByRole("button", { name: scope === "all" ? "All available Congresses" : `${scope}th Congress`, exact: true }).click();
  }
  test.beforeEach(async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    if (surface === "ordinary") await liveInterfaceResponses(page);
  });

  async function changeEditorial(page, change) {
    await page.route(editorialUrl, async (route) => {
      const body = structuredClone(snapshot["leg_valerie_p_foushee:119:editorial"].body);
      change(body);
      await route.fulfill({ json: body });
    });
  }

  test("compact assistance opens all five unchanged paragraphs in one click and retains the complete journey", async ({ page }) => {
    const requests = [];
    page.on("request", (request) => requests.push(request.url()));
    await page.goto(landing);
    const card = page.getByTestId("record-card");
    await expect(card.getByTestId("record-card-entry")).toHaveCount(6);
    await expect(card).toContainText(assistance.explanation);
    await expect(card).not.toContainText(assistance.detail_paragraphs[0]);
    expect(requests.filter((url) => /resource=evidence|\/evidence\?/.test(url))).toHaveLength(0);
    const link = page.locator(`#${assistance.id}`);
    expect(new URL(await link.getAttribute("href"), "http://localhost").pathname).toBe(routePath);
    await link.focus(); await page.keyboard.press("Enter");
    await expect(page.locator("#finding-detail-heading")).toBeFocused();
    const detail = page.getByTestId("card-finding-explanation");
    await expect(detail.locator("p")).toHaveText(assistance.detail_paragraphs);
    await expect(detail.locator("details")).toHaveCount(0);
    for (const paragraph of assistance.detail_paragraphs) await expect(detail.getByText(paragraph, { exact: true })).toBeVisible();
    await page.reload();
    await expect(detail.locator("p")).toHaveText(assistance.detail_paragraphs);
    await page.getByRole("link", { name: /^See 8 House votes:/ }).click();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(8);
    const ids = await page.locator("[data-canonical-action-id]").evaluateAll((els) => els.map((el) => el.dataset.canonicalActionId).sort());
    expect(ids).toEqual([...assistance.action_ids].sort());
    await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
    await page.goBack();
    await expect(detail.locator("p")).toHaveText(assistance.detail_paragraphs);
    await page.goForward();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(8);
    await page.getByRole("link", { name: "Complete issue record / all votes" }).click();
    await expect(page).not.toHaveURL(/finding=/);
    await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
    await expect(page.locator("#vote-record")).toContainText("recorded actions");
    await page.goBack();
    await page.getByRole("link", { name: "Return to record at a glance" }).click();
    await expect(link).toBeFocused();
    expect(new URL(page.url()).pathname).toBe(routePath);
    if (surface === "ordinary") expect(requests.some((url) => url.includes("/api/review/"))).toBe(false);
  });

  test("a stale card is withheld while independently valid current summaries and full receipts remain", async ({ page }) => {
    // Change only source metadata, not any politician's claim or vote meaning.
    await changeEditorial(page, (body) => { body.presentations.find((p) => p.issue_id === "JUSTICE_PUBLIC_SAFETY").provenance.test_source_revision = "current-api-source"; });
    await page.goto(landing);
    await expect(page.getByText(/The reviewed source has changed/)).toBeVisible();
    await expect(page.getByTestId("record-card")).toHaveCount(0);
    await expect(page.getByText(/No reviewed findings are available|Issue summaries could not be verified/)).toHaveCount(0);
    await page.getByRole("button", { name: "Explore Justice & Public Safety", exact: true }).click();
    await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
    await expect(page.getByTestId("reviewed-analysis")).toContainText("D.C.");
    await expect(page.locator("#vote-record")).toContainText("recorded actions");
    // Even an old exact-source deep link retains the current full issue summary.
    const source = candidate.sources.find((s) => s.issue_id === education.issue_id).presentation_sha256["119"];
    await page.goto(`${landing}&issue=${education.issue_id}&finding=${encodeURIComponent(education.finding_id)}&source=${source}#finding-detail`);
    await expect(page.getByText(/This finding link does not match/)).toBeVisible();
    await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
    await expect(page.locator("#vote-record")).toContainText("25 recorded actions");
  });

  test("API failures and invalid member, scope or data remain distinct from no summary", async ({ page }) => {
    await page.route(editorialUrl, (route) => route.fulfill({ status: 503, body: "unavailable" }));
    await page.goto(landing);
    await expect(page.getByText(/Reviewed findings are unavailable right now/)).toBeVisible();
    await expect(page.getByText(/No reviewed findings are available/)).toHaveCount(0);
    await page.getByRole("button", { name: "Browse vote record for Justice & Public Safety" }).click();
    await expect(page.getByTestId("reviewed-analysis")).toHaveCount(0);
    await expect(page.locator("#vote-record")).toContainText("recorded actions");
    for (const invalid of ["member", "scope", "data"]) {
      await changeEditorial(page, (body) => {
        if (invalid === "member") body.member_bioguide_id = "WRONG";
        if (invalid === "scope") body.scope = "118";
        if (invalid === "data") body.presentations.pop();
      });
      await page.goto(landing);
      await expect(page.getByText(/Issue summaries could not be verified/)).toBeVisible();
      await expect(page.getByTestId("record-card")).toHaveCount(0);
      await expect(page.getByRole("button", { name: /^Explore Justice/ })).toHaveCount(0);
    }
  });

  test("real no-summary member and scope, scope changes and direct paired receipts are truthful", async ({ page }) => {
    await page.goto(landing.replace("leg_valerie_p_foushee", "leg_thomas_massie"));
    await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
    await expect(page.getByTestId("record-card")).toHaveCount(0);
    await page.goto(landing);
    await selectScope(page, "118");
    await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
    await selectScope(page, "all");
    await expect(page.getByTestId("record-card")).toContainText("119th Congress");
    await page.locator(`#${education.id}`).click();
    await expect(page.getByTestId("card-finding-detail")).toContainText("The final vote does not identify which part she opposed.");
    await page.getByRole("link", { name: /^See 2 House votes:/ }).click();
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
    await page.reload();
    for (const id of education.action_ids) await expect(page.locator(`[data-canonical-action-id="${id}"]`)).toBeVisible();
    await page.goto(`${landing}&issue=EDUCATION_WORKFORCE#action-receipt-house-119-1-79`);
    await expect(page.locator("#action-receipt-house-119-1-79 button").first()).toBeFocused();
    expect(new URL(page.url()).pathname).toBe(routePath);
  });

  test("loading stays distinct and a delayed previous scope cannot restore its card", async ({ page }) => {
    let release;
    const gate = new Promise((resolve) => { release = resolve; });
    await page.route(editorialUrl, async (route) => {
      if (new URL(route.request().url()).searchParams.get("scope") !== "119") return route.fallback();
      await gate;
      await route.fulfill({ json: snapshot["leg_valerie_p_foushee:119:editorial"].body });
    });
    try {
      await page.goto(landing);
      await expect(page.getByText("Loading reviewed findings…", { exact: true })).toBeVisible();
      await expect(page.getByText(/No reviewed findings are available/)).toHaveCount(0);
      await selectScope(page, "118");
      await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
      release();
      await expect(page.getByTestId("record-card")).toHaveCount(0);
      await expect(page).toHaveURL(/scope=118/);
    } finally { release(); }
  });

  test("every selected entry resolves its complete action set on this route", async ({ page }) => {
    for (const entry of candidate.entries) {
      await page.goto(landing);
      await page.locator(`#${entry.id}`).click();
      await page.getByRole("link", { name: `See ${entry.action_ids.length} House votes: ${entry.headline}` }).click();
      await expect(page.locator("[data-canonical-action-id]")).toHaveCount(entry.action_ids.length);
      expect(await page.locator("[data-canonical-action-id]").evaluateAll((els) => els.map((el) => el.dataset.canonicalActionId).sort())).toEqual([...entry.action_ids].sort());
      expect(new URL(page.url()).pathname).toBe(routePath);
    }
  });

  for (const scope of ["all", "119"]) test(`header Vote record opens exact finding receipts in ${scope} scope`, async ({ page }) => {
    test.setTimeout(60_000);
    for (const [index, entry] of candidate.entries.entries()) {
      await page.goto(`${routePath}?representative=leg_valerie_p_foushee&scope=${scope}`);
      await page.locator(`#${entry.id}`).click();
      await expect(page.getByTestId("card-finding-detail")).toBeVisible();
      await expect(page.locator("#finding-detail-heading")).toBeFocused();
      await expect(page.locator("#vote-record")).toHaveCount(0);
      const before = new URL(page.url());
      const headerLink = page.getByRole("navigation", { name: "Selected issue sections" }).getByRole("link", { name: "Vote record", exact: true });
      const findingLink = page.getByRole("link", { name: `See ${entry.action_ids.length} House votes: ${entry.headline}` });
      await expect(headerLink).toHaveAttribute("href", await findingLink.getAttribute("href"));
      if (index % 2) { await headerLink.focus(); await page.keyboard.press("Enter"); }
      else await headerLink.click();
      const after = new URL(page.url());
      for (const key of ["representative", "scope", "issue", "finding", "source"]) expect(after.searchParams.get(key)).toBe(before.searchParams.get(key));
      expect(after.pathname).toBe(routePath);
      expect(after.searchParams.get("view")).toBe("receipts");
      expect(after.hash).toBe("#vote-record");
      await expect(page.locator("[data-canonical-action-id]")).toHaveCount(entry.action_ids.length);
      expect(await page.locator("[data-canonical-action-id]").evaluateAll((els) => els.map((el) => el.dataset.canonicalActionId).sort())).toEqual([...entry.action_ids].sort());
      await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
      if (entry.finding_id === "wording:synthesis:war-powers") {
        await page.reload();
        await expect(page.locator("[data-canonical-action-id]")).toHaveCount(entry.action_ids.length);
        await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
        await page.goBack();
        await expect(page).not.toHaveURL(/view=receipts/);
        await expect(page.locator("#vote-record")).toHaveCount(0);
        await expect(page.locator("#finding-detail-heading")).toBeFocused();
        await page.goForward();
        await expect(page.locator("[data-canonical-action-id]")).toHaveCount(entry.action_ids.length);
        await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
      }
    }
  });

  test("header navigation keeps focus when initial issue focus is delayed", async ({ page }) => {
    // Hold the frame after the initial summary scroll, then release it after
    // keyboard navigation. This exercises the browser race without sleeps.
    await page.addInitScript(() => {
      const scrollIntoView = Element.prototype.scrollIntoView;
      const requestFrame = window.requestAnimationFrame.bind(window);
      let holdNextFrame = false;
      Element.prototype.scrollIntoView = function (...args) {
        if (this.id === "issue-summary") holdNextFrame = true;
        return scrollIntoView.apply(this, args);
      };
      window.requestAnimationFrame = (callback) => {
        if (!holdNextFrame) return requestFrame(callback);
        holdNextFrame = false;
        return requestFrame((time) => {
          window.releaseInitialIssueFocus = () => callback(time);
        });
      };
    });
    await page.goto(`${routePath}?representative=leg_valerie_p_foushee&scope=119&issue=ENVIRONMENT_ENERGY`);
    await expect(page.locator("#vote-record")).toContainText("recorded");
    await expect.poll(() => page.evaluate(() => typeof window.releaseInitialIssueFocus)).toBe("function");
    const link = page.getByRole("navigation", { name: "Selected issue sections" }).getByRole("link", { name: "Vote record", exact: true });
    await link.focus();
    await page.keyboard.press("Enter");
    const heading = page.getByRole("heading", { name: "Vote record", exact: true });
    await expect(heading).toBeFocused();
    await page.evaluate(() => window.releaseInitialIssueFocus());
    await test.info().attach("focus-after-delayed-initial-frame", {
      body: JSON.stringify(await page.evaluate(() => ({
        hash: window.location.hash,
        activeId: document.activeElement?.id,
        activeText: document.activeElement?.textContent,
      }))),
      contentType: "application/json",
    });
    await expect(heading).toBeFocused();
    await expect(page).toHaveURL(/#vote-record$/);
  });

  for (const interaction of ["Tab", "header focus"]) test(`initial issue landing preserves early ${interaction}`, async ({ page }, testInfo) => {
    await holdInitialIssueFocus(page);
    await page.goto(`${routePath}?representative=leg_valerie_p_foushee&scope=119&issue=ENVIRONMENT_ENERGY`);
    await expect.poll(() => page.evaluate(() => typeof window.releaseInitialIssueFocus)).toBe("function");
    if (interaction === "Tab") await page.keyboard.press("Tab");
    else await page.getByRole("navigation", { name: "Selected issue sections" }).getByRole("link", { name: "Vote record", exact: true }).focus();
    expect(await page.evaluate(() => {
      window.earlyInteractionFocus = document.activeElement;
      return document.activeElement !== document.body;
    })).toBe(true);
    await page.evaluate(() => window.releaseInitialIssueFocus());
    await testInfo.attach("early-focus-observation", { contentType: "application/json", body: JSON.stringify(await page.evaluate(() => ({
      expectedText: window.earlyInteractionFocus?.textContent,
      activeId: document.activeElement?.id,
      activeText: document.activeElement?.textContent,
      hash: location.hash,
      events: window.initialFocusEvents,
    }))) });
    expect(await page.evaluate(() => document.activeElement === window.earlyInteractionFocus)).toBe(true);
    if (interaction === "header focus") {
      await page.keyboard.press("Enter");
      await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
      await expect(page).toHaveURL(/#vote-record$/);
    }
  });

  test("header anchors preserve full reviewed and receipts-only issue routes", async ({ page }) => {
    for (const [member, scope, issue] of [
      ["leg_valerie_p_foushee", "119", "ENVIRONMENT_ENERGY"],
      ["leg_valerie_p_foushee", "118", "JUSTICE_PUBLIC_SAFETY"],
      ["leg_thomas_massie", "119", "ECONOMY_TAXES"],
      ...(surface === "ordinary" ? [["leg_angela_d_alsobrooks", "119", "EDUCATION_WORKFORCE"]] : []),
    ]) {
      await page.goto(`${routePath}?representative=${member}&scope=${scope}&issue=${issue}`);
      const ledger = page.locator("#vote-record");
      await expect(ledger).toContainText("recorded");
      const headerLink = page.getByRole("navigation", { name: "Selected issue sections" }).getByRole("link", { name: "Vote record", exact: true });
      await expect(headerLink).toHaveAttribute("href", "#vote-record");
      await headerLink.focus(); await page.keyboard.press("Enter");
      await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
      const url = new URL(page.url());
      expect(url.searchParams.get("representative")).toBe(member);
      expect(url.searchParams.get("scope")).toBe(scope);
      expect(url.searchParams.get("issue")).toBe(issue);
      expect(url.searchParams.has("finding")).toBe(false);
      expect(url.searchParams.has("view")).toBe(false);
      if (member === "leg_angela_d_alsobrooks") await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
      await page.reload();
      await expect(ledger).toBeVisible();
      await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
    }
  });

  test("complete desktop/mobile card and opened assistance are readable and captured", async ({ page }) => {
    const output = process.env.RECORD_CARD_RELEASE_SCREENSHOT_DIR;
    if (output) fs.mkdirSync(output, { recursive: true });
    for (const [name, width, height] of [["desktop", 1440, 900], ["mobile", 390, 844], ["narrow", 360, 800]]) {
      await page.setViewportSize({ width, height });
      await page.goto(landing);
      const card = page.getByTestId("record-card");
      await expect(card.getByTestId("record-card-entry")).toHaveCount(6);
      for (const entry of candidate.entries) await expect(card.getByText(entry.explanation, { exact: true })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      const textStyle = await card.locator("article p.mt-2").first().evaluate((el) => ({ fontSize: getComputedStyle(el).fontSize, clamp: getComputedStyle(el).webkitLineClamp, overflow: getComputedStyle(el).overflow }));
      expect(textStyle.fontSize).toBe("14px"); expect(textStyle.clamp).toBe("none"); expect(textStyle.overflow).toBe("visible");
      if (output) {
        await page.screenshot({ path: path.join(output, `${surface}-${name}-landing.png`) });
        await page.screenshot({ path: path.join(output, `${surface}-${name}-complete-card.png`), fullPage: true, clip: await card.boundingBox() });
      }
      await page.locator(`#${assistance.id}`).click();
      await expect(page.getByTestId("card-finding-explanation").locator("p")).toHaveText(assistance.detail_paragraphs);
      await expect(page.locator("#finding-detail-heading")).toBeFocused();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      if (output) {
        await page.evaluate(async () => {
          window.scrollTo({ top: 0, behavior: "instant" });
          await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        });
        expect(await page.evaluate(() => window.scrollY)).toBe(0);
        await page.screenshot({ path: path.join(output, `${surface}-${name}-assistance-detail.png`), fullPage: true, clip: await page.getByTestId("card-finding-detail").boundingBox() });
      }
    }
  });

  test("partial receipt response discloses missing linked votes without changing the finding", async ({ page }) => {
    const evidenceUrl = surface === "ordinary" ? "**/positions/EDUCATION_WORKFORCE/evidence*" : "**/api/review/record-card?resource=evidence*";
    await page.route(evidenceUrl, async (route) => {
      const url = new URL(route.request().url());
      if (surface === "review" && url.searchParams.get("domain") !== "EDUCATION_WORKFORCE") return route.fallback();
      const body = structuredClone(snapshot["leg_valerie_p_foushee:119:EDUCATION_WORKFORCE"].body);
      body.evidence = body.evidence.filter((row) => row.canonical_action_id !== "house:119:1:83");
      await route.fulfill({ json: body });
    });
    await page.goto(landing);
    await page.locator(`#${education.id}`).click();
    const detail = page.getByTestId("card-finding-detail");
    await expect(detail).toContainText(education.evidence_label);
    await expect(detail).toContainText("The final vote does not identify which part she opposed.");
    await page.getByRole("link", { name: /^See 2 House votes:/ }).click();
    const notice = page.getByRole("status").filter({ hasText: "Showing 1 of 2 linked vote receipts." });
    await expect(notice).toBeVisible();
    await expect(notice).toContainText("The remaining linked receipt is unavailable in this response.");
    await expect(page.locator("[data-canonical-action-id]")).toHaveCount(1);
    await expect(page.locator("[data-canonical-action-id]")).toHaveAttribute("data-canonical-action-id", "house:119:1:79");
    await expect(page.getByRole("heading", { name: "Vote record", exact: true })).toBeFocused();
    await expect(detail).toContainText(education.evidence_label);
    await expect(detail).toContainText("The final vote does not identify which part she opposed.");
    await page.reload();
    await expect(notice).toBeVisible();
    await page.goBack();
    await expect(page.locator("#finding-detail-heading")).toBeFocused();
    await page.goForward();
    await expect(notice).toBeVisible();
    await page.getByRole("link", { name: "Complete issue record / all votes" }).click();
    await expect(notice).toHaveCount(0);
    await expect(page.locator("#vote-record")).toContainText("24 recorded actions");
  });
});
