export const RECORD_ACROSS_PRODUCT_FRAMING = "Record Across Congresses";

export const RECORD_ACROSS_COPY = {
  panelTitle: RECORD_ACROSS_PRODUCT_FRAMING,
  oneSentenceExplanation:
    "Reviewed House vote evidence exists in both the 118th and 119th Congresses for these policy-question families. Counts stay separated by Congress and vote-status bucket.",
  collapsedSummaryLabel: "Reviewed family evidence in both Congresses",
  eligibleFamilyCountLabel: "Eligible families",
  directComparableFamilyLabel: "Closest family match",
  conditionalComparableFamilyLabel: "Caveated family match",
  noEligibleFamiliesState:
    "No reviewed family has enough House vote evidence in both Congresses for this panel yet.",
  priorCongressOnlyState:
    "Reviewed family evidence is available in the 118th Congress, but not in the 119th Congress for this official.",
  recentCongressOnlyState:
    "Reviewed family evidence is available in the 119th Congress, but not in the 118th Congress for this official.",
  notVotingCaveat:
    "Not-voting rows are shown separately and are not counted as Yes or No votes.",
  missingNoRecordCaveat:
    "Missing/no-record means this official has no counted vote row for that roll call in the reviewed data.",
  relatedUnavailableNote:
    "Related rows that do not meet the family standard are not shown in this panel.",
  whyNotInferenceExplanation:
    "This panel places reviewed roll-call evidence from two Congresses side by side. It does not describe what that means about the official's views, behavior, or reasons.",
  sourceEvidenceDrilldownPrompt:
    "View roll-call evidence",
  closeEvidenceDrilldownPrompt: "Hide roll-call evidence",
  drilldownHeading: "Roll-call evidence used for this family",
};

export const RECORD_ACROSS_COUNT_FIELDS = [
  {
    key: "cast_substantive_yes_count",
    label: "Cast substantive Yes",
  },
  {
    key: "cast_substantive_no_count",
    label: "Cast substantive No",
  },
  {
    key: "not_voting_count",
    label: "Not voting",
  },
  {
    key: "present_count",
    label: "Present",
  },
  {
    key: "missing_no_record_count",
    label: "Missing/no-record",
  },
];

const ALLOWED_STATUSES = new Set(["directly_comparable", "conditionally_comparable"]);
const SUPPORTED_CONGRESSES = ["118", "119"];
const DISALLOWED_COPY_TERMS = [
  "changed",
  "change",
  "trend",
  "shifted",
  "movement",
  "more supportive",
  "less supportive",
  "consistent",
  "flip",
  "ideological",
  "evolved",
  "moderated",
  "became",
  "continuity",
  "moved toward",
  "moved away from",
];

export function sanitizeRecordAcrossResponse(payload) {
  if (!payload || payload.product_framing !== RECORD_ACROSS_PRODUCT_FRAMING) {
    return null;
  }

  const summary = sanitizeSummary(payload.summary);
  const families = Array.isArray(payload.families)
    ? payload.families.map(sanitizeFamily).filter(Boolean)
    : [];

  return {
    product_framing: payload.product_framing,
    legislator_identifier: stringOrEmpty(payload.legislator_identifier),
    supported_congresses: Array.isArray(payload.supported_congresses)
      ? payload.supported_congresses.filter((value) => value === 118 || value === 119)
      : [118, 119],
    legislator: sanitizeLegislator(payload.legislator),
    summary,
    families: sortDisplayFamilies(families),
  };
}

export function getDisplayFamilies(response) {
  if (!response || response.product_framing !== RECORD_ACROSS_PRODUCT_FRAMING) {
    return [];
  }

  return (response.families || []).filter(
    (family) =>
      family.record_across_congresses_available === true &&
      ALLOWED_STATUSES.has(family.comparability_status),
  );
}

export function getFamilyMatchLabel(status) {
  if (status === "directly_comparable") {
    return RECORD_ACROSS_COPY.directComparableFamilyLabel;
  }
  if (status === "conditionally_comparable") {
    return RECORD_ACROSS_COPY.conditionalComparableFamilyLabel;
  }
  return "";
}

