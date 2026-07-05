import { sanitizeRecordAcrossResponse } from "./recordAcrossCongresses.mjs";

export const GOLDEN_RENDER_FIXTURE_ROUTE = "/golden-render-fixture";

export const GOLDEN_RENDER_UNSAFE_PHRASES = [
  "this was a direct vote",
  "records a direct position",
  "the House voted on whether",
  "the Senate voted on whether",
  "whether to agree to",
  "Amendment No.",
  "the amendment decreases",
  "the amendment redirects",
  "source basis",
  "classification reason",
  "House amendment vote",
  "other reviewed policy measures",
  "has the clearest pattern: mostly",
  "mostly opposed in the reviewed sample",
  "mostly supported in the reviewed sample",
];

export const goldenLegislator = {
  id: "golden_valerie_foushee",
  bioguide_id: "F000481",
  name_display: "Valerie P. Foushee",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};

export const limitedEvidenceLegislator = {
  id: "golden_limited_profile",
  bioguide_id: "GOLDEN",
  name_display: "Golden Limited Profile",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};

const scopeMetadata = {
  congresses: [118, 119],
  requested_congresses: [118, 119],
  scope_label: "Full record",
  window_start: "2023-01-03",
  window_end: "2026-07-05",
};

export const goldenPositionsPayload = {
  scope_metadata: scopeMetadata,
  positions: [
    positionRow({
      domain: "NATIONAL_SECURITY_FOREIGN",
      recorded_votes: 7,
      interpreted_support_count: 1,
      interpreted_oppose_count: 5,
      interpreted_other_count: 1,
    }),
    positionRow({
      domain: "ECONOMY_TAXES",
      recorded_votes: 5,
      interpreted_support_count: 0,
      interpreted_oppose_count: 5,
      interpreted_other_count: 0,
    }),
    positionRow({
      domain: "JUSTICE_PUBLIC_SAFETY",
      recorded_votes: 5,
      interpreted_support_count: 1,
      interpreted_oppose_count: 4,
      interpreted_other_count: 0,
    }),
    positionRow({
      domain: "IMMIGRATION_BORDER",
      recorded_votes: 4,
      interpreted_support_count: 2,
      interpreted_oppose_count: 2,
      interpreted_other_count: 0,
    }),
    positionRow({
      domain: "HEALTH_SOCIAL",
      recorded_votes: 10,
      interpreted_support_count: 0,
      interpreted_oppose_count: 1,
      interpreted_other_count: 0,
    }),
    positionRow({
      domain: "EDUCATION_WORKFORCE",
      recorded_votes: 10,
      interpreted_support_count: 2,
      interpreted_oppose_count: 0,
      interpreted_other_count: 0,
    }),
  ],
};

export const goldenFingerprintPayload = {
  fingerprint: goldenPositionsPayload.positions.map((row) => ({
    domain: row.domain,
    total_votes: 41,
    vote_share: row.recorded_votes / 41,
  })),
};

export const limitedEvidencePositionsPayload = {
  scope_metadata: scopeMetadata,
  positions: [
    positionRow({
      domain: "NATIONAL_SECURITY_FOREIGN",
      recorded_votes: 10,
      interpreted_support_count: 0,
      interpreted_oppose_count: 1,
      interpreted_other_count: 0,
    }),
    positionRow({
      domain: "ECONOMY_TAXES",
      recorded_votes: 10,
      interpreted_support_count: 2,
      interpreted_oppose_count: 0,
      interpreted_other_count: 0,
    }),
  ],
};

export const limitedEvidenceFingerprintPayload = {
  fingerprint: limitedEvidencePositionsPayload.positions.map((row) => ({
    domain: row.domain,
    total_votes: 20,
    vote_share: row.recorded_votes / 20,
  })),
};

