import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gunzipSync } from "node:zlib";
import test from "node:test";
import { contentHash, projectRecordCard, resolveCardFinding, recordCardUrl, suppliedDirection } from "./recordCard.mjs";
import { recordCardReviewEnabled } from "./recordCardReviewServer.mjs";
import { parsePassARouteState, buildPassAUrl } from "./frontendPassA.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const candidate = JSON.parse(fs.readFileSync(path.join(root, "docs/review_packets/record_at_a_glance_v1/candidate.json")));
const snapshot = JSON.parse(gunzipSync(fs.readFileSync(path.join(root, candidate.source_snapshot))));
const payload = snapshot["leg_valerie_p_foushee:119:editorial"].body;
const args = { candidate, payload, legislatorId: candidate.legislator_id, memberBioguideId: candidate.member_bioguide_id, scope: "119" };

test("exact current publication roots and complete accepted selection remain stable", async () => {
  assert.deepEqual(candidate.sources.map((s) => s.published_artifact_id), [245, 239, 251, 248]);
  const before = JSON.stringify(payload);
  const first = await projectRecordCard(args);
  assert.equal(first.status, "ready");
  assert.equal(first.entries.length, 6);
  assert.deepEqual(first, await projectRecordCard(args));
  assert.equal(JSON.stringify(payload), before, "projection must not edit accepted payloads");
  const ns = payload.presentations.find((p) => p.issue_id === "NATIONAL_SECURITY_FOREIGN");
  assert.equal(ns.policy_trajectories.length, 0, "do not revive superseded NS trajectory");
});

test("source findings, all supporting actions and explicitly supplied episodes are traceable", async () => {
  for (const entry of (await projectRecordCard(args)).entries) {
    assert.equal(await contentHash(entry.sourceFinding), entry.finding_sha256);
    assert.deepEqual(entry.action_ids, entry.sourceFinding.action_ids);
    assert.deepEqual(entry.episode_ids, entry.sourceFinding.episode_ids ?? null);
    assert.equal(entry.episode_count, entry.sourceFinding.episode_ids?.length ?? null);
    const ledger = snapshot[`${candidate.legislator_id}:119:${entry.issue_id}`].body.evidence;
    for (const id of entry.action_ids) assert.ok(ledger.some((r) => r.canonical_action_id === id));
  }
});

test("member, scope, complete input, and immutable presentation identity fail closed", async () => {
  for (const overrides of [{ legislatorId: "leg_thomas_massie" }, { memberBioguideId: "M001184" }, { scope: "118" }]) assert.equal((await projectRecordCard({ ...args, ...overrides })).status, "identity_mismatch");
  const partial = structuredClone(payload); partial.presentations.pop();
  assert.equal((await projectRecordCard({ ...args, payload: partial })).status, "incomplete");
  const changed = structuredClone(payload); changed.presentations.find((p) => p.review_state).teaser += " changed";
  assert.equal((await projectRecordCard({ ...args, payload: changed })).status, "source_mismatch");
  const wrong = structuredClone(candidate); wrong.entries[0].action_ids = ["house:119:1:1"];
  assert.equal((await projectRecordCard({ ...args, candidate: wrong })).status, "source_mismatch");
});

test("recorded Yea/Nay, party, title or prose never assigns missing policy direction", () => {
  for (const position of ["yea", "nay", "present", "not_voting"]) assert.equal(suppliedDirection({ position, title: "Supported an important policy", party: "D", action_ids: ["house:119:1:1"] }), null);
  assert.equal(suppliedDirection({ direction: null, semantic_lineage_directions: ["opposition"] }), "opposition");
  assert.equal(suppliedDirection({ direction: null, semantic_lineage_directions: ["support", "opposition"] }), null);
});