export function getSparseStateCopy(response) {
  const displayFamilies = getDisplayFamilies(response);
  if (!response || displayFamilies.length > 0) {
    return "";
  }

  const availability = getSubstantiveAvailability(response.families || []);
  if (availability.has118 && !availability.has119) {
    return RECORD_ACROSS_COPY.priorCongressOnlyState;
  }
  if (availability.has119 && !availability.has118) {
    return RECORD_ACROSS_COPY.recentCongressOnlyState;
  }
  return RECORD_ACROSS_COPY.noEligibleFamiliesState;
}

export function buildFamilyRollCallDrilldown({ family, evidenceRows = [] } = {}) {
  if (!family || !ALLOWED_STATUSES.has(family.comparability_status)) {
    return null;
  }

  const rowsByRollCallId = new Map(
    (Array.isArray(evidenceRows) ? evidenceRows : []).map((row) => [String(row?.roll_call_id || ""), row]),
  );

  return {
    family_id: family.family_id,
    family_name: family.family_name,
    issue_domain: family.issue_domain,
    match_label: getFamilyMatchLabel(family.comparability_status),
    governing_question: family.governing_question,
    comparability_caveat: family.comparability_caveat,
    congresses: Object.fromEntries(
      SUPPORTED_CONGRESSES.map((congress) => [
        congress,
        buildCongressRollCallRows({
          congress,
          rollCallIds: family.roll_call_ids_considered_by_congress?.[congress] || [],
          rowsByRollCallId,
        }),
      ]),
    ),
  };
}

export function getFamilyRollCallIds(family) {
  return SUPPORTED_CONGRESSES.flatMap(
    (congress) => family?.roll_call_ids_considered_by_congress?.[congress] || [],
  );
}

export function getRollCallCountBucket(row) {
  if (!row || row.missing_no_record === true) {
    return "missing_no_record_count";
  }
  if (row.position === "not_voting") {
    return "not_voting_count";
  }
  if (row.position === "present") {
    return "present_count";
  }
  if (
    row.interpretation_status === "interpreted" &&
    row.position === "yea" &&
    row.support_position &&
    row.oppose_position
  ) {
    return "cast_substantive_yes_count";
  }
  if (
    row.interpretation_status === "interpreted" &&
    row.position === "nay" &&
    row.support_position &&
    row.oppose_position
  ) {
    return "cast_substantive_no_count";
  }
  return "";
}

export function isCountedSubstantiveFamilyEvidence(row) {
  const bucket = getRollCallCountBucket(row);
  return bucket === "cast_substantive_yes_count" || bucket === "cast_substantive_no_count";
}

export function getCountBucketLabel(bucket) {
  return RECORD_ACROSS_COUNT_FIELDS.find((field) => field.key === bucket)?.label || "Not counted substantive evidence";
}

export function getApprovedFamilyEvidenceSummary(row) {
  if (!row || row.missing_no_record === true) {
    return RECORD_ACROSS_COPY.missingNoRecordCaveat;
  }

  const candidates = [
    row.what_happened,
    row.plain_english_summary,
    row.member_vote_context,
    row.description,
    row.question,
  ];
  const safeCandidate = candidates.find((candidate) => {
    const text = stringOrEmpty(candidate).trim();
    return text && !containsDisallowedCopy(text);
  });

  return safeCandidate || "Reviewed roll-call evidence row.";
}

export function containsDisallowedCopy(value) {
  const text = stringOrEmpty(value).toLowerCase();
  return DISALLOWED_COPY_TERMS.some((term) => text.includes(term));
}

function sanitizeSummary(summary = {}) {
  return {
    record_across_congresses_available: summary.record_across_congresses_available === true,
    display_eligible_family_count: numberOrZero(summary.display_eligible_family_count),
    directly_comparable_display_eligible_family_count: numberOrZero(
      summary.directly_comparable_display_eligible_family_count,
    ),
    conditionally_comparable_display_eligible_family_count: numberOrZero(
      summary.conditionally_comparable_display_eligible_family_count,
    ),
  };
}

