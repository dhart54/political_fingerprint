const PUBLIC_TIERS = new Set([
  "reviewed_conclusion",
  "developing_read",
  "non_directional_or_limited_evidence",
  "receipts_only",
]);

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

export function getEditorialPresentation(payload, domain) {
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
