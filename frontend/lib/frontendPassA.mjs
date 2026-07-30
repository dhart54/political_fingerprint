import { isProceduralContextRow } from "./proceduralContext.mjs";

export const ISSUE_SORT_MODES = Object.freeze([
  "recommended",
  "most_evidence",
  "reviewed_analysis",
  "a_z",
]);

export const ACTION_FILTERS = Object.freeze([
  "all",
  "yea",
  "nay",
  "non_directional",
  "substantive",
  "procedural_context",
]);

const CLAIM_RANK = Object.freeze({
  full_issue_synthesis: 4,
  full_review_no_common_throughline: 3,
  full_review_no_safe_synthesis: 2,
  reviewed_sample_finding: 1,
  vote_record_only: 0,
});

export function parsePassARouteState(search = "") {
  const params = new URLSearchParams(search);
  const scope = ["all", "119", "118"].includes(params.get("scope"))
    ? params.get("scope")
    : "all";
  const issue = normalizeIssue(params.get("issue"));
  return {
    legislatorId: normalizeLegislatorId(params.get("representative")),
    issue,
    scope,
  };
}

export function buildPassAUrl(
  currentUrl,
  { legislatorId = null, issue = null, scope = "all" },
) {
  const url = new URL(currentUrl, "http://localhost");
  if (legislatorId) {
    url.searchParams.set("representative", legislatorId);
  } else {
    url.searchParams.delete("representative");
  }
  if (legislatorId && issue) {
    url.searchParams.set("issue", issue);
  } else {
    url.searchParams.delete("issue");
  }
  if (legislatorId && scope !== "all") {
    url.searchParams.set("scope", scope);
  } else {
    url.searchParams.delete("scope");
  }
  return `${url.pathname}${url.search}${url.hash}`;
}

export function scopeLabel(scope) {
  if (scope === "119") {
    return "119th Congress";
  }
  if (scope === "118") {
    return "118th Congress";
  }
  return "All available Congresses";
}

export function isPublicAnalysisAvailable(presentation) {
  return Boolean(
    presentation?.review_state
      && presentation.tier !== "receipts_only"
      && presentation.review_state.public_claim_class !== "vote_record_only"
      && presentation.public_status_label,
  );
}

export function buildIssueOverviewRows({
  rows = [],
  presentations = new Map(),
  stableDomainOrder = [],
}) {
  const domainRank = new Map(
    stableDomainOrder.map((domain, index) => [domain, index]),
  );
  return rows.map((row, originalIndex) => {
    const presentation = presentations.get(row.domain) || null;
    const total = optionalNonNegativeNumber(row.total_votes)
      ?? (
        nonNegativeNumber(row.yea_count)
        + nonNegativeNumber(row.nay_count)
        + nonNegativeNumber(row.other_count)
      );
    const substantive = (
      nonNegativeNumber(row.interpreted_support_count)
      + nonNegativeNumber(row.interpreted_oppose_count)
    );
    const analysisAvailable = isPublicAnalysisAvailable(presentation);
    return {
      ...row,
      analysisAvailable,
      claimRank: analysisAvailable
        ? CLAIM_RANK[presentation.review_state.public_claim_class] || 0
        : 0,
      domainRank: domainRank.get(row.domain) ?? stableDomainOrder.length,
      originalIndex,
      presentation,
      substantiveEvidenceCount: substantive,
      totalRecordedActions: total,
    };
  });
}

export function sortAndFilterIssues(rows = [], mode = "recommended") {
  const normalizedMode = ISSUE_SORT_MODES.includes(mode) ? mode : "recommended";
  const filtered = normalizedMode === "reviewed_analysis"
    ? rows.filter((row) => row.analysisAvailable)
    : [...rows];
  return filtered.sort((left, right) => {
    if (normalizedMode === "a_z") {
      return publicIssueLabel(left).localeCompare(publicIssueLabel(right));
    }
    if (normalizedMode === "most_evidence") {
      return evidenceCompare(left, right);
    }
    if (normalizedMode === "reviewed_analysis") {
      return (
        right.claimRank - left.claimRank
        || evidenceCompare(left, right)
      );
    }
    return (
      Number(right.analysisAvailable) - Number(left.analysisAvailable)
      || right.claimRank - left.claimRank
      || evidenceCompare(left, right)
    );
  });
}