function sanitizeLegislator(legislator = {}) {
  return {
    legislator_identifier: stringOrEmpty(legislator.legislator_identifier),
    chamber: stringOrEmpty(legislator.chamber),
    name_display: stringOrEmpty(legislator.name_display),
    state: stringOrEmpty(legislator.state),
    district: stringOrEmpty(legislator.district),
    party: stringOrEmpty(legislator.party),
  };
}

function sanitizeFamily(family) {
  if (!family || !ALLOWED_STATUSES.has(family.comparability_status)) {
    return null;
  }

  return {
    family_id: stringOrEmpty(family.family_id),
    family_name: stringOrEmpty(family.family_name),
    issue_domain: stringOrEmpty(family.issue_domain),
    comparability_status: family.comparability_status,
    governing_question: stringOrEmpty(family.governing_question),
    comparability_caveat: stringOrEmpty(family.comparability_caveat),
    record_across_congresses_available:
      family.record_across_congresses_available === true,
    unavailable_reason: stringOrEmpty(family.unavailable_reason),
    roll_call_ids_considered_by_congress: sanitizeRollCallIds(
      family.roll_call_ids_considered_by_congress,
    ),
    family_evidence_counts_by_congress: sanitizeCountsByCongress(
      family.family_evidence_counts_by_congress,
    ),
  };
}

function sanitizeRollCallIds(idsByCongress = {}) {
  return {
    118: sanitizeRollCallIdList(idsByCongress["118"]),
    119: sanitizeRollCallIdList(idsByCongress["119"]),
  };
}

function sanitizeRollCallIdList(values) {
  return Array.isArray(values)
    ? values.map((value) => Number(value)).filter(Number.isFinite)
    : [];
}

function sanitizeCountsByCongress(countsByCongress = {}) {
  return {
    118: sanitizeCounts(countsByCongress["118"]),
    119: sanitizeCounts(countsByCongress["119"]),
  };
}

function sanitizeCounts(counts = {}) {
  return Object.fromEntries(
    RECORD_ACROSS_COUNT_FIELDS.map((field) => [field.key, numberOrZero(counts[field.key])]),
  );
}

function sortDisplayFamilies(families) {
  return [...families].sort((left, right) => {
    const leftRank = left.comparability_status === "directly_comparable" ? 0 : 1;
    const rightRank = right.comparability_status === "directly_comparable" ? 0 : 1;
    return leftRank - rightRank;
  });
}

function getSubstantiveAvailability(families) {
  return families.reduce(
    (result, family) => {
      const counts118 = family.family_evidence_counts_by_congress?.["118"] || {};
      const counts119 = family.family_evidence_counts_by_congress?.["119"] || {};
      result.has118 =
        result.has118 ||
        numberOrZero(counts118.cast_substantive_yes_count) +
          numberOrZero(counts118.cast_substantive_no_count) >
          0;
      result.has119 =
        result.has119 ||
        numberOrZero(counts119.cast_substantive_yes_count) +
          numberOrZero(counts119.cast_substantive_no_count) >
          0;
      return result;
    },
    { has118: false, has119: false },
  );
}

function numberOrZero(value) {
  return Number.isFinite(value) ? value : 0;
}

function stringOrEmpty(value) {
  return typeof value === "string" ? value : "";
}

function buildCongressRollCallRows({ congress, rollCallIds, rowsByRollCallId }) {
  return rollCallIds.map((rollCallId) => {
    const row = rowsByRollCallId.get(String(rollCallId));
    if (!row) {
      return {
        roll_call_id: String(rollCallId),
        congress: Number(congress),
        missing_no_record: true,
        position: "",
        count_bucket: "missing_no_record_count",
        counted_substantive_evidence: false,
      };
    }

    const countBucket = getRollCallCountBucket(row);
    return {
      ...row,
      roll_call_id: String(row.roll_call_id || rollCallId),
      congress: Number(row.congress || congress),
      count_bucket: countBucket,
      counted_substantive_evidence: isCountedSubstantiveFamilyEvidence(row),
    };
  });
}
