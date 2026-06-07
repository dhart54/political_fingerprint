import assert from "node:assert/strict";
import test from "node:test";

import { deriveEvidenceGroups } from "./evidenceGrouping.mjs";
import { buildIssueOverview, formatRenderedIssueOverview } from "./issueOverview.mjs";

const partyOutcomeContext = {
  member_party: "D",
  member_voted_with_party_majority: true,
  member_voted_with_winning_side: false,
};

test("groups repeated rows by stable bill identifier and preserves row roles", () => {
  const rows = [
    row({
      bill_id: "119:hr:22",
      bill_title: "National Defense Authorization Act",
      description: "National Defense Authorization Act",
      issue_facet: "Defense authorization",
      rollcall_number: 200,
      vote_context: { ...partyOutcomeContext, vote_type: "final_passage" },
    }),
    row({
      bill_id: "119:hr:22",
      bill_title: "National Defense Authorization Act",
      description: "Motion to Commit",
      issue_facet: "Motion to commit",
      rollcall_number: 201,
      vote_context: { ...partyOutcomeContext, vote_type: "motion" },
    }),
    row({
      bill_id: "119:hr:22",
      bill_title: "National Defense Authorization Act",
      description: "Defense authorization amendment",
      interpretation_status: "insufficient_evidence",
      issue_facet: "Defense authorization amendment",
      rollcall_number: 202,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The amendment source text does not explain the full practical policy effect.",
      vote_context: { ...partyOutcomeContext, vote_type: "amendment" },
    }),
  ];

  const grouping = deriveEvidenceGroups(rows);
  const group = grouping.groups[0];

  assert.equal(grouping.summary.totalRows, 3);
  assert.equal(grouping.summary.totalGroups, 1);
  assert.equal(grouping.summary.repeatedGroupCount, 1);
  assert.equal(grouping.summary.countedYesNoRows, 2);
  assert.equal(grouping.summary.ambiguousOrInsufficientRows, 1);
  assert.equal(grouping.summary.proceduralRows, 1);
  assert.equal(grouping.summary.amendmentRows, 1);
  assert.equal(group.id, "bill:119:hr:22");
  assert.equal(group.category, "related_floor_or_procedural_votes");
  assert.match(group.scanSummary, /including 1 procedural row/);
});

test("does not group unrelated rows only because they share a broad issue facet", () => {
  const rows = [
    row({
      description: "Foreign military sale to Country A",
      issue_facet: "foreign_military_sales",
      rollcall_number: 10,
    }),
    row({
      description: "Foreign military sale to Country B",
      issue_facet: "foreign_military_sales",
      rollcall_number: 11,
    }),
  ];

  const grouping = deriveEvidenceGroups(rows);

  assert.equal(grouping.summary.totalRows, 2);
  assert.equal(grouping.summary.totalGroups, 2);
  assert.equal(grouping.summary.repeatedGroupCount, 0);
  assert.deepEqual(
    grouping.groups.map((group) => group.rollCalls.map((rollCall) => rollCall.rollcall_number)),
    [[10], [11]],
  );
});

