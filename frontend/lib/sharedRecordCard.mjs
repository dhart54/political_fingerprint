// Candidate presentation calibration over publication-gated API findings.
// No ledger, member-specific content, persistence, or publication authority.
import { contentHash, findingIdentity, FINDING_FIELDS } from "./recordCard.mjs";
import { issuePresentationStatus } from "./editorialPresentation.mjs";
import { DOMAIN_ORDER } from "./issueEvidenceCoverage.mjs";

export const CARD_POLICY = Object.freeze({ version: "shared-record-card-candidate-v1", wordBudget: 500, shortExplanationWords: 55 });
const DIRECTIONS = ["support", "opposition", "mixed"];
const VOLATILE = new Set(["generated_at", "captured_at", "captured_at_utc", "fetched_at"]);
export function substantiveInput(value) {
  if (Array.isArray(value)) return value.map(substantiveInput);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value).filter(([key]) => !VOLATILE.has(key)).map(([key, item]) => [key, substantiveInput(item)]));
}
const words = (text) => text.trim().split(/\s+/u).filter(Boolean).length;
const title = (item) => item.public_title || item.title || item.heading;
const body = (item) => item.primary_sentence || item.body;
const paragraphs = (item) => [...new Set([body(item), item.secondary_clarification, ...(item.limitations || [])].filter(Boolean))];
const key = (row) => `${row.issue}:${row.id}`;
const sameSet = (a, b) => a.length === b.length && a.every((id) => b.includes(id));
const compare = (a, b) => FINDING_FIELDS.indexOf(a.field) - FINDING_FIELDS.indexOf(b.field) || a.id.localeCompare(b.id, "en");
const scopedLimits = (row) => (row.presentation.limitations || []).filter((limit) => limit.action_ids?.some((id) => row.item.action_ids.includes(id))).map((limit) => limit.body).filter(Boolean);
const validDate = (value) => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(`${value}T00:00:00Z`)) && new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) === value;

export async function sourceCoverage(presentation) {
  const source_text = presentation.scope_boundary;
  const source_sha256 = await contentHash(source_text);
  const typed = presentation.evidence_coverage;
  let cutoff = null;
  if (typed && (typed.source_field !== "scope_boundary" || typed.source_text !== source_text || typed.source_sha256 !== source_sha256 || (typed.cutoff != null && !validDate(typed.cutoff)))) throw Error("Coverage metadata does not match its source boundary.");
  if (typed?.cutoff) cutoff = typed.cutoff;
  const match = source_text?.match(/\bthrough (January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4})\./);
  if (!cutoff && match) {
    const month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].indexOf(match[1]) + 1;
    const iso = `${match[3]}-${String(month).padStart(2, "0")}-${match[2].padStart(2, "0")}`;
    if (validDate(iso)) cutoff = iso;
  }
  return { issue_id: presentation.issue_id, reviewed_scope: presentation.reviewed_scope, cutoff, cutoff_label: cutoff, status: cutoff ? "specified" : "unspecified_in_bound_review_scope", source_field: "scope_boundary", source_text, source_sha256, issue_limitations: presentation.limitations || [] };
}

