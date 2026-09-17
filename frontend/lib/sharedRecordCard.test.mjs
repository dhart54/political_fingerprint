import assert from "node:assert/strict";
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import test from "node:test";
import { buildSharedRecordCard, projectSharedRecordCard, sourceCoverage, CARD_POLICY } from "./sharedRecordCard.mjs";
import { contentHash, resolveCardFinding } from "./recordCard.mjs";
import { issuePresentationStatus } from "./editorialPresentation.mjs";

const snapshot = JSON.parse(gunzipSync(fs.readFileSync(new URL("../../docs/editorial/publication_replacements/m15b_green_activation_execution/after-justice-live.json.gz", import.meta.url))));
const original = snapshot["leg_valerie_p_foushee:119:editorial"].body;
const args = (payload = structuredClone(original)) => ({ payload, legislatorId: original.legislator_id, memberBioguideId: original.member_bioguide_id, scope: "119" });
const run = (payload) => buildSharedRecordCard(args(payload));
function sparse(issue) {
  const payload = structuredClone(original);
  for (const p of payload.presentations) if (p.issue_id !== issue) { p.review_state = null; p.tier = "receipts_only"; }
  return payload;
}

test("substantive determinism, response order and observational timestamps", async () => {
  const payload = structuredClone(original), first = await run(payload);
  assert.equal(first.status, "ready");
  assert(first.openingWords <= CARD_POLICY.wordBudget);
  assert.deepEqual(payload, original);
  payload.captured_at = "2099-01-01";
  payload.presentations.reverse();
  for (const p of payload.presentations) { p.generated_at = "2099-02-02"; for (const field of ["syntheses", "repeated_patterns", "policy_trajectories", "notable_choices"]) p[field]?.reverse(); }
  assert.deepEqual(await run(payload), first);
});

test("complete published actions and contextual components preserve exact receipts and all qualifications", async () => {
  const model = await run();
  for (const entry of model.entries) {
    assert.equal(entry.finding_sha256, await contentHash(entry.sourceFinding));
    assert.deepEqual(entry.action_ids, entry.sourceFinding.action_ids);
    for (const action of entry.action_ids) assert(snapshot[`${original.legislator_id}:119:${entry.issue_id}`].body.evidence.some((row) => row.canonical_action_id === action));
    for (const binding of entry.source_bindings) {
      const p = original.presentations.find((p) => p.issue_id === binding.issue_id);
      const finding = p[binding.field].find((f) => (f.wording_item_id || f.proposition_id) === binding.finding_id);
      assert(entry.detail_paragraphs.includes(finding.primary_sentence || finding.body));
      for (const limit of finding.limitations || []) { assert(entry.explanation.includes(limit)); assert(entry.detail_paragraphs.includes(limit)); }
    }
  }
  const assistance = model.entries.find((e) => e.finding_id === "wording:synthesis:security-assistance");
  assert.equal(assistance.action_ids.length, 8);
  assert.equal(assistance.source_bindings.length, 5);
  for (const country of ["Ukraine", "Jordan", "Taiwan", "Israel"]) assert(assistance.detail_paragraphs.join(" ").includes(country));
  assert(assistance.detail_paragraphs.join(" ").includes("$3.3 billion"));
});

test("directionless display is preserved; sparse paired Education finding remains atomic", async () => {
  const model = await run(sparse("EDUCATION_WORKFORCE"));
  assert.equal(model.entries.length, 3);
  assert.equal(model.entries.filter((e) => e.section === "neutral").length, 2);
  const mixed = model.entries.find((e) => e.section === "mixed");
  assert.deepEqual(mixed.action_ids, ["house:119:1:79", "house:119:1:83"]);
  assert(mixed.detail_paragraphs.join(" ").includes("whole package"));
  assert.deepEqual(model.reviewedDomains, ["EDUCATION_WORKFORCE"]);
});

test("scope boundaries preserve known and genuinely unspecified cutoffs", async () => {
  const model = await run();
  assert.equal(model.evidenceCoverage.find((p) => p.issue_id === "NATIONAL_SECURITY_FOREIGN").cutoff, "2026-07-23");
  assert(model.evidenceCoverage.filter((p) => p.issue_id !== "NATIONAL_SECURITY_FOREIGN").every((p) => p.cutoff === null));
  const all = snapshot["leg_valerie_p_foushee:all:editorial"].body;
  assert.deepEqual((await buildSharedRecordCard({ ...args(all), scope: "all" })).reviewedScopes, ["119"]);
  const unspecified = { issue_id: "X", reviewed_scope: "119", scope_boundary: "Reviewed 119th Congress.", captured_at: "2026-09-17" };
  assert.equal((await sourceCoverage(unspecified)).cutoff, null);
  const binding = { cutoff: "2026-07-23", source_field: "scope_boundary", source_text: unspecified.scope_boundary, source_sha256: await contentHash(unspecified.scope_boundary) };
  assert.equal((await sourceCoverage({ ...unspecified, evidence_coverage: binding })).cutoff, "2026-07-23");
  await assert.rejects(sourceCoverage({ ...unspecified, evidence_coverage: { ...binding, cutoff: "2026-02-30" } }));
  const changed = structuredClone(original);
  changed.presentations[2].evidence_coverage = binding;
  assert.equal((await run(changed)).status, "source_mismatch");
});