export const goldenEvidenceByDomain = {
  NATIONAL_SECURITY_FOREIGN: evidencePayload("NATIONAL_SECURITY_FOREIGN", [
    voteRow({ rollcall_number: 101, issue_facet: "Defense authorization amendment", position: "nay", unsafe: true }),
    voteRow({ rollcall_number: 102, issue_facet: "foreign_military_sales", position: "nay", unsafe: true }),
    voteRow({ rollcall_number: 103, issue_facet: "Veterans cemetery administration", position: "nay" }),
    voteRow({ rollcall_number: 104, issue_facet: "national_security_foreign", position: "nay" }),
    voteRow({ rollcall_number: 105, issue_facet: "defense_authorization", position: "nay" }),
    voteRow({ rollcall_number: 106, issue_facet: "war_powers_votes", position: "yea" }),
    voteRow({
      rollcall_number: 107,
      issue_facet: "House amendment vote",
      interpretation_status: "ambiguous",
      position: "nay",
      vote_type: "amendment",
      unsafe: true,
    }),
  ]),
  ECONOMY_TAXES: evidencePayload("ECONOMY_TAXES", [
    voteRow({ rollcall_number: 201, issue_facet: "budget_reconciliation_and_debt_limit", position: "nay" }),
    voteRow({ rollcall_number: 202, issue_facet: "small_business_loan_eligibility", position: "nay" }),
    voteRow({ rollcall_number: 203, issue_facet: "military_construction_and_va_appropriations", position: "nay" }),
    voteRow({ rollcall_number: 204, issue_facet: "temporary_government_funding", position: "nay" }),
    voteRow({ rollcall_number: 205, issue_facet: "government_funding_and_shutdown", position: "nay" }),
  ]),
  JUSTICE_PUBLIC_SAFETY: evidencePayload("JUSTICE_PUBLIC_SAFETY", [
    voteRow({ rollcall_number: 301, issue_facet: "fentanyl_scheduling_and_penalties", position: "nay" }),
    voteRow({ rollcall_number: 302, issue_facet: "federal_law_enforcement_equipment", position: "nay" }),
    voteRow({ rollcall_number: 303, issue_facet: "law_enforcement_safety_reporting", position: "yea" }),
    voteRow({ rollcall_number: 304, issue_facet: "dc_police_pursuit_policy", position: "nay" }),
    voteRow({ rollcall_number: 305, issue_facet: "dc_policing_reform_repeal", position: "nay" }),
  ]),
  IMMIGRATION_BORDER: evidencePayload("IMMIGRATION_BORDER", [
    voteRow({ rollcall_number: 401, issue_facet: "immigration_border", position: "nay" }),
    voteRow({ rollcall_number: 402, issue_facet: "immigration_border", position: "nay" }),
    voteRow({ rollcall_number: 403, issue_facet: "dc_immigration_information_sharing", position: "yea" }),
    voteRow({ rollcall_number: 404, issue_facet: "immigration_enforcement", position: "yea" }),
  ]),
  HEALTH_SOCIAL: evidencePayload("HEALTH_SOCIAL", [
    voteRow({ rollcall_number: 501, issue_facet: "health_insurance_premiums", position: "nay" }),
  ]),
  EDUCATION_WORKFORCE: evidencePayload("EDUCATION_WORKFORCE", [
    voteRow({ rollcall_number: 601, issue_facet: "school_foreign_funding_and_contract_restrictions", position: "yea" }),
    voteRow({ rollcall_number: 602, issue_facet: "school_foreign_influence_parent_notifications", position: "yea" }),
  ]),
};

export const goldenFixtureData = {
  fingerprint: goldenFingerprintPayload,
  positions: goldenPositionsPayload,
};

export const goldenIssueFixtureData = {
  positions: goldenPositionsPayload,
  evidenceByDomain: goldenEvidenceByDomain,
};

export const limitedEvidenceFixtureData = {
  fingerprint: limitedEvidenceFingerprintPayload,
  positions: limitedEvidencePositionsPayload,
};

export const limitedEvidenceIssueFixtureData = {
  positions: limitedEvidencePositionsPayload,
  evidenceByDomain: {
    NATIONAL_SECURITY_FOREIGN: evidencePayload("NATIONAL_SECURITY_FOREIGN", [
      voteRow({ rollcall_number: 701, issue_facet: "national_security_foreign", position: "nay" }),
    ]),
    ECONOMY_TAXES: evidencePayload("ECONOMY_TAXES", [
      voteRow({ rollcall_number: 801, issue_facet: "economy_taxes", position: "yea" }),
      voteRow({ rollcall_number: 802, issue_facet: "economy_taxes", position: "yea" }),
    ]),
  },
};

