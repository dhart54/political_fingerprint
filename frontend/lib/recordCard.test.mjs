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
  assert.equal(assistance.explanation, assistance.explanation_lines.join("\n\n"));
  assert.equal(assistance.explanation_lines.length, 5);
  assert.match(assistance.explanation_lines[0], /whole measure also covered other purposes/);
  assert.match(assistance.explanation_lines[1], /different accounts through different mechanisms/);
  assert.match(assistance.explanation_lines[3], /funds in the bill from being used for Israel\. The same amendment reduced the Foreign Military Financing account by \$3\.3 billion/);
});

test("all-scope coverage stays 119th-Congress bounded and has no invented cutoff", async () => {
  const model = await projectRecordCard({ ...args, scope: "all", payload: snapshot[`${candidate.legislator_id}:all:editorial`].body });
  assert.equal(model.status, "ready");
  assert.equal(model.scope, "all");
  assert.equal(model.evidenceCoverage.find((c) => c.issue_id === "NATIONAL_SECURITY_FOREIGN").cutoff, "2026-07-23");
  assert.deepEqual(model.evidenceCoverage.filter((c) => c.cutoff === null).map((c) => c.issue_id), ["EDUCATION_WORKFORCE", "ENVIRONMENT_ENERGY", "JUSTICE_PUBLIC_SAFETY"]);
  for (const coverage of model.evidenceCoverage) {
    const source = snapshot[`${candidate.legislator_id}:all:editorial`].body.presentations.find((p) => p.issue_id === coverage.issue_id);
    assert.equal(coverage.source_field, "scope_boundary");
    assert.equal(coverage.source_text, source.scope_boundary);
    assert.equal(coverage.source_sha256, await contentHash(source.scope_boundary));
    if (coverage.cutoff) assert.ok(coverage.source_text.includes(`through ${coverage.cutoff_label}.`));
    else assert.equal(coverage.status, "unspecified_in_bound_review_scope");
    assert.notEqual(coverage.cutoff, candidate.generated_at);
    assert.notEqual(coverage.cutoff, candidate.snapshot_captured_at);
  }
  assert.equal(model.reviewedDomains.length, 4);
  assert.ok(model.entries.every((e) => e.reviewedScope === "119th Congress"));
});

test("coverage source mismatches fail closed rather than supplying a shared cutoff", async () => {
  const wrong = structuredClone(candidate);
  wrong.sources[0].evidence_coverage["119"].source_text = wrong.sources[3].evidence_coverage["119"].source_text;
  assert.equal((await projectRecordCard({ ...args, candidate: wrong })).status, "source_mismatch");
});

test("Education's exact accepted typed semantics do not override its deliberate display restriction", async () => {
  const traces = JSON.parse(fs.readFileSync(path.join(root, "docs/review_packets/record_at_a_glance_v1/education_direction_review.json")));
  assert.deepEqual(traces.map((t) => t.typed_semantic_direction), ["opposition", "support"]);
  for (const trace of traces) {
    const docs = {};
    for (const ref of trace.references) {
      docs[ref.role] = JSON.parse(fs.readFileSync(path.join(root, ref.path)));
      assert.equal(await contentHash(docs[ref.role]), ref.document_sha256);
    }
    assert.equal(docs.semantics.findings_subject_sha256, "795027fdcf49a4956b99804be9d44ec7bd233877e4bc76caa4121f7b61df169d");
    const semantic = docs.semantics.subject.accepted_proposition_records.find((r) => r.proposition_id === trace.semantic_source_id);
    const wording = docs.wording.subject.accepted_wording_records.find((r) => r.wording_item_id === trace.finding_id);
    const finding = payload.presentations.find((p) => p.issue_id === "EDUCATION_WORKFORCE").repeated_patterns.find((r) => r.wording_item_id === trace.finding_id);
    assert.equal(await contentHash(semantic), trace.semantic_record_sha256);
    assert.equal(await contentHash(wording), trace.accepted_wording_sha256);
    assert.equal(await contentHash(finding), trace.finding_sha256);
    assert.deepEqual(finding.semantic_source_ids, [trace.semantic_source_id]);
    assert.deepEqual(semantic.evidence_action_ids, finding.action_ids);
    assert.equal(semantic.direction, trace.typed_semantic_direction);
    assert.equal(wording.direction_display, null);
    assert.equal(docs.display.subject.presentation_accounting.directionless_repeated_patterns, 2);
    assert.equal(finding.show_direction, false);
    assert.equal(trace.candidate_direction_projection, null);
    const override = structuredClone(candidate);
    override.entries[0] = { ...override.entries[0], issue_id: "EDUCATION_WORKFORCE", field: "repeated_patterns", finding_id: trace.finding_id, finding_sha256: trace.finding_sha256, action_ids: trace.action_ids, section: trace.typed_semantic_direction };
    assert.equal((await projectRecordCard({ ...args, candidate: override })).status, "source_mismatch");
  }
});

test("new wording context resolves exact existing receipts and complete country component findings", async () => {
  for (const binding of candidate.wording_source_bindings) {
    const source = binding.source_resource
      ? snapshot[binding.source_resource].body.evidence.find((r) => r.canonical_action_id === binding.action_id).governed_receipt_projection
      : payload.presentations.find((p) => p.issue_id === binding.issue_id)[binding.source_finding_id.includes(":pattern:") ? "repeated_patterns" : "notable_choices"].find((r) => r.wording_item_id === binding.source_finding_id);
    assert.equal(await contentHash(source), binding.source_sha256);
    assert.deepEqual(binding.source, source);
    const entry = candidate.entries.find((e) => e.finding_id === binding.finding_id);
    for (const action of binding.action_id ? [binding.action_id] : source.action_ids) assert.ok(entry.action_ids.includes(action));
  }
  const waiver = candidate.entries.find((e) => e.finding_id === "wording:pattern:california-emissions-waivers");
  assert.match(waiver.explanation, /let California apply its own vehicle-emissions standards/);
  assert.match(waiver.explanation, /Omnibus Low NOX regulation and Advanced Clean Cars II/);
  assert.match(waiver.explanation, /do not show support for every part/);
  for (const entry of candidate.entries) {
    assert.match(entry.evidence_label, new RegExp(`^Based on ${entry.action_ids.length} House votes`));
    assert.notEqual(entry.headline, entry.explanation);
    assert.ok(["See the votes", "Compare the proposals"].includes(entry.link_label));
  }
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