export function chronologicalActions(rows = []) {
  return [...rows].sort((left, right) => (
    String(right.vote_date || "").localeCompare(String(left.vote_date || ""))
    || Number(right.congress || 0) - Number(left.congress || 0)
    || Number(right.rollcall_number || 0) - Number(left.rollcall_number || 0)
    || String(right.roll_call_id || "").localeCompare(String(left.roll_call_id || ""))
  ));
}

export function filterActions(rows = [], filter = "all", highlightedIds = []) {
  const normalizedFilter = ACTION_FILTERS.includes(filter) ? filter : "all";
  const highlights = new Set(highlightedIds);
  if (filter === "highlighted") {
    return rows.filter((row) => highlights.has(canonicalActionId(row)));
  }
  if (normalizedFilter === "yea") {
    return rows.filter((row) => normalize(row.position) === "yea");
  }
  if (normalizedFilter === "nay") {
    return rows.filter((row) => normalize(row.position) === "nay");
  }
  if (normalizedFilter === "non_directional") {
    return rows.filter((row) => (
      normalize(row.position) === "present"
      || normalize(row.position) === "not_voting"
    ));
  }
  if (normalizedFilter === "substantive") {
    return rows.filter(isSubstantiveReceipt);
  }
  if (normalizedFilter === "procedural_context") {
    return rows.filter((row) => (
      isProceduralContextRow(row)
      || ["ambiguous", "insufficient_evidence"].includes(
        normalize(row.interpretation_status),
      )
    ));
  }
  return rows;
}

export function canonicalActionId(row) {
  const supplied = [row?.canonical_action_id, row?.roll_call_id].find(
    (value) => typeof value === "string" && /^[a-z]+:\d+:\d+:\d+$/.test(value),
  );
  if (supplied) {
    return supplied;
  }

  const chamber = normalize(row?.chamber);
  const congress = Number(row?.congress);
  const rollCall = Number(row?.rollcall_number);
  const voteYear = Number(String(row?.vote_date || "").slice(0, 4));
  const congressStartYear = 1789 + ((congress - 1) * 2);
  const session = voteYear === congressStartYear
    ? 1
    : voteYear === congressStartYear + 1
      ? 2
      : null;

  if (
    ["house", "senate"].includes(chamber)
    && Number.isInteger(congress)
    && congress > 0
    && Number.isInteger(session)
    && Number.isInteger(rollCall)
    && rollCall > 0
  ) {
    return `${chamber}:${congress}:${session}:${rollCall}`;
  }

  const fallback = row?.canonical_action_id || row?.roll_call_id;
  return typeof fallback === "string" ? fallback : "";
}

export function isSubstantiveReceipt(row) {
  return (
    ["yea", "nay"].includes(normalize(row?.position))
    && normalize(row?.interpretation_status) === "interpreted"
    && !isProceduralContextRow(row)
  );
}

export function actionReceiptId(row) {
  return `action-receipt-${canonicalActionId(row).replaceAll(":", "-")}`;
}

function evidenceCompare(left, right) {
  return (
    right.totalRecordedActions - left.totalRecordedActions
    || right.substantiveEvidenceCount - left.substantiveEvidenceCount
    || left.domainRank - right.domainRank
    || left.originalIndex - right.originalIndex
  );
}

function publicIssueLabel(row) {
  return String(row.publicLabel || row.label || row.domain || "");
}

function nonNegativeNumber(value) {
  return optionalNonNegativeNumber(value) ?? 0;
}

function optionalNonNegativeNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function normalizeIssue(value) {
  return typeof value === "string" && /^[A-Z][A-Z0-9_]+$/.test(value)
    ? value
    : null;
}

function normalizeLegislatorId(value) {
  return typeof value === "string" && /^leg_[a-z0-9_]+$/.test(value)
    ? value
    : null;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase().replaceAll(" ", "_");
}
