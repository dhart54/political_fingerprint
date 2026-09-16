// Offline, read-only projection of the verified post-M15B public snapshot.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import { contentHash, findingIdentity, FINDING_FIELDS, suppliedDirection } from "../frontend/lib/recordCard.mjs";
import { DOMAIN_ORDER } from "../frontend/lib/issueEvidenceCoverage.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourcePath = "docs/editorial/publication_replacements/m15b_green_activation_execution";
const out = path.join(root, "docs/review_packets/record_at_a_glance_v1");
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, sourcePath, name), "utf8"));
const bytes = fs.readFileSync(path.join(root, sourcePath, "after-justice-live.json.gz"));
const snapshotHash = createHash("sha256").update(bytes).digest("hex");
if (snapshotHash !== read("file_manifest.json")["after-justice-live.json.gz"]) throw Error("Snapshot bytes differ from verified manifest");
const snapshot = JSON.parse(gunzipSync(bytes));
const audit = JSON.parse(gunzipSync(fs.readFileSync(path.join(root, sourcePath, "production_audits.json.gz"))))["after-justice"];
const member = "leg_valerie_p_foushee";
const presentations = snapshot[`${member}:119:editorial`].body.presentations;

// Authored choices, in stable domain order within each descriptive section.
const selections = [
  ["JUSTICE_PUBLIC_SAFETY", "prop:d7e189366b477118", "support", "A terrorism-response exercise and threat assessment", "A cold-weather response exercise and an assessment of vehicular-terrorism threats.", "Adds a specific preparedness choice; the same two actions in National Security are not counted again."],
  ["NATIONAL_SECURITY_FOREIGN", "wording:synthesis:war-powers", "support", "Removing U.S. forces from specified hostilities", "Nine country-specific War Powers resolutions covered hostilities involving Iran, Lebanon and Venezuela; their wording and timing differed.", "Keeps the accepted cross-country War Powers finding together; pairs it with the assistance contrast to avoid implying one position on all foreign involvement."],
  ["ENVIRONMENT_ENERGY", "wording:pattern:california-emissions-waivers", "opposition", "Overturning two California vehicle-emissions waivers", "The resolutions targeted separate EPA waiver decisions; these votes do not show support for every part of the underlying rules.", "Concrete, understandable disapproval choice; avoids presenting the overlapping 13-resolution synthesis as separate corroboration."],
  ["JUSTICE_PUBLIC_SAFETY", "prop:354da734fec2fcf6", "opposition", "Replacing or repealing specific D.C. public-safety rules", "The reviewed proposals concerned youth cases, police bargaining and pursuits, pretrial detention, and policing reforms.", "Names the specific objects of the accepted D.C. finding and adds information distinct from preparedness."],
  ["EDUCATION_WORKFORCE", "m14f:notable:hr1048_substitute_final", "mixed", "College foreign-gift reporting: replacement supported, final package opposed", "The replacement set reporting, disclosure and compliance rules; the broader final H.R. 1048 package also restricted contracts, and the final vote does not identify which part she opposed.", "Preserves the necessary paired amendment/package choices and the whole-package limitation."],
  ["NATIONAL_SECURITY_FOREIGN", "wording:synthesis:security-assistance", "mixed", "Security assistance differed by country and proposal", null, "Retains the complete accepted country-specific contrast, including Israel, rather than picking one country or splitting it into support/opposition rows."],
];
const sources = [];
const inventory = [];
for (const issue of DOMAIN_ORDER) {
  const p = presentations.find((p) => p.issue_id === issue);
  if (!p?.review_state || p.tier === "receipts_only") continue;
  const registry = audit.registry.find((r) => r.member_bioguide_id === "F000477" && r.issue_id === issue);
  const metadata = registry.publication_metadata_jsonb;
  const source = { issue_id: issue, published_artifact_id: registry.artifact_id, published_natural_key: metadata.presentation_natural_key, artifact_version: metadata.presentation_artifact_version, content_sha256: metadata.active_artifact_sha256, lineage_provenance: p.provenance, presentation_sha256: {} };
  for (const scope of ["119", "all"]) source.presentation_sha256[scope] = await contentHash(snapshot[`${member}:${scope}:editorial`].body.presentations.find((p) => p.issue_id === issue));
  sources.push(source);
  for (const field of FINDING_FIELDS) for (const item of p[field] || []) {
    const selected = selections.find((s) => s[0] === issue && s[1] === findingIdentity(item));
    const receiptEpisodeBindings = (p.exact_action_receipts || []).filter((r) => item.action_ids.includes(r.canonical_action_id) && r.episode_id).map((r) => ({ action_id: r.canonical_action_id, episode_id: r.episode_id }));
    inventory.push({ issue_id: issue, field, finding_id: findingIdentity(item), finding_sha256: await contentHash(item), source, interpreted_direction: suppliedDirection(item), action_ids: item.action_ids, episode_ids: item.episode_ids ?? null, episode_count: item.episode_ids?.length ?? null, supplied_receipt_episode_bindings: receiptEpisodeBindings, scope: p.review_state, scope_boundary: p.scope_boundary, presentation_limitations: p.limitations, accepted_finding: item, selected: Boolean(selected), rationale: selected?.[5] || omissionReason(issue, item) });
  }
}
const entries = selections.map(([issue, id, section, headline, explanation, rationale]) => {
  const row = inventory.find((r) => r.issue_id === issue && r.finding_id === id);
  if (!row || row.interpreted_direction !== section) throw Error(`No supplied direction: ${id}`);
  return { id: `record-card-${entriesSafeId(id)}`, issue_id: issue, field: row.field, finding_id: id, finding_sha256: row.finding_sha256, section, headline, explanation: explanation ?? row.accepted_finding.primary_sentence, action_ids: row.action_ids, episode_ids: row.episode_ids, episode_count: row.episode_count, evidence_label: row.accepted_finding.evidence_count_label || `${row.action_ids.length} supporting House votes`, material_limitations: row.accepted_finding.limitations || [], rationale };
});
const generatedAt = process.argv.includes("--check") ? JSON.parse(fs.readFileSync(path.join(out, "candidate.json"))).generated_at : new Date().toISOString();
const candidate = { status: "candidate", version: 1, legislator_id: member, member_bioguide_id: "F000477", scopes: ["119", "all"], generated_at: generatedAt, evidence_cutoff: null, evidence_cutoff_note: "The reviewed findings specify the 119th Congress; a precise review/evidence cutoff is not supplied. Snapshot capture and card generation are not evidence cutoffs.", source_snapshot: `${sourcePath}/after-justice-live.json.gz`, source_snapshot_sha256: snapshotHash, snapshot_captured_at: audit.captured_at_utc, sources, entries };
const uniqueActions = [...new Set(entries.flatMap((e) => e.action_ids))];
const packet = { candidate_status: "pending_product_review", candidate, eligible_inventory: inventory, reviewed_domain_count: sources.length, available_domain_count: DOMAIN_ORDER.length, selected_unique_actions: uniqueActions, selected_action_mentions: entries.reduce((n, e) => n + e.action_ids.length, 0), independent_evidence_score: null, material_omission_review: "This selection is not a domain summary. It omits Education's bargaining and China-linked funding findings, Environment's appliance/BLM findings, Justice's firearm and fraud-enforcement patterns and mixed HALT episode, and additional National Security choices. Those are material to any overall issue or political verdict, which this card does not offer. All are visible in the full issue record. The assistance contrast remains complete; no country exception is dropped. The two preparedness actions recur in both domains and appear only once here. War Powers component patterns and the environmental synthesis overlap selected actions and are not independent corroboration. Education's undirected pattern fields remain undirected; prose is not parsed to classify them." };
fs.mkdirSync(out, { recursive: true });
const inventoryText = "# Eligible presentation inventory\n\nAll current reviewed presentation items, including overlapping syntheses and component findings. Direction is supplied typed data; missing direction remains missing. Complete text, source hashes, scope, limitations and explicit episode bindings are in [inventory.json](inventory.json).\n\n| Issue | Accepted finding | Direction | Selection and rationale |\n|---|---|---|---|\n" + inventory.map((row) => `| ${row.issue_id} | ${row.accepted_finding.public_title || row.accepted_finding.title || row.accepted_finding.heading} | ${row.interpreted_direction || "Not supplied"} | **${row.selected ? "Selected" : "Omitted"}** — ${row.rationale} |`).join("\n") + "\n";
for (const [name, data] of [["candidate.json", candidate], ["inventory.json", packet], ["inventory.md", inventoryText]]) {
  const output = typeof data === "string" ? data : `${JSON.stringify(data, null, 2)}\n`;
  const target = path.join(out, name);
  if (process.argv.includes("--check")) {
    if (fs.readFileSync(target, "utf8").replaceAll("\r\n", "\n") !== output) throw Error(`${name} drift`);
  } else fs.writeFileSync(target, output);
}
console.log(`${inventory.length} inventoried findings; ${entries.length} selected; ${sources.length} reviewed domains; ${uniqueActions.length} unique supporting actions. No publication changes.`);

function entriesSafeId(id) { return id.replace(/[^a-z0-9]+/gi, "-"); }
function omissionReason(issue, item) {
  const id = findingIdentity(item);
  if (issue === "EDUCATION_WORKFORCE") return "Accepted wording retained in inventory and issue view; typed direction is absent, so V1 does not infer a section from prose. Distinct bargaining/funding choices are omitted, not summarized by the selected package contrast.";
  if (issue === "ENVIRONMENT_ENERGY") return "The disapproval synthesis overlaps the selected waiver actions; appliance and BLM patterns add distinct detail available in the full issue. No claim is made about the whole domain.";
  if (issue === "JUSTICE_PUBLIC_SAFETY") return "Distinct firearm/fraud or mixed HALT evidence remains in the full issue; these omissions prevent treating this small selection as a comprehensive Justice position.";
  if (/war-powers|terrorism-preparedness|jordan-assistance|ukraine-assistance|israel-fmf|taiwan-funding/.test(id)) return "Overlaps a selected accepted finding or the same preparedness actions selected under Justice; avoid evidence inflation and preserve the whole country-specific contrast.";
  return "Separate concrete choice available in the full issue; omitted for bounded first-minute length, not low evidence or political importance. Does not contradict the exact selected policy objects.";
}
