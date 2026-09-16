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

// Read accepted references, never regenerate or change the published presentation.
const educationPaths = {
  semantics: "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1/accepted_behavioral_findings.json",
  wording: "docs/editorial/public_wording_candidates/f000477_education_workforce_m14f_v1/accepted_public_copy.json",
  display: "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/human_site_integration_authority.json",
};
const educationDocs = Object.fromEntries(Object.entries(educationPaths).map(([key, file]) => [key, JSON.parse(fs.readFileSync(path.join(root, file), "utf8"))]));
if (!educationDocs.semantics.internal_analytical_authority || !educationDocs.wording.accepted || educationDocs.display.subject.decision !== "accept_as_rendered" || educationDocs.display.subject.presentation_accounting.directionless_repeated_patterns !== 2) throw Error("Education acceptance boundary changed");
const educationDirectionReview = [];
for (const item of presentations.find((p) => p.issue_id === "EDUCATION_WORKFORCE").repeated_patterns) {
  const semantic = educationDocs.semantics.subject.accepted_proposition_records.find((r) => item.semantic_source_ids.includes(r.proposition_id));
  const wording = educationDocs.wording.subject.accepted_wording_records.find((r) => r.wording_item_id === findingIdentity(item));
  if (!semantic || !wording || JSON.stringify(semantic.evidence_action_ids) !== JSON.stringify(item.action_ids) || wording.direction_display !== null || item.show_direction !== false || suppliedDirection(item) !== null) throw Error("Education direction trace changed");
  educationDirectionReview.push({ finding_id: findingIdentity(item), finding_sha256: await contentHash(item), semantic_source_id: semantic.proposition_id, typed_semantic_direction: semantic.direction, action_ids: semantic.evidence_action_ids, semantic_record_sha256: await contentHash(semantic), accepted_wording_sha256: await contentHash(wording), accepted_wording_subject_sha256: item.mapping.wording_item_subject_sha256, references: await Promise.all(Object.entries(educationPaths).map(async ([key, file]) => ({ role: key, path: file, document_sha256: await contentHash(educationDocs[key]) }))), disposition: "intentional_presentation_restriction", candidate_direction_projection: null, reason: "M14F deliberately supplies no direction display for non-mixed behavioral findings; M14G's accept-as-rendered authority explicitly retains two directionless patterns. Typed meaning exists upstream, but assigning a Supported/Opposed card section would override that accepted display restriction. No such override is authorized here." });
}

const assistanceLines = [
  "Ukraine: Opposed three aid restrictions with different scopes; supported a measure authorizing support for Ukraine. That whole measure also covered other purposes, so the vote does not isolate every provision.",
  "Jordan: Opposed two proposals to cut or restrict assistance, affecting different accounts through different mechanisms.",
  "Taiwan: Opposed removing funding for the Taiwan Security Cooperation Initiative.",
  "Israel: Supported an amendment barring funds in the bill from being used for Israel. The same amendment reduced the Foreign Military Financing account by $3.3 billion.",
  "The Israel and Taiwan amendments are individual choices, not recurring country patterns. These choices do not establish one uniform position on assistance across countries.",
];

