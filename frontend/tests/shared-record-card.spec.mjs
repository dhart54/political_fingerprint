import fs from "node:fs";
import path from "node:path";
import { gunzipSync } from "node:zlib";
import { expect, test } from "@playwright/test";
import { buildSharedRecordCard } from "../lib/sharedRecordCard.mjs";

const snapshot = JSON.parse(gunzipSync(fs.readFileSync(path.resolve("../docs/editorial/publication_replacements/m15b_green_activation_execution/after-justice-live.json.gz"))));
const payload = snapshot["leg_valerie_p_foushee:119:editorial"].body;
const model = await buildSharedRecordCard({ payload, legislatorId: payload.legislator_id, memberBioguideId: payload.member_bioguide_id, scope: "119" });
const assistance = model.entries.find((e) => e.finding_id === "wording:synthesis:security-assistance");
const profiles = [
  { id: "leg_valerie_p_foushee", bioguide_id: "F000477", name_display: "Valerie P. Foushee", chamber: "house", state: "NC", district: "04", party: "D" },
  { id: "leg_thomas_massie", bioguide_id: "M001184", name_display: "Thomas Massie", chamber: "house", state: "KY", district: "04", party: "R" },
];
const base = "/review/record-card?policy=shared&representative=leg_valerie_p_foushee&scope=119";
async function liveReads(page, transform = (body) => body) {
  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const member = url.pathname.split("/")[2];
    if (url.pathname.endsWith("/profile")) return route.fulfill({ json: profiles.find((p) => p.id === member) });
    const scope = url.searchParams.get("scope") || "all";
    const resource = url.pathname.endsWith("/editorial-presentations") ? "editorial" : url.pathname.endsWith("/evidence") ? url.pathname.split("/")[4] : "positions";
    const response = snapshot[`${member}:${scope}:${resource}`];
    if (!response) throw Error(`Unexpected read ${url}`);
    await route.fulfill({ status: response.status, json: resource === "editorial" ? transform(structuredClone(response.body)) : response.body });
  });
}
async function capture(page, target, name) {
  if (!process.env.RECORD_CARD_CAPTURE_DIR) return;
  fs.mkdirSync(process.env.RECORD_CARD_CAPTURE_DIR, { recursive: true });
  // A full element screenshot otherwise captures the sticky site header across
  // the middle after scrolling through every card link. Reset real scroll only.
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const box = await target.boundingBox();
  await page.screenshot({ fullPage: true, clip: box, path: path.join(process.env.RECORD_CARD_CAPTURE_DIR, `${name}.png`) });
}

