const INTERNAL_DISCLOSURE = /\b(?:acceptance|benchmark sample|candidate|delegated|digest|editorial|hash|implementation|interpretation|launch ratification|manifest|milestone|provenance|publication|ratification|repository|review(?:ed|ing)?|sha-?256)\b/i;
const INTERNAL_PATH_OR_ID = /(?:^|[\\/])docs[\\/]|\.json\b|\b[a-f0-9]{40,}\b|^[a-z][a-z0-9_-]*(?::[a-z0-9_-]+){2,}$/i;

export function buildPublicReceipt(row = {}) {
  const projection = row.governed_receipt_projection || null;
  return {
    exactActionMeaning:
      projection?.exact_action_meaning
      || row.plain_english_summary
      || row.interpretation_reason
      || "",
    policyQuestion:
      projection?.policy_question
      || row.question
      || row.description
      || "",
    proposedChange: projection ? "" : row.policy_effect || row.what_happened || "",
    representativeVote: projection?.member_action || row.position || "",
    episodeRelationship: publicEpisodeRelationship(
      projection?.episode_relationship || row.episode_relationship,
    ),
    limitations: publicLimitations(
      projection?.caveats,
      row.uncertainty_note,
    ),
    voteSources: publicSources(
      projection?.vote_sources || (row.source_url ? [row.source_url] : []),
      "vote",
    ),
    actionSources: publicSources(
      projection?.action_meaning_sources || row.source_basis,
      "action",
    ),
  };
}

export function publicLimitations(values, fallback = "") {
  const supplied = Array.isArray(values) && values.length ? values : [fallback];
  return supplied
    .filter((value) => typeof value === "string")
    .map((value) => value.trim())
    .filter(Boolean)
    .filter(isVoterRelevantLimitation);
}

export function publicSources(values, kind = "action") {
  const seen = new Set();
  return (Array.isArray(values) ? values : [])
    .map((source) => normalizeSource(source, kind))
    .filter(Boolean)
    .filter((source) => {
      if (seen.has(source.url)) {
        return false;
      }
      seen.add(source.url);
      return true;
    });
}

function isVoterRelevantLimitation(value) {
  return !INTERNAL_DISCLOSURE.test(value) && !INTERNAL_PATH_OR_ID.test(value);
}

function publicEpisodeRelationship(value) {
  if (typeof value !== "string") {
    return "";
  }
  const normalized = value.trim();
  if (
    !normalized
    || INTERNAL_DISCLOSURE.test(normalized)
    || INTERNAL_PATH_OR_ID.test(normalized)
    || /^[a-z0-9]+(?:[-_:][a-z0-9]+){2,}$/i.test(normalized)
  ) {
    return "";
  }
  return normalized;
}

function normalizeSource(source, kind) {
  const url = typeof source === "string"
    ? source
    : source?.url || source?.source_url;
  if (typeof url !== "string" || !/^https?:\/\//.test(url)) {
    return null;
  }
  return {
    label: kind === "vote" ? "Official vote" : actionSourceLabel(url),
    url,
  };
}

function actionSourceLabel(url) {
  const normalized = url.toLowerCase();
  if (normalized.includes("cbo.gov")) {
    return "Official cost estimate";
  }
  if (normalized.includes("/amendment/") || normalized.includes("hamdt")) {
    return "Official amendment";
  }
  if (normalized.includes("/bill/") || normalized.includes("/bills/")) {
    return "Official bill";
  }
  if (
    normalized.includes("committee-report")
    || normalized.includes("rulesreport")
    || normalized.includes("/crpt/")
  ) {
    return "Official report";
  }
  if (normalized.includes("/plaws/") || normalized.includes("public-law")) {
    return "Official law text";
  }
  return "Official bill or amendment material";
}