// Authored choices, in stable domain order within each descriptive section.
const selections = [
  ["JUSTICE_PUBLIC_SAFETY", "prop:d7e189366b477118", "support", "Two terrorism-preparedness requirements", "One required a cold-weather response exercise; the other required an assessment of vehicular-terrorism threats.", "Distinct mechanisms: a concrete exercise/assessment pair makes the accepted preparedness finding understandable in one short entry. Its actions are distinct from D.C. rule changes; the identical National Security actions appear only here."],
  ["NATIONAL_SECURITY_FOREIGN", "wording:synthesis:war-powers", "support", "Removing U.S. forces from specified hostilities", "Nine country-specific War Powers resolutions covered hostilities involving Iran, Lebanon and Venezuela; their wording and timing differed.", "Keeps the accepted cross-country War Powers finding together; pairs it with the assistance contrast to avoid implying one position on all foreign involvement."],
  ["ENVIRONMENT_ENERGY", "wording:pattern:california-emissions-waivers", "opposition", "Overturning two California vehicle-emissions waivers", "The EPA waivers let California apply its own vehicle-emissions standards: the Omnibus Low NOX regulation and Advanced Clean Cars II. The resolutions would overturn those permissions; these votes do not show support for every part of either rule.", "Distinct mechanism: two identified permissions can be explained together while retaining both decisions. The broader disapproval synthesis includes these same actions and would add a second layer of generalization."],
  ["JUSTICE_PUBLIC_SAFETY", "prop:354da734fec2fcf6", "opposition", "Replacing or repealing specific D.C. public-safety rules", "The reviewed proposals concerned youth cases, police bargaining and pursuits, pretrial detention, and policing reforms.", "Names the specific objects of the accepted D.C. finding and adds information distinct from preparedness."],
  ["EDUCATION_WORKFORCE", "m14f:notable:hr1048_substitute_final", "mixed", "College foreign-gift reporting: replacement supported, final package opposed", "She supported an amendment to replace the bill's text with reporting thresholds, searchable disclosures, some exclusions, and fines or compliance plans. She then opposed the broader final H.R. 1048 package, which also restricted contracts. The final vote does not identify which part she opposed.", "Necessary contextual pairing: the supported replacement and opposed final package distinguish two proposals within one episode. Keeping both prevents the package vote from implying opposition to all foreign-gift reporting; neither pattern is represented by this pair."],
  ["NATIONAL_SECURITY_FOREIGN", "wording:synthesis:security-assistance", "mixed", "Security assistance differed by country and proposal", "The reviewed choices cover Ukraine, Jordan, Taiwan and Israel; they do not establish one uniform position on assistance.", "Necessary contextual pairing: retain the complete accepted four-country contrast alongside War Powers, including Israel and Ukraine's mixed choices. Its length is warranted by the differences that would be lost by selecting a single country or direction."],
];
const sources = [];
const inventory = [];
for (const issue of DOMAIN_ORDER) {
  const p = presentations.find((p) => p.issue_id === issue);
  if (!p?.review_state || p.tier === "receipts_only") continue;
  const registry = audit.registry.find((r) => r.member_bioguide_id === "F000477" && r.issue_id === issue);
  const metadata = registry.publication_metadata_jsonb;
  const source = { issue_id: issue, published_artifact_id: registry.artifact_id, published_natural_key: metadata.presentation_natural_key, artifact_version: metadata.presentation_artifact_version, content_sha256: metadata.active_artifact_sha256, lineage_provenance: p.provenance, presentation_sha256: {} };
  // A reviewed-scope projection, not a maximum vote date or snapshot timestamp.
  const knownCutoff = issue === "NATIONAL_SECURITY_FOREIGN";
  if (knownCutoff && !p.scope_boundary.includes("through July 23, 2026.")) throw Error("National Security cutoff source changed");
  source.evidence_coverage = {};
  for (const scope of ["119", "all"]) {
    const boundary = snapshot[`${member}:${scope}:editorial`].body.presentations.find((row) => row.issue_id === issue).scope_boundary;
    if (knownCutoff && !boundary.includes("through July 23, 2026.")) throw Error("National Security scope cutoff differs");
    source.evidence_coverage[scope] = { cutoff: knownCutoff ? "2026-07-23" : null, cutoff_label: knownCutoff ? "July 23, 2026" : null, status: knownCutoff ? "specified" : "unspecified_in_bound_review_scope", source_field: "scope_boundary", source_text: boundary, source_sha256: await contentHash(boundary) };
  }
  for (const scope of ["119", "all"]) source.presentation_sha256[scope] = await contentHash(snapshot[`${member}:${scope}:editorial`].body.presentations.find((p) => p.issue_id === issue));
  sources.push(source);
  for (const field of FINDING_FIELDS) for (const item of p[field] || []) {
    const selected = selections.find((s) => s[0] === issue && s[1] === findingIdentity(item));
    const receiptEpisodeBindings = (p.exact_action_receipts || []).filter((r) => item.action_ids.includes(r.canonical_action_id) && r.episode_id).map((r) => ({ action_id: r.canonical_action_id, episode_id: r.episode_id }));
    const directionReview = educationDirectionReview.find((r) => r.finding_id === findingIdentity(item));
    const omission = selected ? null : omissionReason(issue, item);
    inventory.push({ issue_id: issue, field, finding_id: findingIdentity(item), finding_sha256: await contentHash(item), source, interpreted_direction: suppliedDirection(item), direction_review: directionReview || null, action_ids: item.action_ids, episode_ids: item.episode_ids ?? null, episode_count: item.episode_ids?.length ?? null, supplied_receipt_episode_bindings: receiptEpisodeBindings, scope: p.review_state, scope_boundary: p.scope_boundary, presentation_limitations: p.limitations, accepted_finding: item, selected: Boolean(selected), omission_category: omission?.category || null, rationale: selected?.[5] || omission.reason });
  }
}
const entries = selections.map(([issue, id, section, headline, explanation, rationale]) => {
  const row = inventory.find((r) => r.issue_id === issue && r.finding_id === id);
  if (!row || row.interpreted_direction !== section) throw Error(`No supplied direction: ${id}`);
  return { id: `record-card-${entriesSafeId(id)}`, issue_id: issue, field: row.field, finding_id: id, finding_sha256: row.finding_sha256, section, headline, explanation, ...(id === "wording:synthesis:security-assistance" ? { detail_paragraphs: assistanceLines } : {}), link_label: section === "mixed" ? "Compare the proposals" : "See the votes", action_ids: row.action_ids, episode_ids: row.episode_ids, episode_count: row.episode_count, evidence_label: `Based on ${row.action_ids.length} House votes${row.episode_count === 1 ? " · 1 legislative episode" : ""}`, material_limitations: row.accepted_finding.limitations || [], rationale };
});
const generatedAt = process.argv.includes("--check") ? JSON.parse(fs.readFileSync(path.join(out, "candidate.json"))).generated_at : new Date().toISOString();
const wordingBindings = [];
for (const [issue, ids] of [["ENVIRONMENT_ENERGY", ["house:119:1:112", "house:119:1:114"]]]) {
  for (const actionId of ids) {
    const receipt = snapshot[`${member}:119:${issue}`].body.evidence.find((r) => r.canonical_action_id === actionId).governed_receipt_projection;
    wordingBindings.push({ issue_id: issue, finding_id: "wording:pattern:california-emissions-waivers", source_resource: `${member}:119:${issue}`, source_field: "body.evidence[].governed_receipt_projection", action_id: actionId, source_sha256: await contentHash(receipt), source: receipt, wording_use: "Plain-language explanation of the bound waiver-of-preemption mechanism; the named standards identify the two permissions. No inference of support for either underlying rule." });
  }
}
const assistanceSource = presentations.find((p) => p.issue_id === "NATIONAL_SECURITY_FOREIGN");
for (const id of ["wording:pattern:ukraine-assistance", "wording:pattern:jordan-assistance", "wording:notable:taiwan-funding", "wording:notable:israel-fmf-reduction"]) {
  const row = FINDING_FIELDS.flatMap((field) => assistanceSource[field] || []).find((item) => findingIdentity(item) === id);
  if (!row.action_ids.every((action) => entries.find((entry) => entry.finding_id === "wording:synthesis:security-assistance").action_ids.includes(action))) throw Error("Assistance context is outside the selected finding");
  wordingBindings.push({ issue_id: "NATIONAL_SECURITY_FOREIGN", finding_id: "wording:synthesis:security-assistance", source_finding_id: id, source_sha256: await contentHash(row), source: row, wording_use: "Retain the component's material scope and whole-measure qualifications within the complete country contrast." });
}
const candidate = { status: "candidate", version: 1, legislator_id: member, member_bioguide_id: "F000477", scopes: ["119", "all"], generated_at: generatedAt, evidence_cutoff_note: "Per-issue cutoffs are explicitly bound to each source's scope boundary. Unspecified boundaries remain unspecified. Snapshot capture and card generation are not evidence cutoffs.", source_snapshot: `${sourcePath}/after-justice-live.json.gz`, source_snapshot_sha256: snapshotHash, snapshot_captured_at: audit.captured_at_utc, sources, entries, wording_source_bindings: wordingBindings };
const uniqueActions = [...new Set(entries.flatMap((e) => e.action_ids))];
const packet = { candidate_status: "release_review_pending", candidate, eligible_inventory: inventory, reviewed_domain_count: sources.length, available_domain_count: DOMAIN_ORDER.length, selected_unique_actions: uniqueActions, selected_action_mentions: entries.reduce((n, e) => n + e.action_ids.length, 0), independent_evidence_score: null, common_selection_considerations: ["Exact accepted policy object and bounded mechanism", "Distinct information relative to selected findings and actual action overlap", "Necessary contextual pairing and material qualifications", "Faithful representation under established presentation restrictions", "Reading cost and limited first-minute space"], selection_reconsideration: "All 28 items were reconsidered on these same qualitative grounds; no vote-count threshold, direction quota, issue quota, score or fixed entry count is used. Six entries remain after review, not to equalize sections. Education's typed meanings were traced before applying its explicit accepted display restriction; neither was judged less meaningful because presentation metadata was absent.", material_omission_review: "Distinct omitted findings remain material to any broader interpretation. Item-specific reasons below separate actual overlap, required country pairing, presentation restrictions and limited space. In particular, the Education funding finding qualifies any broader reading of its selected reporting episode, and bargaining remains independent of that episode. The overview must not stand in for those issue findings. The complete assistance contrast preserves every country, and the shared preparedness actions appear once." };
fs.mkdirSync(out, { recursive: true });
const inventoryText = "# Reviewed presentation inventory\n\nAll 28 items are considered using the same grounds: exact policy object, distinct information and actual overlap, necessary contextual pairing, faithful representation, and reading cost. There is no fixed count or section quota. Complete text, source hashes, scope, limitations and episode bindings are in [inventory.json](inventory.json). Education's accepted typed meanings and deliberate display restrictions are traced in [education_direction_review.json](education_direction_review.json).\n\n| Issue | Accepted finding | Direction available to card | Selection and rationale |\n|---|---|---|---|\n" + inventory.map((row) => `| ${row.issue_id} | ${row.accepted_finding.public_title || row.accepted_finding.title || row.accepted_finding.heading} | ${row.interpreted_direction || `Restricted (accepted semantics: ${row.direction_review?.typed_semantic_direction})`} | **${row.selected ? "Selected" : `Omitted: ${row.omission_category}`}** — ${row.rationale} |`).join("\n") + "\n";
for (const [name, data] of [["candidate.json", candidate], ["inventory.json", packet], ["inventory.md", inventoryText], ["education_direction_review.json", educationDirectionReview]]) {
  const output = typeof data === "string" ? data : `${JSON.stringify(data, null, 2)}\n`;
  const target = path.join(out, name);
  if (process.argv.includes("--check")) {
    if (fs.readFileSync(target, "utf8").replaceAll("\r\n", "\n") !== output) throw Error(`${name} drift`);
  } else fs.writeFileSync(target, output);
}
console.log(`${inventory.length} inventoried findings; ${entries.length} selected; ${sources.length} reviewed domains; ${uniqueActions.length} unique supporting actions. No publication changes.`);