test("issue overview exposes grouping metadata without changing approved counts or copy", () => {
  const rows = [
    row({
      bill_id: "119:hconres:14",
      description: "Establishing the congressional budget for the United States Government for fiscal year 2025",
      issue_facet: "budget_reconciliation_and_debt_limit",
      policy_effect: "Budget instructions for later tax, spending, deficit, and debt-limit legislation.",
      rollcall_number: 50,
      what_happened: "The House adopted a budget blueprint that started reconciliation instructions for later budget legislation.",
      why_it_mattered: "The vote opened a fast-track process for later tax, spending, deficit, and debt-limit legislation.",
    }),
    row({
      bill_id: "119:hconres:14",
      description: "Establishing the congressional budget for the United States Government for fiscal year 2025",
      issue_facet: "budget_reconciliation_and_debt_limit",
      policy_effect: "Reconciliation instructions for later tax, spending, deficit, and debt-limit legislation.",
      rollcall_number: 100,
      what_happened: "The House agreed to the Senate-amended budget framework for FY2025-FY2034 reconciliation instructions.",
      why_it_mattered: "The vote kept the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation.",
    }),
    row({
      description: "Carter of Texas Amendment En Bloc No. 2",
      interpretation_status: "ambiguous",
      issue_facet: "appropriations_amendment",
      policy_effect: "",
      rollcall_number: 180,
      uncertainty_note: "The official amendment text was not clear enough to explain the practical change.",
    }),
  ];

  const overview = buildIssueOverview(rows, {
    domain: "ECONOMY_TAXES",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.votePattern.interpretedYesNoCount, 2);
  assert.equal(overview.votePattern.opposeCount, 2);
  assert.equal(overview.votePattern.ambiguousCount, 1);
  assert.equal(overview.evidenceGrouping.summary.totalRows, 3);
  assert.equal(overview.evidenceGrouping.summary.repeatedGroupCount, 1);
  assert.match(rendered, /limited interpreted evidence/);
  assert.match(rendered, /Only 2 reviewed Yes\/No votes could be interpreted/);
});

test("high-risk national security grouping remains limited and does not overinterpret procedural rows", () => {
  const rows = [
    row({
      bill_id: "119:sjres:12",
      bill_title: "Foreign military sale resolution",
      chamber: "senate",
      issue_facet: "foreign_military_sales",
      rollcall_number: 12,
      what_happened: "The Senate voted on whether to allow a specific foreign military sale to proceed.",
      why_it_mattered: "The vote concerned whether to allow or disapprove a specific foreign military sale.",
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "passage" },
    }),
    row({
      bill_id: "119:hr:22",
      bill_title: "National Defense Authorization Act",
      description: "Defense authorization amendment",
      interpretation_status: "insufficient_evidence",
      issue_facet: "Defense authorization amendment",
      rollcall_number: 202,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available source text identifies an amendment but does not explain the full practical policy effect.",
      vote_context: { ...partyOutcomeContext, vote_type: "amendment" },
    }),
    row({
      bill_id: "119:hr:22",
      bill_title: "National Defense Authorization Act",
      description: "House floor procedure",
      interpretation_status: "insufficient_evidence",
      issue_facet: "House floor procedure",
      rollcall_number: 203,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available source text identifies floor procedure rather than a clear final policy choice.",
      vote_context: { ...partyOutcomeContext, vote_type: "rule" },
    }),
  ];

  const overview = buildIssueOverview(rows, {
    domain: "NATIONAL_SECURITY_FOREIGN",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);
  const defenseGroup = overview.evidenceGrouping.groups.find((group) => group.id === "bill:119:hr:22");

  assert.equal(overview.readiness.status, "limited");
  assert.equal(overview.votePattern.interpretedYesNoCount, 1);
  assert.equal(overview.votePattern.ambiguousCount, 2);
  assert.equal(defenseGroup.category, "limited_context_rows");
  assert.equal(defenseGroup.ambiguousOrInsufficientCount, 2);
  assert.match(defenseGroup.scanSummary, /not counted in the summarized pattern/);
  assert.match(rendered, /limited interpreted evidence/);
  assert.match(rendered, /should not be read as a stable pattern/);
  assert.doesNotMatch(rendered, /consistently opposed|consistently supported|you should vote|is corrupt/i);
});

test("procedural-context rows stay visible without becoming counted evidence", () => {
  const rows = [
    row({
      bill_id: "119:hres:489",
      bill_title: "Providing for consideration of several measures",
      description: "On Ordering the Previous Question",
      interpretation_status: "insufficient_evidence",
      issue_facet: "house_of_representatives",
      rollcall_number: 160,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The vote was procedural and tied to floor consideration of multiple bills.",
      vote_context: { ...partyOutcomeContext, vote_type: "rule" },
    }),
    row({
      bill_id: "119:hres:489",
      bill_title: "Providing for consideration of several measures",
      description: "On Agreeing to the Resolution",
      interpretation_status: "insufficient_evidence",
      issue_facet: "house_of_representatives",
      rollcall_number: 161,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The vote was on adopting a House rule resolution.",
      vote_context: { ...partyOutcomeContext, vote_type: "rule" },
    }),
  ];

  const grouping = deriveEvidenceGroups(rows);
  const overview = buildIssueOverview(rows, {
    domain: "JUSTICE_PUBLIC_SAFETY",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(grouping.summary.countedYesNoRows, 0);
  assert.equal(grouping.summary.ambiguousOrInsufficientRows, 2);
  assert.equal(grouping.summary.proceduralContextRows, 2);
  assert.equal(grouping.groups[0].category, "procedural_context_rows");
  assert.match(grouping.groups[0].scanSummary, /procedural context/);
  assert.equal(overview.votePattern.supportCount, 0);
  assert.equal(overview.votePattern.opposeCount, 0);
  assert.equal(overview.votePattern.proceduralContextCount, 2);
  assert.equal(overview.readiness.status, "limited");
  assert.match(rendered, /procedural-context/);
  assert.match(rendered, /not used to summarize support, opposition, or alignment/);
  assert.doesNotMatch(rendered, /consistently opposed|consistently supported|broad Justice|you should vote/i);
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
