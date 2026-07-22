import assert from "node:assert/strict";
import test from "node:test";

import { buildLimitedContextSummary } from "./voteCardSummary.mjs";
import { buildIssueOverview, formatRenderedIssueOverview } from "./issueOverview.mjs";
import { isProceduralContextRow } from "./proceduralContext.mjs";
import { justiceEditorialIssueFixtureData } from "./justiceEditorialRenderFixture.mjs";

test("procedural-context vote cards explain floor process without support or opposition claims", () => {
  const row = proceduralRow({
    bill_id: "119:hres:489",
    bill_title: "Providing for consideration of several measures",
    question: "On Ordering the Previous Question",
    rollcall_number: 160,
  });

  const summary = buildLimitedContextSummary(row);

  assert.equal(isProceduralContextRow(row), true);
  assert.match(summary, /Procedural-context row/);
  assert.match(summary, /explain floor process/);
  assert.match(summary, /not counted as support or opposition/);
  assert.match(summary, /should not be read as final passage/);
  assert.doesNotMatch(summary, /supported the underlying|opposed the underlying|alignment|misalignment|you should vote/i);
});

test("procedural-context rows do not over-promote issue readiness", () => {
  const rows = [
    interpretedRow({
      rollcall_number: 101,
      issue_facet: "fentanyl_scheduling_and_penalties",
      what_happened: "The House passed the HALT Fentanyl Act.",
      why_it_mattered: "The vote concerned fentanyl-related substance scheduling and penalties.",
    }),
    proceduralRow({
      bill_id: "119:hres:489",
      rollcall_number: 160,
      question: "On Ordering the Previous Question",
    }),
    proceduralRow({
      bill_id: "119:hres:489",
      rollcall_number: 161,
      question: "On Agreeing to the Resolution",
    }),
  ];

  const overview = buildIssueOverview(rows, {
    domain: "JUSTICE_PUBLIC_SAFETY",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.votePattern.interpretedYesNoCount, 1);
  assert.equal(overview.votePattern.supportCount, 1);
  assert.equal(overview.votePattern.opposeCount, 0);
  assert.equal(overview.votePattern.proceduralContextCount, 2);
  assert.equal(overview.readiness.status, "limited");
  assert.ok(overview.readiness.reasons.includes("too_few_counted_interpreted_yes_no_rows"));
  assert.match(rendered, /limited interpreted evidence/);
  assert.match(rendered, /procedural-context/);
  assert.doesNotMatch(rendered, /consistently supported the measures|broadly supports|direct position on the underlying/i);
});

test("explicit non-interpreted procedural type classifies without phrase matching", () => {
  assert.equal(isProceduralContextRow({
    interpretation_status: "ambiguous",
    vote_type: "procedural",
    description: "Floor action 12",
  }), true);
});

test("interpreted substantive row is never overridden by procedural metadata or title", () => {
  assert.equal(isProceduralContextRow({
    interpretation_status: "interpreted",
    vote_type: "procedural",
    description: "Motion with procedural language but reviewed substantive meaning",
  }), false);
});

test("all six Justice controls classify as floor-process context in production fallback", () => {
  const rows = justiceEditorialIssueFixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence;
  const controls = rows.filter((row) => row.interpretation_status !== "interpreted");
  assert.deepEqual(controls.map((row) => row.rollcall_number), [160, 161, 267, 268, 290, 291]);
  assert.ok(controls.every(isProceduralContextRow));
  assert.ok(controls.every((row) => row.classification_reason === "procedural_context"));

  const overview = buildIssueOverview(rows, { domain: "JUSTICE_PUBLIC_SAFETY", representativeName: "Example Member" });
  const rendered = formatRenderedIssueOverview(overview);
  assert.equal(overview.votePattern.proceduralContextCount, 6);
  assert.match(rendered, /Six procedural-context rows remain visible/i);
  assert.match(rendered, /explain floor process/i);
  assert.doesNotMatch(rendered, /source text does not clearly explain|failed to explain/i);
});

function proceduralRow(overrides = {}) {
  return {
    interpretation_status: "insufficient_evidence",
    issue_facet: "house_of_representatives",
    position: "nay",
    support_position: null,
    oppose_position: null,
    uncertainty_note: "The vote was procedural and tied to floor consideration of multiple bills.",
    vote_context: {
      final_result: "passed",
      member_party: "D",
      member_voted_with_party_majority: true,
      member_voted_with_winning_side: false,
      vote_type: "rule",
    },
    ...overrides,
  };
}

function interpretedRow(overrides = {}) {
  return {
    interpretation_status: "interpreted",
    issue_facet: "fentanyl_scheduling_and_penalties",
    position: "yea",
    support_position: "yea",
    oppose_position: "nay",
    vote_context: {
      final_result: "passed",
      member_party: "D",
      member_voted_with_party_majority: false,
      member_voted_with_winning_side: true,
      vote_type: "final_passage",
    },
    ...overrides,
  };
}
