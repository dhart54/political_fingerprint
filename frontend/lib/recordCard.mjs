// A projection of an explicit review selection. No vote-derived meaning or ranking.
import { DOMAIN_ORDER } from "./issueEvidenceCoverage.mjs";
import { presentationIdentityMatches } from "./editorialPresentation.mjs";

export const FINDING_FIELDS = ["syntheses", "repeated_patterns", "policy_trajectories", "notable_choices"];
export const SECTION_ORDER = ["support", "opposition", "mixed"];

export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}

export async function contentHash(value) {
  const bytes = new TextEncoder().encode(canonicalJson(value));
  const hash = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function findingIdentity(item) {
  return item.wording_item_id || item.proposition_id || null;
}

export function suppliedDirection(item) {
  if (SECTION_ORDER.includes(item.direction)) return item.direction;
  const directions = item.semantic_lineage_directions;
  return Array.isArray(directions) && directions.length === 1 && SECTION_ORDER.includes(directions[0])
    ? directions[0] : null;
}

export function reviewedPresentations(payload) {
  return (payload?.presentations || []).filter((p) => p.review_state && p.tier !== "receipts_only");
}

export async function projectRecordCard({ candidate, payload, legislatorId, memberBioguideId, scope, requestStatus = "ready" }) {
  const empty = (status) => ({ status, entries: [], reviewedDomains: [] });
  if (requestStatus !== "ready") return empty(requestStatus);
  if (!payload || !Array.isArray(payload.presentations)) return empty("incomplete");
  if (!presentationIdentityMatches(payload, { legislatorId, memberBioguideId }) || payload.scope !== scope) return empty("identity_mismatch");
  const domains = payload.presentations.map((p) => p.issue_id);
  if (domains.length !== DOMAIN_ORDER.length || new Set(domains).size !== domains.length || DOMAIN_ORDER.some((d) => !domains.includes(d))) return empty("incomplete");
  const reviewed = reviewedPresentations(payload);
  const reviewedDomains = DOMAIN_ORDER.filter((d) => reviewed.some((p) => p.issue_id === d));
  if (!reviewed.length) return empty("empty");
  if (!candidate || candidate.status !== "candidate" || candidate.legislator_id !== legislatorId || candidate.member_bioguide_id !== memberBioguideId || !candidate.scopes.includes(scope)) return { ...empty("not_selected"), reviewedDomains };
  const byDomain = new Map(reviewed.map((p) => [p.issue_id, p]));
  // Verify the whole reviewed set, including omitted findings, before projecting.
  // A missing domain cannot silently change the impression of the selected set.
  for (const source of candidate.sources) {
    const p = byDomain.get(source.issue_id);
    if (!p) return { ...empty("incomplete"), reviewedDomains };
    if (p.requested_scope !== scope || p.reviewed_scope !== "119" || canonicalJson(p.review_state.congress_scope) !== "[119]" || await contentHash(p) !== source.presentation_sha256[scope]) return empty("source_mismatch");
    const coverage = source.evidence_coverage?.[scope];
    if (!coverage || coverage.source_field !== "scope_boundary" || coverage.source_text !== p.scope_boundary || await contentHash(p.scope_boundary) !== coverage.source_sha256) return empty("source_mismatch");
  }
  if (reviewed.length !== candidate.sources.length) return empty("source_mismatch");
  const entries = [];
  for (const selection of candidate.entries) {
    const p = byDomain.get(selection.issue_id);
    const item = p?.[selection.field]?.find((f) => findingIdentity(f) === selection.finding_id);
    if (!item || await contentHash(item) !== selection.finding_sha256 || suppliedDirection(item) !== selection.section || canonicalJson(item.action_ids) !== canonicalJson(selection.action_ids) || !selection.action_ids.length) return empty("source_mismatch");
    const source = candidate.sources.find((s) => s.issue_id === selection.issue_id);
    entries.push({ ...selection, source, sourceFinding: item, sourcePresentationHash: source.presentation_sha256[scope], reviewedScope: "119th Congress" });
  }
  // Manifest order is explicit; never sort by vote/episode counts or political direction.
  return { status: "ready", entries, reviewedDomains, scope, generationTime: candidate.generated_at, evidenceCoverage: candidate.sources.map((source) => ({ issue_id: source.issue_id, ...source.evidence_coverage[scope] })) };
}

export function resolveCardFinding(model, issue, findingId, sourceHash) {
  return model?.status === "ready" ? model.entries.find((entry) => entry.issue_id === issue && entry.finding_id === findingId && entry.sourcePresentationHash === sourceHash) || null : null;
}

export function recordCardUrl(currentUrl, { legislatorId, scope, issue = null, findingId = null, sourceHash = null, view = null, hash = "" }) {
  const url = new URL(currentUrl, "http://localhost");
  for (const [key, value] of Object.entries({ representative: legislatorId, scope, issue, finding: findingId, source: sourceHash, view })) {
    if (value) url.searchParams.set(key, value); else url.searchParams.delete(key);
  }
  url.hash = hash;
  return `${url.pathname}${url.search}${url.hash}`;
}
