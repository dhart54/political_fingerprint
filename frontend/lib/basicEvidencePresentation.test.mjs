import assert from "node:assert/strict";
import test from "node:test";

import {
  BASIC_EVIDENCE_STATE,
  buildBasicEvidencePresentation,
  hasAvailableIssueEvidence,
  issueAvailabilityLabel,
} from "./basicEvidencePresentation.mjs";

test("basic evidence preserves directional and non-directional states without a conclusion", () => {
  const result = buildBasicEvidencePresentation([
    row({ position: "yea" }),
    row({ position: "nay" }),
    row({ position: "present" }),
    row({ position: "not_voting" }),
    row({ interpretation_status: "ambiguous" }),
  ]);

  assert.equal(result.state, BASIC_EVIDENCE_STATE.voteEvidence);
  assert.equal(result.substantiveVotes, 2);
  assert.equal(result.present, 1);
  assert.equal(result.notVoting, 1);
  assert.equal(result.limitedRecords, 1);
  assert.match(result.message, /does not combine them into a broader issue conclusion/);
  assert.doesNotMatch(result.message, /mostly|pattern|supports|opposes/i);
});

test("procedural-only rows remain context and never become a policy position", () => {
  const result = buildBasicEvidencePresentation([
    row({ interpretation_status: "ambiguous", vote_type: "procedural" }),
    row({
      interpretation_status: "ambiguous",
      issue_facet: "house_of_representatives",
      question: "Providing for consideration of several measures",
      vote_type: "rule",
    }),
  ]);

  assert.equal(result.state, BASIC_EVIDENCE_STATE.proceduralContextOnly);
  assert.equal(result.proceduralRecords, 2);
  assert.equal(result.substantiveVotes, 0);
  assert.match(result.message, /do not establish a direct position/);
});

test("issue availability follows actual evidence counts, including non-directional-only records", () => {
  const directional = { recorded_votes: 1, total_votes: 1, yea_count: 1 };
  const nonDirectional = { recorded_votes: 0, total_votes: 1, other_count: 1 };
  const noEvidence = { recorded_votes: 0, total_votes: 0, interpreted_support_count: 1 };

  assert.equal(hasAvailableIssueEvidence(directional), true);
  assert.equal(issueAvailabilityLabel(directional), "Vote evidence");
  assert.equal(hasAvailableIssueEvidence(nonDirectional), true);
  assert.equal(issueAvailabilityLabel(nonDirectional), "Non-directional evidence");
  assert.equal(hasAvailableIssueEvidence(noEvidence), false);
  assert.equal(issueAvailabilityLabel(noEvidence), "No evidence");
});

function row(overrides = {}) {
  return {
    interpretation_status: "interpreted",
    position: "yea",
    vote_type: "final_passage",
    ...overrides,
  };
}