export async function buildSharedRecordCard({ payload, legislatorId, memberBioguideId, scope, requestStatus = "ready" }) {
  const empty = (status) => ({ status, policyVersion: CARD_POLICY.version, entries: [], reviewedDomains: [], exceptions: [], omissions: [] });
  if (requestStatus !== "ready") return empty(requestStatus);
  const validity = issuePresentationStatus(payload, { legislatorId, memberBioguideId }, scope);
  if (validity !== "ready") return empty(validity);
  const source = substantiveInput(payload);
  // Canonical domain/finding order avoids response ordering becoming a selection rule.
  source.presentations.sort((a, b) => DOMAIN_ORDER.indexOf(a.issue_id) - DOMAIN_ORDER.indexOf(b.issue_id));
  for (const p of source.presentations) for (const field of FINDING_FIELDS) if (Array.isArray(p[field])) p[field].sort((a, b) => String(findingIdentity(a)).localeCompare(String(findingIdentity(b)), "en"));
  const fingerprint = await contentHash({ policy: CARD_POLICY, source });
  const reviewed = source.presentations.filter((p) => p.review_state && p.tier !== "receipts_only");
  if (!reviewed.length) return { ...empty("empty"), sourceFingerprint: fingerprint };
  const exceptions = new Map();
  const omissions = [];
  const exception = (row, rule, reason) => {
    const semantic = [...(row.item?.semantic_source_ids || [row.id || row.issue])].sort().join("+");
    const id = `${rule}:${semantic}`;
    exceptions.set(id, { id, rule, semantic_source: semantic, reason });
    omissions.push({ finding_id: row.id, issue_id: row.issue, category: "representation_limitation", exception_id: id, reason });
  };
  const rows = [];
  const coverage = [];
  for (const p of reviewed) {
    const congresses = p.review_state.congress_scope;
    if (!Array.isArray(congresses) || congresses.length !== 1 || String(congresses[0]) !== p.reviewed_scope || (scope !== "all" && scope !== p.reviewed_scope) || typeof p.scope_boundary !== "string") return empty("source_mismatch");
    try { coverage.push(await sourceCoverage(p)); } catch { return empty("source_mismatch"); }
    const hash = await contentHash(p);
    const seen = new Set();
    for (const field of FINDING_FIELDS) for (const item of p[field] || []) {
      const row = { issue: p.issue_id, id: findingIdentity(item), field, item, presentation: p, hash };
      if (!row.id || seen.has(row.id)) return empty("source_mismatch");
      seen.add(row.id);
      rows.push(row);
    }
  }
  const blocked = new Set();
  const components = new Set();
  const closures = new Map();
  const valid = (row) => {
    const item = row.item;
    const actions = item.action_ids;
    if (!Array.isArray(actions) || !actions.length || new Set(actions).size !== actions.length || actions.some((id) => !/^house:\d+:\d+:\d+$/.test(id))) return "Complete unique House action references are required.";
    if (actions.some((id) => id.split(":")[1] !== row.presentation.reviewed_scope)) return "Action Congress differs from the reviewed scope.";
    if (item.public_supporting_action_ids && !sameSet(actions, item.public_supporting_action_ids)) return "Public supporting actions disagree with finding actions.";
    if (item.semantic_lineage_action_ids && !sameSet(actions, item.semantic_lineage_action_ids)) return "Contextual actions were excluded from the public projection; a complete compact form is unavailable.";
    if (typeof title(item) !== "string" || !title(item).trim() || typeof body(item) !== "string" || !body(item).trim()) return "Reviewed title and complete explanation are required.";
    if (item.limitations && (!Array.isArray(item.limitations) || item.limitations.some((value) => typeof value !== "string"))) return "Unsupported limitation representation.";
    if (item.direction != null && !DIRECTIONS.includes(item.direction)) return "Unsupported typed direction.";
    if (item.semantic_lineage_directions?.some((direction) => !DIRECTIONS.includes(direction))) return "Unsupported semantic-lineage direction.";
    if (item.direction && item.semantic_lineage_directions?.length && !item.semantic_lineage_directions.includes(item.direction)) return "Display and lineage directions conflict.";
    return null;
  };
  for (const row of rows) {
    const reason = valid(row);
    if (reason) { blocked.add(key(row)); exception(row, "finding_form", reason); }
  }
  // Account for every resolvable component before traversal. A missing sibling
  // must not free later children into standalone, context-stripped entries.
  for (const row of rows) for (const relation of row.item.mapping?.relationship_roles || []) {
    for (const child of rows.filter((other) => other.issue === row.issue && other.item.semantic_source_ids?.includes(relation.proposition_id))) components.add(key(child));
  }
  function closure(row, trail = new Set()) {
    if (trail.has(key(row))) throw Error("Cyclic contextual relationship.");
    const next = new Set([...trail, key(row)]);
    const children = [];
    for (const relation of row.item.mapping?.relationship_roles || []) {
      if (!["primary_support", "contextual_support", "contrast", "limiting", "support"].includes(relation.relationship_role)) throw Error(`Unsupported relationship role: ${relation.relationship_role}.`);
      const matches = rows.filter((other) => other.issue === row.issue && other.item.semantic_source_ids?.includes(relation.proposition_id));
      if (matches.length !== 1) throw Error(`Missing or ambiguous contextual finding: ${relation.proposition_id}.`);
      const child = matches[0];
      components.add(key(child));
      children.push(child, ...closure(child, next));
    }
    return [...new Map(children.map((child) => [key(child), child])).values()].sort(compare);
  }
  for (const row of rows) {
    try {
      const children = closure(row);
      if (blocked.has(key(row))) continue;
      if (children.length && (!sameSet([...new Set(children.flatMap((r) => r.item.action_ids || []))], row.item.action_ids) || children.some((child) => blocked.has(key(child))))) throw Error("Complete contextual bundle cannot be represented with the parent's exact action set.");
      closures.set(key(row), children);
    } catch (error) { if (!blocked.has(key(row))) exception(row, "contextual_bundle", error.message); blocked.add(key(row)); }
  }
  for (const row of rows.filter((row) => components.has(key(row)))) omissions.push({ finding_id: row.id, issue_id: row.issue, category: "necessary_contextual_pairing", reason: "Retained only with its typed parent relationship; never separated into an independent directional entry." });
  const byDomain = DOMAIN_ORDER.map((domain) => rows.filter((row) => row.issue === domain && !blocked.has(key(row)) && !components.has(key(row))).sort(compare));
  const entries = [];
  let cost = 0;
  while (byDomain.some((queue) => queue.length)) for (const queue of byDomain) {
    const row = queue.shift();
    if (!row) continue;
    const item = row.item;
    const children = closures.get(key(row)) || [];
    const previous = entries.find((entry) => entry.action_ids.some((id) => item.action_ids.includes(id)));
    if (previous) {
      omissions.push({ issue_id: row.issue, finding_id: row.id, category: "actual_overlap", overlapping_entry: previous.id, shared_action_ids: item.action_ids.filter((id) => previous.action_ids.includes(id)), reason: "Shares exact actions with the earlier selected unit; not counted as independent evidence." });
      continue;
    }
    const direction = item.show_direction === false ? null : item.direction || (item.semantic_lineage_directions?.length === 1 ? item.semantic_lineage_directions[0] : null);
    const mixed = direction === "mixed" || item.semantic_lineage_directions?.includes("mixed") || children.length > 0;
    const compact = children.length ? `Compare the complete set of ${item.action_ids.length} House choices.` : words(body(item)) <= CARD_POLICY.shortExplanationWords ? body(item) : mixed ? `Compare the complete set of ${item.action_ids.length} House choices.` : `Read the complete explanation of these ${item.action_ids.length} House choices.`;
    const qualifications = [...new Set([item.secondary_clarification, ...(item.limitations || []), ...scopedLimits(row)].filter(Boolean))];
    const explanationParagraphs = [compact, ...qualifications];
    for (const child of children) {
      const limits = [...new Set([child.item.secondary_clarification, ...(child.item.limitations || []), ...scopedLimits(child)].filter(Boolean))];
      if (limits.length) explanationParagraphs.push(`${title(child.item)}: ${limits.join(" ")}`);
    }
    const explanation = explanationParagraphs.join(" ");
    const entryCost = words(`${title(item)} ${explanation}`);
    if (entryCost > CARD_POLICY.wordBudget) { exception(row, "compact_form", "The complete qualified unit exceeds the opening-card word budget; a shared compact form needs review."); continue; }
    if (cost + entryCost > CARD_POLICY.wordBudget) { omissions.push({ issue_id: row.issue, finding_id: row.id, category: "limited_space", words: entryCost, remaining_words: CARD_POLICY.wordBudget - cost, reason: "The complete qualified unit does not fit the remaining opening-card budget." }); continue; }
    cost += entryCost;
    entries.push({
      id: `shared-card-${row.issue}-${row.id.replace(/[^a-z0-9]+/gi, "-")}`,
      issue_id: row.issue, finding_id: row.id, field: row.field,
      finding_sha256: await contentHash(item), section: direction || "neutral",
      headline: title(item), explanation, explanation_paragraphs: explanationParagraphs,
      action_ids: item.action_ids, episode_ids: item.episode_ids || null,
      evidence_label: `Based on ${item.action_ids.length} House votes`,
      link_label: mixed ? "Compare the proposals" : "See the votes",
      sourceFinding: item, sourcePresentationHash: row.hash,
      reviewedScope: `${row.presentation.reviewed_scope}th Congress`,
      detail_paragraphs: [...new Set([...paragraphs(item), ...scopedLimits(row)]),
        ...children.flatMap((child) => [title(child.item), ...new Set([...paragraphs(child.item), ...scopedLimits(child)])])],
      source_bindings: await Promise.all([row, ...children].map(async (r) => ({
        issue_id: r.issue, field: r.field, finding_id: r.id, action_ids: r.item.action_ids,
        finding_sha256: await contentHash(r.item), presentation_sha256: r.hash,
        semantic_source_ids: r.item.semantic_source_ids || [r.id],
      }))),
      qualification_paragraphs: qualifications,
    });
  }
  return { status: entries.length ? "ready" : "representation_unavailable", policyVersion: CARD_POLICY.version, authority: "candidate_for_presentation_review", sourceFingerprint: fingerprint, entries, reviewedDomains: reviewed.map((p) => p.issue_id), scope, reviewedScopes: [...new Set(reviewed.map((p) => p.reviewed_scope))].sort(), evidenceCoverage: coverage, exceptions: [...exceptions.values()].sort((a, b) => a.id.localeCompare(b.id, "en")), omissions, openingWords: cost };
}

export async function projectSharedRecordCard(args, cached = null) {
  try {
    const current = await buildSharedRecordCard(args);
    if (cached && await contentHash(cached) !== await contentHash(current)) return { ...current, status: "source_mismatch", entries: [] };
    return current;
  } catch {
    return { status: "incomplete", entries: [], reviewedDomains: [] };
  }
}