// Deployable wording and exact-source bindings only. No snapshot, receipt payload,
// replay loader or new publication authority is included in the ordinary route.
// Product review: PR191 head 56a35e860783466f6079cba47f6338e2e6a09dab,
// with the user's exact assistance shortening/detail relocation instruction.
const runtimeContent = {
  status: candidate.status, version: candidate.version,
  legislator_id: member, member_bioguide_id: candidate.member_bioguide_id,
  scopes: candidate.scopes,
  sources: sources.map(({ issue_id, presentation_sha256, evidence_coverage }) => ({ issue_id, presentation_sha256, evidence_coverage })),
  entries: entries.map(({ rationale, material_limitations, ...entry }) => entry),
};
const runtimePath = path.join(root, "frontend/lib/recordCardContent.json");
const runtimeText = `${JSON.stringify(runtimeContent, null, 2)}\n`;
if (process.argv.includes("--check")) {
  if (fs.readFileSync(runtimePath, "utf8").replaceAll("\r\n", "\n") !== runtimeText) throw Error("Runtime card wording/source mapping drift");
} else fs.writeFileSync(runtimePath, runtimeText);

function entriesSafeId(id) { return id.replace(/[^a-z0-9]+/gi, "-"); }
function omissionReason(issue, item) {
  const id = findingIdentity(item);
  const reasons = {
    "m14f:pattern:china_linked_education_funding": ["representation_limitation", "Accepted opposition exists in m14d:covered_china_linked_funding_exclusions, but M14F/M14G deliberately retain a directionless display. A directional section would override it. These two funding exclusions are distinct from the selected H.R.1048 episode and necessary context for any broader claim about foreign-influence rules; the card makes no such claim."],
    "m14f:pattern:collective_bargaining_continuity": ["representation_limitation", "Accepted support exists in m14d:continuity_of_collective_bargaining, but M14F/M14G deliberately retain a directionless display. A directional section would override it. This independent federal/private-sector bargaining relationship is not covered by the selected reporting episode and is not an overlap or low-evidence omission."],
    "wording:synthesis:congressional-disapproval": ["actual_overlap", "Contains both selected California actions, plus the separate appliance and BLM patterns. Adding it would repeat those actions while compressing three different mechanisms into another entry; the two omitted component patterns are separately assessed for space."],
    "wording:pattern:doe-appliance-equipment-rules": ["limited_space", "No action overlap with California. This adds four different appliance/equipment rules and regulatory functions; explaining their differences would require another regulatory-disapproval entry. The named waiver mechanism is retained as the narrower example; this is not evidence of lesser importance."],
    "wording:pattern:blm-land-decisions": ["limited_space", "No action overlap with California. Seven land decisions span places, plans, leasing and withdrawals; the required distinctions add more reading than the two named waiver permissions. These land choices remain a separate finding in the issue record."],
    "prop:e76b98cf92ef34cb": ["limited_space", "Distinct firearm-access evidence, not overlap: retired-service purchases, defense-facility carry and merchant coding need three objects explained. The selected D.C. finding keeps its common jurisdiction and the preparedness pair its two concrete mechanisms; neither summarizes firearm access."],
    "prop:e75e7aebbd7b2d29": ["limited_space", "Distinct opposition to payment-integrity oversight and longer pandemic-fraud enforcement periods. It adds two enforcement mechanisms beyond the chosen D.C. and preparedness entries. Its omission means those entries cannot imply uniform support for public-safety or enforcement measures."],
    "prop:53cda8d886a88f12": ["limited_space", "Distinct mixed HALT episode with three linked actions: certification amendment, earlier bill and later framework. It must remain one qualified episode. The shorter H.R.1048 pair already makes an amendment/package distinction legible; adding HALT requires a second timeline, not three short directional entries."],
    "wording:pattern:fisa-title-vii": ["limited_space", "Distinct surveillance-extension bills, not War Powers or assistance overlap. Whole-bill votes require a separate limitation on attributing opposition to Title VII alone; the selected foreign-hostilities/assistance pair already occupies substantial space. No general surveillance conclusion follows from the selected set."],
    "wording:pattern:military-dod-sex-gender": ["limited_space", "Five separate military/DoD amendments add health-care and biological-sex requirements limited to specified settings. Those objects are separate from hostilities and assistance and require another qualified entry; they are not represented by the selected defense-related findings."],
    "wording:notable:aumf-repeal": ["limited_space", "Repealing the 1991/2002 authorizations is distinct from the selected country-specific removal resolutions. It is not counted as overlap; explaining the separate authorization mechanism would add another military-authority entry."],
    "wording:notable:icc-sanctions": ["limited_space", "A distinct complete-bill sanctions choice concerning ICC actions against protected people. Its whole-bill and Court-wide limits need their own entry; the assistance and War Powers findings cannot represent it."],
    "wording:notable:haiti-tps": ["limited_space", "A distinct bill requiring a Haiti TPS designation, with a whole-bill limit and no broader immigration pattern. It adds a new mechanism beyond the complete hostilities/assistance contrast; omitted for reading length, not weak evidence."],
    "wording:notable:fy2026-ndaa": ["limited_space", "A distinct large defense-authorization package whose vote cannot identify a position on individual components. Its explanation supplies less specific policy behavior than the retained exact hostilities and assistance findings; it is not treated as opposing all defense policy."],
  };
  if (reasons[id]) return { category: reasons[id][0], reason: reasons[id][1] };
  const container = ["wording:pattern:iran-war-powers", "wording:pattern:lebanon-war-powers", "wording:pattern:venezuela-war-powers"].includes(id) ? "wording:synthesis:war-powers" : ["wording:pattern:ukraine-assistance", "wording:pattern:jordan-assistance", "wording:notable:israel-fmf-reduction", "wording:notable:taiwan-funding"].includes(id) ? "wording:synthesis:security-assistance" : id === "wording:pattern:terrorism-preparedness" ? "prop:d7e189366b477118" : null;
  if (!container) throw Error(`Missing item-specific omission review: ${issue}/${id}`);
  const selected = selections.find((s) => s[1] === container);
  const selectedItem = FINDING_FIELDS.flatMap((field) => presentations.find((p) => p.issue_id === selected[0])[field] || []).find((r) => findingIdentity(r) === container);
  if (!item.action_ids.every((action) => selectedItem.action_ids.includes(action))) throw Error(`Claimed overlap is not complete: ${id}`);
  return { category: container.includes("security-assistance") ? "necessary_contextual_pairing" : "actual_overlap", reason: `${item.public_title || item.title || item.heading}: all ${item.action_ids.length} actions are already included in ${container}. ${container.includes("security-assistance") ? "Keep this country inside the full four-country contrast, with its direction, mechanism and qualifications; a separate entry would repeat evidence and detach necessary context." : container.includes("war-powers") ? "The selected synthesis preserves this country's removal resolutions alongside the other two countries, including timing/wording differences; another entry would repeat its actions." : "The same exercise and assessment are selected under Justice. A second domain label would not create additional evidence."}` };
}
