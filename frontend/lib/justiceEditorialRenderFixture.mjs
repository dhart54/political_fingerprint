import { editorialGoldLegislator } from "./editorialGoldRenderFixture.mjs";

export const justiceEditorialLegislator = editorialGoldLegislator;

const definitions = [
  [32, "2025-02-06", "yea", "Trahan amendment No. 2 to H.R. 27", "amendment", "failed"],
  [33, "2025-02-06", "nay", "HALT Fentanyl Act", "final_passage", "passed"],
  [130, "2025-05-15", "nay", "Federal Law Enforcement Officer Service Weapon Purchase Act", "final_passage", "passed"],
  [131, "2025-05-15", "yea", "Improving Law Enforcement Officer Safety and Wellness Through Data Act", "final_passage", "passed"],
  [160, "2025-06-10", "nay", "Previous question on H. Res. 489", "procedural", "passed", "On Ordering the Previous Question"],
  [161, "2025-06-10", "nay", "Adoption of H. Res. 489", "procedural", "passed", "On Agreeing to the Resolution"],
  [166, "2025-06-12", "yea", "HALT Fentanyl Act (S. 331)", "final_passage", "passed"],
  [267, "2025-09-16", "nay", "Previous question on H. Res. 707", "procedural", "passed", "On Ordering the Previous Question"],
  [268, "2025-09-16", "nay", "Adoption of H. Res. 707", "procedural", "passed", "On Agreeing to the Resolution"],
  [275, "2025-09-17", "nay", "D.C. Policing Protection Act", "final_passage", "passed"],
  [290, "2025-11-18", "nay", "Previous question on H. Res. 879", "procedural", "passed", "On Ordering the Previous Question"],
  [291, "2025-11-18", "nay", "Adoption of H. Res. 879", "procedural", "passed", "On Agreeing to the Resolution"],
  [299, "2025-11-19", "nay", "CLEAN DC Act", "final_passage", "passed"],
];

const rows = definitions.map(([roll, date, position, title, voteType, result, question = title]) => ({
  roll_call_id: `justice-editorial-${roll}`,
  congress: 119,
  rollcall_number: roll,
  vote_date: date,
  chamber: "house",
  description: title,
  question,
  issue_domain: "JUSTICE_PUBLIC_SAFETY",
  issue_facet: voteType === "procedural" ? "floor_rule_for_multiple_bills" : "justice_public_safety",
  interpretation_status: voteType === "procedural" ? "ambiguous" : "interpreted",
  position,
  support_position: "yea",
  oppose_position: "nay",
  plain_english_summary: voteType === "procedural" ? `${question} on a rule governing floor consideration of multiple measures.` : `${title} fixture row.`,
  policy_effect: `${title} fixture effect.`,
  what_happened: `${title} fixture action.`,
  why_it_mattered: `${title} fixture stakes.`,
  uncertainty_note: voteType === "procedural" ? "This floor-process action is retained as procedural context." : "",
  interpretation_reason: voteType === "procedural" ? "procedural_context" : "policy_vote",
  classification_reason: voteType === "procedural" ? "procedural_context" : "policy_vote",
  source_basis: [],
  source_url: `https://clerk.house.gov/Votes/2025${roll}`,
  vote_type: voteType,
  vote_context: { vote_type: voteType, question, final_result: result, member_party: "D", member_voted_with_party_majority: true },
}));

export const justiceEditorialIssueFixtureData = {
  positions: {
    scope_metadata: { congresses: [119], requested_congresses: [119], scope_label: "119th Congress", window_start: "2025-02-06", window_end: "2025-11-19" },
    positions: [{ domain: "JUSTICE_PUBLIC_SAFETY", recorded_votes: 13, interpreted_support_count: 3, interpreted_oppose_count: 4, interpreted_other_count: 6 }],
  },
  evidenceByDomain: { JUSTICE_PUBLIC_SAFETY: { domain: "JUSTICE_PUBLIC_SAFETY", evidence: rows } },
};
