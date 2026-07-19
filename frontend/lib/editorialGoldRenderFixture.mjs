export const editorialGoldLegislator = {
  id: "leg_valerie_p_foushee",
  bioguide_id: "F000477",
  name_display: "Valerie P. Foushee",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};


const editorialRows = [
  editorialRow({ roll: 310, date: "2025-12-03", position: "not_voting", title: "Small Business Regulatory Reduction Act" }),
  editorialRow({ roll: 285, date: "2025-11-12", position: "nay", title: "Continuing Appropriations, Agriculture, Legislative Branch, and Military Construction and Veterans Affairs Appropriations Act, 2026" }),
  editorialRow({ roll: 281, date: "2025-09-19", position: "nay", title: "Continuing Appropriations and Extensions Act, 2026" }),
  editorialRow({ roll: 263, date: "2025-09-10", position: "yea", status: "ambiguous", title: "Motion to instruct conferees on H.R. 3944", voteType: "procedural" }),
  editorialRow({ roll: 182, date: "2025-06-25", position: "nay", title: "Military Construction, Veterans Affairs, and Related Agencies Appropriations Act, 2026" }),
  editorialRow({ roll: 180, date: "2025-06-25", position: "nay", status: "ambiguous", title: "Carter amendments en bloc No. 2 to H.R. 3944", voteType: "amendment" }),
  editorialRow({ roll: 156, date: "2025-06-05", position: "nay", title: "American Entrepreneurs First Act of 2025" }),
  editorialRow({ roll: 100, date: "2025-04-10", position: "nay", title: "Concurrent resolution on the budget for fiscal year 2025 — Senate-revised framework", voteType: "amendment" }),
  editorialRow({ roll: 50, date: "2025-02-25", position: "nay", title: "Concurrent resolution on the budget for fiscal year 2025 — initial House framework", voteType: "other" }),
  {
    ...editorialRow({ roll: 999, date: "2024-06-01", position: "nay", status: "ambiguous", title: "Additional limited-context economy fixture" }),
    congress: 118,
  },
];


export const editorialGoldIssueFixtureData = {
  positions: {
    scope_metadata: {
      congresses: [118, 119],
      requested_congresses: [118, 119],
      scope_label: "Full record",
      window_start: "2024-06-01",
      window_end: "2025-12-03",
    },
    positions: [
      {
        domain: "ECONOMY_TAXES",
        recorded_votes: editorialRows.length,
        interpreted_support_count: 0,
        interpreted_oppose_count: 6,
        interpreted_other_count: 4,
        yea_share: 0,
        nay_share: 1,
      },
    ],
  },
  evidenceByDomain: {
    ECONOMY_TAXES: {
      domain: "ECONOMY_TAXES",
      evidence: editorialRows,
    },
  },
};


function editorialRow({ date, position, roll, status = "interpreted", title, voteType = "final_passage" }) {
  return {
    roll_call_id: `editorial-${roll}`,
    congress: 119,
    rollcall_number: roll,
    vote_date: date,
    chamber: "house",
    description: title,
    question: title,
    issue_domain: "ECONOMY_TAXES",
    issue_facet: "economy_taxes",
    interpretation_status: status,
    position,
    support_position: "yea",
    oppose_position: "nay",
    plain_english_summary: `${title} fixture row.`,
    policy_effect: `${title} fixture effect.`,
    what_happened: `${title} fixture action.`,
    why_it_mattered: `${title} fixture stakes.`,
    uncertainty_note: status === "interpreted" ? "" : "Kept as context rather than a substantive policy finding.",
    interpretation_reason: status === "interpreted" ? "policy_vote" : "context_only",
    classification_reason: status === "interpreted" ? "policy_vote" : "limited_context",
    source_basis: [],
    source_url: `https://clerk.house.gov/evs/2025/roll${String(roll).padStart(3, "0")}.xml`,
    vote_type: voteType,
    vote_context: {
      vote_type: voteType,
      final_result: roll === 263 ? "failed" : "passed",
      vote_margin: 4,
      member_party: "D",
      member_voted_with_party_majority: true,
      member_voted_with_winning_side: false,
      member_party_majority_position: position,
    },
  };
}
