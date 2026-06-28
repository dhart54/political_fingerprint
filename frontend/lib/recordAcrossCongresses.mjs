export const RECORD_ACROSS_PRODUCT_FRAMING = "Record Across Congresses";

export const RECORD_ACROSS_COPY = {
  panelTitle: RECORD_ACROSS_PRODUCT_FRAMING,
  oneSentenceExplanation:
    "Reviewed House vote evidence exists in both the 118th and 119th Congresses for these policy-question families.",
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
    "Open the roll-call evidence used for this family.",
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
    118: Array.isArray(idsByCongress["118"]) ? idsByCongress["118"].filter(Number.isFinite) : [],
    119: Array.isArray(idsByCongress["119"]) ? idsByCongress["119"].filter(Number.isFinite) : [],
  };
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