for (const mode of ["desktop-live", "mobile-snapshot"]) test(`${mode}: whole shared card, complete detail, paired receipts and persistent navigation`, async ({ page }) => {
  test.setTimeout(60_000);
  await page.setViewportSize(mode.startsWith("mobile") ? { width: 390, height: 844 } : { width: 1280, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const requests = [];
  page.on("request", (r) => requests.push(r.url()));
  if (mode.endsWith("live")) await liveReads(page);
  await page.goto(`${base}&data=${mode.endsWith("live") ? "live" : "snapshot"}`);
  const card = page.getByTestId("record-card");
  await expect(card.getByTestId("record-card-entry")).toHaveCount(model.entries.length);
  expect(requests.filter((url) => /resource=evidence|\/evidence\?/.test(url))).toHaveLength(0);
  if (mode.endsWith("live")) expect(requests.some((url) => url.includes("/api/review/"))).toBe(false);
  for (const entry of model.entries) {
    await expect(card.getByText(entry.headline, { exact: true })).toBeVisible();
    const link = page.locator(`#${entry.id}`);
    await link.scrollIntoViewIfNeeded();
    const box = await link.boundingBox();
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(page.viewportSize().width);
    expect(box.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await capture(page, card, `${mode}-card`);
  const link = page.locator(`#${assistance.id}`);
  await link.focus(); await page.keyboard.press("Enter");
  await expect(page.locator("#finding-detail-heading")).toBeFocused();
  const detail = page.getByTestId("card-finding-explanation");
  await expect(detail.locator("p")).toHaveText(assistance.detail_paragraphs);
  await expect(detail.locator("details")).toHaveCount(0);
  await capture(page, page.getByTestId("card-finding-detail"), `${mode}-detail`);
  await page.reload();
  await expect(detail.locator("p")).toHaveText(assistance.detail_paragraphs);
  await page.getByRole("link", { name: /^See 8 House votes:/ }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(8);
  expect(await page.locator("[data-canonical-action-id]").evaluateAll((els) => els.map((el) => el.dataset.canonicalActionId).sort())).toEqual([...assistance.action_ids].sort());
  await page.goBack(); await expect(detail).toBeVisible();
  await page.goForward(); await expect(page.locator("[data-canonical-action-id]")).toHaveCount(8);
  await page.getByRole("link", { name: "Complete issue record / all votes" }).click();
  await expect(page).not.toHaveURL(/finding=/);
  await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
  await page.goBack();
  await page.getByRole("link", { name: "Return to record at a glance" }).click();
  await expect(link).toBeFocused();
  await expect(page).toHaveURL(/policy=shared/);
});

test("a sparse Education card keeps the substitute and whole package together", async ({ page }) => {
  // Controlled sparse shape, not the real second-member acceptance proof.
  await liveReads(page, (body) => { for (const p of body.presentations) if (p.issue_id !== "EDUCATION_WORKFORCE") { p.review_state = null; p.tier = "receipts_only"; } return body; });
  await page.goto(`${base}&data=live`);
  await page.locator("#shared-card-EDUCATION_WORKFORCE-m14f-notable-hr1048-substitute-final").click();
  await expect(page.getByTestId("card-finding-detail")).toContainText("whole package");
  await page.getByRole("link", { name: /^See 2 House votes:/ }).click();
  await expect(page.locator("[data-canonical-action-id]")).toHaveCount(2);
  expect(await page.locator("[data-canonical-action-id]").evaluateAll((els) => els.map((el) => el.dataset.canonicalActionId).sort())).toEqual(["house:119:1:79", "house:119:1:83"]);
});

test("old source deep link leaves current issue summaries, receipts and full record intact", async ({ page }) => {
  await liveReads(page, (body) => { body.presentations.find((p) => p.issue_id === assistance.issue_id).provenance.test_revision = "new-source"; return body; });
  await page.goto(`${base}&data=live&issue=${assistance.issue_id}&finding=${encodeURIComponent(assistance.finding_id)}&source=${assistance.sourcePresentationHash}#finding-detail`);
  await expect(page.getByTestId("card-finding-detail")).toHaveCount(0);
  await expect(page.getByTestId("reviewed-analysis")).toBeVisible();
  await expect(page.locator("#vote-record")).toContainText("recorded actions");
  await expect(page.getByText(/No reviewed findings are available|Issue summaries could not be verified/)).toHaveCount(0);
});

test("shared review distinguishes no findings, unsupported forms and unavailable API", async ({ page }) => {
  await page.goto(`${base.replace("leg_valerie_p_foushee", "leg_thomas_massie")}&data=snapshot`);
  await expect(page.getByText(/No reviewed findings are available/)).toBeVisible();
  await liveReads(page, (body) => {
    for (const p of body.presentations) for (const field of ["syntheses", "repeated_patterns", "policy_trajectories", "notable_choices"]) for (const finding of p[field] || []) finding.action_ids = [];
    return body;
  });
  await page.goto(`${base}&data=live`);
  await expect(page.getByText(/need a supported overview form/)).toBeVisible();
  await page.route("**/editorial-presentations*", (route) => route.fulfill({ status: 503, json: { detail: "Unavailable" } }));
  await page.reload();
  await expect(page.getByText(/Reviewed findings are unavailable right now/)).toBeVisible();
  await expect(page.getByText(/No reviewed findings are available/)).toHaveCount(0);
});
