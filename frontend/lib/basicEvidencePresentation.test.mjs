import assert from "node:assert/strict";
import test from "node:test";

import {
  BASIC_EVIDENCE_STATE,
  buildBasicEvidencePresentation,
  issueAvailabilityLabel,
} from "./basicEvidencePresentation.mjs";

test("basic evidence preserves directional and non-directional states without a conclusion", () => {
  const result = buildBasicEvidencePresentation([
    row({ position: "yea" }),
    row({ position: "nay" }),
    row({ position: "present" }),
    row({ position: "not_voting" }),
    row({ evidence_status: "missing_evidence", interpretation_status: "missing" }),
    row({ interpretation_status: "ambiguous" }),
  ]);

  assert.equal(result.state, BASIC_EVIDENCE_STATE.voteEvidence);
  assert.equal(result.substantiveVotes, 2);
  assert.equal(result.present, 1);
  assert.equal(result.notVoting, 1);
  assert.equal(result.missingEvidence, 1);
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

test("issue availability is derived only from reviewed evidence presence", () => {
  assert.equal(issueAvailabilityLabel({ interpreted_support_count: 1 }), "Vote evidence");
  assert.equal(issueAvailabilityLabel({ interpreted_other_count: 3 }), "Limited record");
});

function row(overrides = {}) {
  return {
    interpretation_status: "interpreted",
    position: "yea",
    vote_type: "final_passage",
    ...overrides,
  };
}