export const goldenRecordAcrossResponse = sanitizeRecordAcrossResponse({
  product_framing: "Record Across Congresses",
  legislator_identifier: goldenLegislator.id,
  supported_congresses: [118, 119],
  legislator: {
    legislator_identifier: goldenLegislator.id,
    chamber: "house",
    name_display: goldenLegislator.name_display,
  },
  summary: {
    record_across_congresses_available: true,
    display_eligible_family_count: 1,
    directly_comparable_display_eligible_family_count: 1,
    conditionally_comparable_display_eligible_family_count: 0,
  },
  families: [
    {
      family_id: "golden_security_family",
      family_name: "Defense authorization family",
      issue_domain: "NATIONAL_SECURITY_FOREIGN",
      comparability_status: "directly_comparable",
      governing_question: "Whether reviewed defense authorization votes appear in both Congresses.",
      comparability_caveat: "Counts are shown by Congress and do not infer movement over time.",
      record_across_congresses_available: true,
      roll_call_ids_considered_by_congress: {
        118: ["golden-101"],
        119: ["golden-106"],
      },
      family_evidence_counts_by_congress: {
        118: counts({ cast_substantive_no_count: 1 }),
        119: counts({ cast_substantive_yes_count: 1 }),
      },
    },
  ],
});

function positionRow(overrides = {}) {
  const support = Number(overrides.interpreted_support_count || 0);
  const oppose = Number(overrides.interpreted_oppose_count || 0);
  const total = support + oppose || 1;
  return {
    domain: "NATIONAL_SECURITY_FOREIGN",
    recorded_votes: 0,
    interpreted_support_count: 0,
    interpreted_oppose_count: 0,
    interpreted_other_count: 0,
    yea_share: support / total,
    nay_share: oppose / total,
    ...overrides,
  };
}

function evidencePayload(domain, rows) {
  return {
    domain,
    evidence: rows.map((row) => ({
      issue_domain: domain,
      ...row,
    })),
  };
}

function voteRow({
  interpretation_status = "interpreted",
  issue_facet,
  position,
  rollcall_number,
  unsafe = false,
  vote_type = "final_passage",
}) {
  const supported = position === "yea";
  const title = `${formatFacetTitle(issue_facet)} fixture measure ${rollcall_number}`;
  return {
    roll_call_id: `golden-${rollcall_number}`,
    rollcall_number,
    vote_date: `2025-0${(rollcall_number % 8) + 1}-15`,
    chamber: "house",
    description: title,
    question: title,
    issue_facet,
    interpretation_status,
    position,
    support_position: "yea",
    oppose_position: "nay",
    plain_english_summary: unsafe ? "the House voted on whether to agree to Amendment No. 7" : `${title} had reviewed public meaning.`,
    policy_effect: unsafe ? "the amendment decreases and the amendment redirects funds" : `${title} affected the reviewed policy area.`,
    what_happened: unsafe ? "this was a direct vote on an internal raw evidence string" : `${title} was reviewed as a countable measure.`,
    why_it_mattered: unsafe ? "records a direct position from source basis metadata" : `${title} records a vote with public context.`,
    uncertainty_note: unsafe ? "classification reason should stay in details only" : "",
    interpretation_reason: unsafe ? "source basis should stay in details only" : "",
    classification_reason: "policy_vote",
    source_basis: unsafe ? [{ field: "source_basis", source: "source basis fixture" }] : [{ field: "summary", source: "fixture public source" }],
    source_url: "https://example.com/source",
    vote_type,
    vote_context: {
      vote_type,
      final_result: supported ? "passed" : "failed",
      vote_margin: 12,
      member_party: "D",
      member_voted_with_party_majority: true,
      member_voted_with_winning_side: supported,
      member_party_majority_position: position,
    },
  };
}

function formatFacetTitle(value) {
  return String(value || "reviewed")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function counts(overrides = {}) {
  return {
    cast_substantive_yes_count: 0,
    cast_substantive_no_count: 0,
    not_voting_count: 0,
    present_count: 0,
    missing_no_record_count: 0,
    ...overrides,
  };
}