test("mixed choices and whole-package qualifications stay together", async () => {
  const entries = (await projectRecordCard(args)).entries;
  const education = entries.find((e) => e.issue_id === "EDUCATION_WORKFORCE");
  assert.equal(education.section, "mixed");
  assert.deepEqual(education.action_ids, ["house:119:1:79", "house:119:1:83"]);
  assert.match(education.explanation, /final vote does not identify which part she opposed/);
  const assistance = entries.find((e) => e.finding_id === "wording:synthesis:security-assistance");
  assert.equal(assistance.section, "mixed");
  assert.equal(assistance.action_ids.length, 8);
  for (const country of ["Ukraine", "Jordan", "Taiwan", "Israel"]) assert.ok(assistance.explanation.includes(country));
  assert.equal(assistance.explanation, assistance.sourceFinding.primary_sentence);
});

test("all-scope coverage stays 119th-Congress bounded and has no invented cutoff", async () => {
  const model = await projectRecordCard({ ...args, scope: "all", payload: snapshot[`${candidate.legislator_id}:all:editorial`].body });
  assert.equal(model.status, "ready");
  assert.equal(model.scope, "all");
  assert.equal(model.evidenceCutoff, null);
  assert.equal(model.reviewedDomains.length, 4);
  assert.ok(model.entries.every((e) => e.reviewedScope === "119th Congress"));
});

test("selection does not inflate evidence through overlapping findings or infer episodes", async () => {
  const entries = (await projectRecordCard(args)).entries;
  const ids = entries.flatMap((e) => e.action_ids);
  assert.equal(ids.length, new Set(ids).size);
  assert.equal(ids.length, 29);
  assert.equal(entries.find((e) => e.finding_id === "prop:d7e189366b477118").episode_count, null);
});

test("real no-summary scopes are distinct from failed or incomplete requests", async () => {
  assert.equal((await projectRecordCard({ ...args, scope: "118", payload: snapshot[`${candidate.legislator_id}:118:editorial`].body })).status, "empty");
  assert.equal((await projectRecordCard({ ...args, legislatorId: "leg_thomas_massie", memberBioguideId: "M001184", payload: snapshot["leg_thomas_massie:119:editorial"].body })).status, "empty");
  assert.equal((await projectRecordCard({ ...args, requestStatus: "error", payload: null })).status, "error");
  assert.equal((await projectRecordCard({ ...args, requestStatus: "loading", payload: null })).status, "loading");
  assert.equal((await projectRecordCard({ ...args, payload: null })).status, "incomplete");
});

test("finding routes bind source and preserve representative, scope and exact destination", async () => {
  const model = await projectRecordCard(args), e = model.entries[0];
  assert.equal(resolveCardFinding(model, e.issue_id, e.finding_id, e.sourcePresentationHash), e);
  assert.equal(resolveCardFinding(model, e.issue_id, e.finding_id, "old-source"), null);
  const url = recordCardUrl("http://localhost/review/record-card", { legislatorId: args.legislatorId, scope: "119", issue: e.issue_id, findingId: e.finding_id, sourceHash: e.sourcePresentationHash, view: "receipts", hash: "vote-record" });
  const parsed = parsePassARouteState(new URL(url, "http://localhost").search);
  assert.equal(parsed.findingId, e.finding_id); assert.equal(parsed.findingSource, e.sourcePresentationHash); assert.equal(parsed.findingView, "receipts");
  assert.ok(url.endsWith("#vote-record"));
  assert.ok(!buildPassAUrl(`http://localhost${url}`, { ...parsed, scope: "118" }).includes("finding="));
});

test("review flag cannot enable this candidate on Vercel or by default", () => {
  assert.equal(recordCardReviewEnabled({}), false);
  assert.equal(recordCardReviewEnabled({ ENABLE_RECORD_CARD_REVIEW: "1" }), true);
  assert.equal(recordCardReviewEnabled({ ENABLE_RECORD_CARD_REVIEW: "1", VERCEL: "1" }), false);
  assert.equal(recordCardReviewEnabled({ ENABLE_RECORD_CARD_REVIEW: "1", VERCEL_ENV: "production" }), false);
});
