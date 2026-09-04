const RAW_REVIEW_PROCESS_DISCLOSURE = /\b(?:about this interpretation|human[- ]reviewed|review(?:ed| status)? on|editorial process|provenance references?)\b/i;
const STRUCTURALLY_INTERNAL = /(?:^|[\\/])(?:backend|docs|frontend|scripts)[\\/]|\.json\b|\b(?:candidate_content_)?sha-?256\b|\b(?:interpretation|content)[_ -]digest\b|\b[a-f0-9]{40,}\b|\b(?:implementation[_ -]?id|[a-z0-9-]+-implementation|acceptance[_ -](?:receipt|ref)|delegated[_ -]acceptance|launch[_ -]ratification|ratification[_ -](?:receipt|ref)|semantic[_ -]ir[_ -]acceptance)\b/i;
const GENERIC_EPISODE_PROCESS = /^this action is one independently expandable part of the related policy episode\.?$/i;
const GENERIC_RECEIPT_CAVEAT = /^(?:this (?:candidate|receipt|interpretation) does not establish|the (?:candidate|receipt|interpretation) does not establish|this receipt remains bounded to the reviewed|the reviewed interpretation remains a candidate)\b/i;
const ALLOWED_ACTION_SOURCE_LABELS = new Set([
  "Bill or amendment text",
  "Congressional Record",
  "Executive order",
  "U.S. Code",
  "Official cost estimate",
  "Official report",
  "Official law text",
]);

export function buildPublicReceipt(row = {}) {
  const projection = row.governed_receipt_projection || null;
  const fields = deduplicateReceiptFields({
    exactActionMeaning:
      projection?.exact_action_meaning
      || row.plain_english_summary
      || row.interpretation_reason
      || "",
    proposedChange: projection ? "" : row.policy_effect || row.what_happened || "",
    policyQuestion:
      projection?.policy_question
      || row.question
      || row.description
      || "",
  });
  return {
    ...fields,
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
  return !STRUCTURALLY_INTERNAL.test(value)
    && !GENERIC_RECEIPT_CAVEAT.test(value)
    && !RAW_REVIEW_PROCESS_DISCLOSURE.test(value);
}

function publicEpisodeRelationship(value) {
  if (typeof value !== "string") {
    return "";
  }
  const normalized = value.trim();
  if (
    !normalized
    || GENERIC_EPISODE_PROCESS.test(normalized)
    || STRUCTURALLY_INTERNAL.test(normalized)
    || /^[a-z0-9]+(?:[-_:][a-z0-9]+){2,}$/i.test(normalized)
  ) {
    return "";
  }
  return normalized;
}

function deduplicateReceiptFields(fields) {
  const seen = new Set();
  return Object.fromEntries(
    ["exactActionMeaning", "proposedChange", "policyQuestion"].map((key) => {
      const value = typeof fields[key] === "string" ? fields[key].trim() : "";
      const identity = normalizeFieldIdentity(value);
      if (!identity || seen.has(identity)) {
        return [key, ""];
      }
      seen.add(identity);
      return [key, value];
    }),
  );
}

function normalizeFieldIdentity(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\p{P}\p{S}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeSource(source, kind) {
  const url = typeof source === "string"
    ? source
    : source?.url || source?.source_url;
  if (typeof url !== "string" || !/^https?:\/\//.test(url)) {
    return null;
  }
  return {
    label: kind === "vote" ? "Official vote" : publicActionSourceLabel(source, url),
    url,
  };
}

function publicActionSourceLabel(source, url) {
  const supplied = typeof source === "object" && source !== null
    ? source.public_label
    : null;
  return ALLOWED_ACTION_SOURCE_LABELS.has(supplied)
    ? supplied
    : actionSourceLabel(url);
}

function actionSourceLabel(url) {
  const normalized = url.toLowerCase();
  if (normalized.includes("cbo.gov")) {
    return "Official cost estimate";
  }
  if (normalized.includes("/amendment/") || normalized.includes("hamdt")) {
    return "Bill or amendment text";
  }
  if (normalized.includes("/bill/") || normalized.includes("/bills/")) {
    return "Bill or amendment text";
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
  return "Bill or amendment text";
}
