// Offline proof using actual publication responses. Never changes upstream artifacts.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";
import { buildSharedRecordCard, CARD_POLICY, substantiveInput } from "../frontend/lib/sharedRecordCard.mjs";
import { contentHash } from "../frontend/lib/recordCard.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dir = "docs/editorial/publication_replacements/m15b_green_activation_execution";
const read = (file) => fs.readFileSync(path.join(root, file));
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const manifest = JSON.parse(read(`${dir}/file_manifest.json`));
function snapshot(name) {
  const bytes = read(`${dir}/${name}.json.gz`);
  assert.equal(sha(bytes), manifest[`${name}.json.gz`], `Immutable snapshot ${name}`);
  return JSON.parse(gunzipSync(bytes));
}
function args(payload) { return { payload, legislatorId: payload.legislator_id, memberBioguideId: payload.member_bioguide_id, scope: payload.scope }; }
const key = "leg_valerie_p_foushee:119:editorial";
const after = snapshot("after-justice-live");
const reference = await buildSharedRecordCard(args(after[key].body));
assert.equal(reference.status, "ready");
assert.deepEqual(reference, await buildSharedRecordCard(args(after[key].body)));
const timestampOnly = structuredClone(after[key].body);
timestampOnly.captured_at = "2099-01-01";
timestampOnly.presentations.forEach((p) => { p.generated_at = "2099-01-02"; });
assert.deepEqual(reference, await buildSharedRecordCard(args(timestampOnly)));

// Historical authorized update replay; no expected card or selected IDs supplied.
const before = snapshot("before-live");
const prior = await buildSharedRecordCard(args(before[key].body));
// Separately reserved intermediate source set, first evaluated after the shared
// forms and relationship-failure handling were fixed. Same policy, no fitting.
const heldAside = await buildSharedRecordCard(args(snapshot("after-ns-live")["leg_valerie_p_foushee:all:editorial"].body));
assert.equal(heldAside.status, "ready");
assert.notEqual(prior.sourceFingerprint, reference.sourceFingerprint);
const visible = (model) => model.entries.map(({ headline, explanation, action_ids, detail_paragraphs }) => ({ headline, explanation, action_ids, detail_paragraphs }));
const findingIds = (p) => ["syntheses", "repeated_patterns", "policy_trajectories", "notable_choices"].flatMap((f) => (p[f] || []).map((item) => item.wording_item_id || item.proposition_id));
const changes = [];
for (const p of after[key].body.presentations) {
  const old = before[key].body.presentations.find((row) => row.issue_id === p.issue_id);
  const oldHash = await contentHash(substantiveInput(old));
  const newHash = await contentHash(substantiveInput(p));
  if (oldHash !== newHash) changes.push({ issue_id: p.issue_id, before_sha256: oldHash, after_sha256: newHash, before_findings: findingIds(old).length, after_findings: findingIds(p).length, removed_finding_ids: findingIds(old).filter((id) => !findingIds(p).includes(id)), added_finding_ids: findingIds(p).filter((id) => !findingIds(old).includes(id)) });
}
assert(changes.length > 0);
const catalog = JSON.parse(read("backend/app/editorial_presentations/public_review_state_catalog_v1.json"));
const catalogMembers = [...new Set(catalog.entries.map((e) => e.member_id))].sort();
const upstream = JSON.parse(read("docs/editorial/shared_corpora/house_119_v1/issue_mappings/justice_public_safety_v1/m14a_parity_proof.json"));
const massie = await buildSharedRecordCard(args(after["leg_thomas_massie:119:editorial"].body));
assert.equal(massie.status, "empty");
const intervention = { new_shared_meaning: 0, new_presentation_rules: 0, member_specific_edits: 0, manual_selections: 0, additional_upstream_approvals: 0 };
const summarize = async (model) => ({ status: model.status, substantive_output_sha256: await contentHash(model), source_fingerprint: model.sourceFingerprint, selected: model.entries.map((e) => ({ issue_id: e.issue_id, finding_id: e.finding_id, actions: e.action_ids, section: e.section })), opening_words: model.openingWords, exceptions: model.exceptions, omissions: model.omissions, evidence_coverage: model.evidenceCoverage });
const report = {
  status: "implementation_candidate_reuse_proof_blocked", policy: CARD_POLICY,
  policy_module_sha256: sha(read("frontend/lib/sharedRecordCard.mjs").toString().replaceAll("\r\n", "\n")), policy_document_sha256: sha(read("docs/review_packets/record_card_reproducibility_policy.md").toString().replaceAll("\r\n", "\n")),
  input_authority: "Actual archived publication-gated responses from the authorized M15B activation; candidate card rules confer no additional approval.",
  snapshots: Object.fromEntries(["before-live.json.gz", "after-ns-live.json.gz", "after-justice-live.json.gz", "decision_source.json", "execution_record.json"].map((name) => [name, manifest[name]])),
  reference: await summarize(reference), held_aside: await summarize(heldAside),
  update_replay: { from: "before-live", to: "after-justice-live", changes, changed_card_output: await contentHash(prior) !== await contentHash(reference), visible_selected_copy_changed: await contentHash(visible(prior)) !== await contentHash(visible(reference)), result: "The authorized upstream replacement removed an omitted NS trajectory and refreshed NS/Justice sources. Selection and visible selected copy remain identical; their source bindings and finding URLs refresh mechanically. This is not evidence of a historical selected-copy revision. Controlled tests separately verify revised source text propagates immediately.", unchanged_repeat_identical: true, capture_generation_time_invariant: true, interventions: intervention },
  held_aside_input: "after-ns-live / leg_valerie_p_foushee:all:editorial (intermediate authorized replacement state; explicit reviewed-119 boundary)",
  second_member: { completed_nonempty_card: false, public_catalog_members: catalogMembers, actual_massie_public_response_status: massie.status, real_upstream_member: "G000576 (Glenn Grothman)", upstream_proof: "docs/editorial/shared_corpora/house_119_v1/issue_mappings/justice_public_safety_v1/m14a_parity_proof.json", upstream_proof_sha256: await contentHash(upstream), dependency: "An IR-native reviewed finding/presentation for G000576 (or another real second member), with content-bound accepted wording/display permissions and complete source/action mappings. Existing Grothman shared-corpus propositions are detached compiler proof, not eligible reviewed public findings. No new member approval or publication was created." },
  interventions: { implementation: "One shared policy/form proposal and implementation; zero new shared legislative meanings, member edits, or authored selection arrays. Consolidated policy review and later adoption authorization remain required.", reference: intervention, held_aside: intervention, unchanged_repeat: intervention, second_member: "Blocked upstream; not counted as successful reuse." },
};
const output = `${JSON.stringify(report, null, 2)}\n`;
const target = path.join(root, "docs/review_packets/record_card_reproducibility_results.json");
if (process.argv.includes("--check")) assert.equal(fs.readFileSync(target, "utf8").replaceAll("\r\n", "\n"), output);
else fs.writeFileSync(target, output);
console.log(JSON.stringify({ reference_entries: reference.entries.length, held_aside_entries: heldAside.entries.length, changed_issues: changes.map((c) => c.issue_id), exceptions: reference.exceptions, second_member: report.second_member.dependency }, null, 2));
