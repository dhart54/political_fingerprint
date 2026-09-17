import { DOMAIN_ORDER } from "./issueEvidenceCoverage.mjs";

const PUBLIC_TIERS = new Set([
  "reviewed_conclusion",
  "developing_read",
  "non_directional_or_limited_evidence",
  "receipts_only",
]);

// API validity is independent of any optional, content-bound card selection.
export function issuePresentationStatus(payload, identity, scope) {
  if (!payload || !Array.isArray(payload.presentations)) return "incomplete";
  if (!presentationIdentityMatches(payload, identity) || payload.scope !== scope) return "identity_mismatch";
  const indexed = indexEditorialPresentations(payload);
  if (payload.presentations.length !== DOMAIN_ORDER.length || indexed.size !== DOMAIN_ORDER.length || DOMAIN_ORDER.some((domain) => !indexed.has(domain))) return "incomplete";
  if (payload.presentations.some((p) => p.requested_scope !== scope)) return "identity_mismatch";
  return "ready";
}

export function indexEditorialPresentations(payload) {
  const result = new Map();
  for (const presentation of payload?.presentations || []) {
    if (
      typeof presentation?.issue_id !== "string" ||
      !PUBLIC_TIERS.has(presentation?.tier) ||
      typeof presentation?.tier_badge !== "string" ||
      typeof presentation?.teaser !== "string"
    ) {
      continue;
    }
    result.set(presentation.issue_id, presentation);
  }
  return result;
}

export function presentationIdentityMatches(
  payload,
  { legislatorId, memberBioguideId } = {},
) {
  return (
    typeof legislatorId === "string" &&
    typeof memberBioguideId === "string" &&
    payload?.legislator_id === legislatorId &&
    payload?.member_bioguide_id === memberBioguideId
  );
}

export function getEditorialPresentation(payload, domain, identity) {
  if (!presentationIdentityMatches(payload, identity)) {
    return null;
  }
  return indexEditorialPresentations(payload).get(domain) || null;
}

export function getCanonicalActionId(row) {
  const supplied = row?.canonical_action_id || row?.roll_call_id;
  return typeof supplied === "string" && supplied.startsWith("house:")
    ? supplied
    : null;
}

export function receiptAnchorId(actionId) {
  return `vote-receipt-${String(actionId || "").replaceAll(":", "-")}`;
}
