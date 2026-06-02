import assert from "node:assert/strict";
import test from "node:test";

import { buildIssueOverview, formatRenderedIssueOverview } from "./issueOverview.mjs";

const partyOutcomeContext = {
  member_party: "D",
  member_voted_with_party_majority: true,
  member_voted_with_winning_side: false,
};

const valerieEconomyRows = [
  row({
    description: "Establishing the congressional budget for the United States Government for fiscal year 2025",
    issue_facet: "budget_reconciliation_and_debt_limit",
    policy_effect: "Budget instructions for later tax, spending, deficit, and debt-limit legislation.",
    rollcall_number: 50,
    what_happened: "The House adopted a budget blueprint that started reconciliation instructions for later budget legislation.",
    why_it_mattered: "The vote opened a fast-track process for later tax, spending, deficit, and debt-limit legislation.",
  }),
  row({
    description: "Establishing the congressional budget for the United States Government for fiscal year 2025",
    issue_facet: "budget_reconciliation_and_debt_limit",
    policy_effect: "Reconciliation instructions for later tax, spending, deficit, and debt-limit legislation.",
    rollcall_number: 100,
    what_happened: "The House agreed to the Senate-amended budget framework for FY2025-FY2034 reconciliation instructions.",
    why_it_mattered: "The vote kept the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation.",
  }),
  row({
    description: "American Entrepreneurs First Act",
    issue_facet: "small_business_loan_eligibility",
    policy_effect: "Eligibility rules for SBA 7(a) and 504 loans.",
    rollcall_number: 156,
    what_happened: "The House passed a bill changing eligibility requirements for SBA 7(a) and 504 small-business loans.",
    why_it_mattered: "The vote concerned whether certain SBA-backed business loans should be limited to citizens, nationals, or lawful permanent residents.",
  }),
  row({
    description: "Carter of Texas Amendment En Bloc No. 2",
    interpretation_status: "ambiguous",
    issue_facet: "appropriations_amendment",
    policy_effect: "",
    rollcall_number: 180,
    uncertainty_note: "The official amendment text was not clear enough to explain the practical change.",
  }),
  row({
    description: "Military Construction, Veterans Affairs, and Related Agencies Appropriations Act, 2026",
    issue_facet: "military_construction_and_va_appropriations",
    policy_effect: "Annual appropriations for military construction and Veterans Affairs programs.",
    rollcall_number: 182,
    what_happened: "The House passed an FY2026 appropriations bill for military construction, Veterans Affairs, and related agencies.",
    why_it_mattered: "The vote concerned House approval of funding for military construction, military housing, veterans benefits, veterans health programs, and related agencies.",
  }),
  row({
    description: "DeLauro Motion to Instruct Conferees",
    interpretation_status: "ambiguous",
    issue_facet: "conference_instruction",
    position: "yea",
    rollcall_number: 263,
    uncertainty_note: "The source did not include enough official instruction text to describe the exact policy effect.",
  }),
  row({
    description: "Continuing Appropriations and Extensions Act, 2026",
    issue_facet: "temporary_government_funding",
    policy_effect: "Continuing appropriations to keep agencies operating temporarily.",
    rollcall_number: 281,
    what_happened: "The House passed an initial short-term FY2026 funding bill before later Senate changes.",
    why_it_mattered: "The vote concerned whether to keep most federal agencies operating temporarily while regular appropriations bills were still unfinished.",
  }),
  row({
    description: "Continuing Appropriations and Extensions Act, 2026",
    issue_facet: "government_funding_and_shutdown",
    policy_effect: "Funding terms for reopening or continuing federal operations.",
    rollcall_number: 285,
    what_happened: "The House agreed to the Senate-amended funding package that ended the 2025 shutdown and sent the measure to the President.",
    why_it_mattered: "The vote affected whether federal operations would reopen or continue.",
  }),
  row({
    description: "Small Business Regulatory Reduction Act",
    issue_facet: "small_business_regulation",
    policy_effect: "A cap on net new SBA regulatory costs for small businesses.",
    position: "not_voting",
    rollcall_number: 310,
    support_position: "yea",
    what_happened: "The House passed a bill that would require the Small Business Administration to keep its annual small-business regulatory budget at zero or below.",
    why_it_mattered: "The vote concerned how much new regulatory cost the SBA could impose on small businesses through its own rulemaking.",
  }),
];

test("Valerie Foushee Economy & Taxes overview names required measure groups and limits", () => {
  const overview = buildIssueOverview(valerieEconomyRows, {
    domain: "ECONOMY_TAXES",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.votePattern.interpretedYesNoCount, 6);
  assert.equal(overview.votePattern.opposeCount, 6);
  assert.equal(overview.votePattern.supportCount, 0);
  assert.equal(overview.votePattern.notVotingCount, 1);
  assert.equal(overview.votePattern.ambiguousCount, 2);

  for (const expected of [
    "budget framework",
    "tax, spending, deficit, and debt-limit legislation",
    "SBA 7\\(a\\) and 504 loan eligibility",
    "citizenship or lawful-residency status",
    "military construction",
    "military housing",
    "veterans benefits",
    "Veterans Affairs",
    "temporary government funding",
    "shutdown-ending",
    "not-voting row",
    "ambiguous or limited-context rows",
  ]) {
    assert.match(rendered, new RegExp(expected, "i"));
  }

  assert.match(rendered, /If you generally favored these House Republican packages/);
  assert.match(rendered, /The vote record alone does not show her motive/);
  assert.doesNotMatch(rendered, /stored vote context|for-side|against-side|reviewed yes\/no|plus other reviewed measures|leans Nay|is corrupt|character judgment|you should vote|support this candidate|oppose this candidate/i);
});

function row(overrides) {
  return {
    interpretation_status: "interpreted",
    issue_facet: "",
    position: "nay",
    support_position: "yea",
    oppose_position: "nay",
    vote_context: partyOutcomeContext,
    ...overrides,
  };
}