test("actual unsupported contextual projection is one semantic exception; independent entries survive", async () => {
  const model = await run();
  assert.equal(model.exceptions.length, 1);
  assert.match(model.exceptions[0].reason, /Contextual actions were excluded/);
  assert(!model.entries.some((e) => e.finding_id.includes("war-powers")));
  assert(model.omissions.some((o) => o.category === "limited_space"));
  const payload = structuredClone(original);
  for (const p of payload.presentations) if (!["JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY_FOREIGN"].includes(p.issue_id)) { p.review_state = null; p.tier = "receipts_only"; }
  assert((await run(payload)).omissions.some((o) => o.category === "actual_overlap" && o.shared_action_ids.length === 2));
});

test("mismatched cached card and old deep link cannot suppress valid current issue presentations", async () => {
  const old = await run(), payload = structuredClone(original);
  payload.presentations.find((p) => p.issue_id === "EDUCATION_WORKFORCE").repeated_patterns[0].primary_sentence += " Test revision.";
  assert.equal(issuePresentationStatus(payload, args(), "119"), "ready");
  assert.equal((await projectSharedRecordCard(args(payload), old)).status, "source_mismatch");
  const updated = await run(payload);
  assert.notEqual(updated.sourceFingerprint, old.sourceFingerprint);
  assert(updated.entries.find((e) => e.issue_id === "EDUCATION_WORKFORCE").detail_paragraphs.some((text) => text.includes("Test revision.")));
  const oldEntry = old.entries.find((e) => e.issue_id === "EDUCATION_WORKFORCE");
  assert.equal(resolveCardFinding(updated, oldEntry.issue_id, oldEntry.finding_id, oldEntry.sourcePresentationHash), null);
  assert(updated.entries.length > 0);
});

test("raw ledger changes cannot extend finding actions, wording or cutoffs", async () => {
  const first = await run();
  const isolated = structuredClone(snapshot);
  isolated[`${original.legislator_id}:119:JUSTICE_PUBLIC_SAFETY`].body.evidence.push({ canonical_action_id: "house:119:2:999", date: "2099-01-01" });
  assert.deepEqual(await run(isolated["leg_valerie_p_foushee:119:editorial"].body), first);
});

test("no-summary, unavailable, identity, scope and unsupported are distinct", async () => {
  const massie = snapshot["leg_thomas_massie:119:editorial"].body;
  assert.equal((await buildSharedRecordCard({ payload: massie, legislatorId: massie.legislator_id, memberBioguideId: massie.member_bioguide_id, scope: "119" })).status, "empty");
  assert.equal((await buildSharedRecordCard({ ...args(), requestStatus: "error" })).status, "error");
  assert.equal((await buildSharedRecordCard({ ...args(), requestStatus: "loading" })).status, "loading");
  assert.equal((await buildSharedRecordCard({ ...args(), memberBioguideId: "WRONG" })).status, "identity_mismatch");
  assert.equal((await buildSharedRecordCard({ ...args(), scope: "118" })).status, "identity_mismatch");
  const payload = sparse("EDUCATION_WORKFORCE");
  for (const item of [...payload.presentations[2].repeated_patterns, ...payload.presentations[2].notable_choices]) item.action_ids = [];
  assert.equal((await run(payload)).status, "representation_unavailable");
});

test("malformed action, duplicate ID, incomplete domain and missing relationship reject safely", async () => {
  let payload = structuredClone(original);
  payload.presentations.pop();
  assert.equal((await run(payload)).status, "incomplete");
  payload = sparse("EDUCATION_WORKFORCE");
  payload.presentations[2].notable_choices[0].action_ids.push("house:118:1:79");
  assert((await run(payload)).exceptions.some((e) => e.reason.includes("Congress")));
  payload = structuredClone(original);
  const ns = payload.presentations.find((p) => p.issue_id === "NATIONAL_SECURITY_FOREIGN");
  ns.notable_choices = ns.notable_choices.filter((f) => f.wording_item_id !== "wording:notable:israel-fmf-reduction");
  const model = await run(payload);
  assert(!model.entries.some((e) => e.finding_id === "wording:synthesis:security-assistance"));
  assert(!model.entries.some((e) => /ukraine-assistance|jordan-assistance|taiwan-funding/.test(e.finding_id)));
  assert(model.exceptions.some((e) => /Missing or ambiguous/.test(e.reason)));
  payload = sparse("EDUCATION_WORKFORCE");
  payload.presentations[2].repeated_patterns.push(payload.presentations[2].repeated_patterns[0]);
  assert.equal((await run(payload)).status, "source_mismatch");
});
