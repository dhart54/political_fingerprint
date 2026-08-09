import assert from "node:assert/strict";
import test from "node:test";

import {
  buildLedgerItems,
  buildPatternIndex,
  buildSelectedIssueModel,
  completeVisibleRows,
  getActionPresentation,
  getPublicChamberResult,
  publicActionStatus,
  publicActionStatusKind,
} from "./selectedIssueExperience.mjs";

const presentation = {
  tier: "reviewed_conclusion",
  review_state: {
    congress_scope: [119],
    review_scope: "full_defined_issue_record",
    total_recorded_actions: 37,
    complete_episode_count: 32,
  },
  repeated_patterns: [{
    proposition_id: "pattern-1",
    heading: "A supplied pattern",
    body: "Across two separate episodes, the approved wording describes these actions.",
    direction: "opposition",
    action_ids: ["house:119:2:1", "house:119:2:2"],
  }],
};

test("selected issue model keeps all-Congress evidence distinct from 119th interpretation", () => {
  const model = buildSelectedIssueModel({
    presentation,
    rows: Array.from({ length: 89 }),
    scope: "all",
  });
  assert.equal(model.evidence.label, "All available Congresses");
  assert.equal(model.evidence.count, 89);
  assert.equal(model.interpretation.type, "Full reviewed record");
  assert.equal(model.interpretation.scope, "119th Congress · full defined issue record");
  assert.equal(model.interpretation.congressLabel, "119th Congress");
  assert.equal(model.interpretation.actionCount, 37);
  assert.equal(model.interpretation.episodeCount, 32);
  assert.equal(model.scopesAlign, false);
});

test("scope 118 becomes receipts-only without a governed interpretation", () => {
  const model = buildSelectedIssueModel({
    presentation: { tier: "receipts_only", review_state: null },
    rows: Array.from({ length: 52 }),
    scope: "118",
  });
  assert.equal(model.evidence.label, "118th Congress");
  assert.equal(model.evidence.count, 52);
  assert.equal(model.interpretation, null);
});

test("pattern index derives independent episode counts from governed receipt bindings", () => {
  const patterns = buildPatternIndex(presentation, [
    governedRow(1, "episode-a"),
    governedRow(2, "episode-b"),
  ]);
  assert.equal(patterns[0].actionCount, 2);
  assert.equal(patterns[0].episodeCount, 2);
  assert.equal(patterns[0].statusLabel, "Opposition");
});

test("related parent-measure actions group without losing child actions or controls", () => {
  const rows = [
    ledgerRow(278, "final_passage", { control: true }),
    ledgerRow(275, "amendment"),
    ledgerRow(273, "amendment"),
  ];
  const items = buildLedgerItems(rows);
  assert.equal(items.length, 1);
  assert.equal(items[0].type, "group");
  assert.equal(items[0].rows.length, 3);
  assert.equal(items[0].composition.controls, 1);
  assert.deepEqual(items[0].composition.positions, [{ label: "Nay", count: 3 }]);
  assert.deepEqual(
    items[0].rows.map((row) => row.rollcall_number),
    [278, 275, 273],
  );
});

test("related group composition preserves mixed vote positions", () => {
  const items = buildLedgerItems([
    { ...ledgerRow(278, "final_passage", { control: true }), position: "nay" },
    withVote(ledgerRow(275, "amendment"), "yea"),
    withVote(ledgerRow(273, "amendment"), "not_voting"),
  ]);
  assert.deepEqual(items[0].composition.positions, [
    { label: "Nay", count: 1 },
    { label: "Yea", count: 1 },
    { label: "Not Voting", count: 1 },
  ]);
});

function withVote(row, vote) {
  return {
    ...row,
    position: vote,
    governed_receipt_projection: {
      ...row.governed_receipt_projection,
      member_action: vote,
    },
  };
}

test("pagination completes a related-action group instead of showing a partial group", () => {
  const rows = [
    { rollcall_number: 300, description: "Independent action" },
    ...[278, 275, 273, 265, 259].map((roll) => ledgerRow(roll, "amendment")),
  ];
  assert.equal(completeVisibleRows(rows, 3).length, 6);
});

test("compact action presentation uses amendment purpose and preserves parent measure", () => {
  const row = ledgerRow(275, "amendment");
  const compact = getActionPresentation(row);
  assert.equal(compact.title, "Limit military speed-camera funding");
  assert.equal(compact.parentMeasure, "National Defense Authorization Act for Fiscal Year 2027");
  assert.equal(compact.status, "");
});

test("exceptional action statuses have distinct stable semantic treatments", () => {
  const cases = [
    [{ vote_type: "procedural" }, "Procedural / context", "procedural"],
    [{ governed_receipt_control: { status: "noncounting_control" } }, "Non-counting control", "noncounting"],
    [{ interpretation_status: "ambiguous" }, "Limited context", "limited"],
    [{ interpretation_status: "insufficient_evidence" }, "Unresolved evidence", "unresolved"],
  ];
  for (const [row, label, kind] of cases) {
    assert.equal(publicActionStatus(row), label);
    assert.equal(publicActionStatusKind(label), kind);
  }
  assert.equal(publicActionStatus({ interpretation_status: "interpreted" }), "");
  assert.equal(publicActionStatusKind(""), "");
});

test("a supplied final-passage label remains more specific than fallback question text", () => {
  const compact = getActionPresentation({
    ...ledgerRow(278, "final_passage", { control: true }),
    amendment_purpose: "Final passage after amendments",
    question: "The exact final-package policy question remains unresolved.",
  });
  assert.equal(compact.title, "Final passage after amendments");
  assert.equal(compact.status, "Non-counting control");
});

test("approved exact-action meaning supplies a concise title when official labels are absent", () => {
  const compact = getActionPresentation({
    canonical_action_id: "house:119:2:240",
    chamber: "house",
    congress: 119,
    rollcall_number: 240,
    vote_type: "suspension_passage",
    description: "House roll 240",
    question: "On Passage",
    governed_receipt_projection: {
      exact_action_meaning: "The House choice was whether to pass H.R. 1181, barring payment-card networks from assigning firearm-retailer category codes.",
    },
  });
  assert.equal(compact.title, "The House choice was whether to pass H.R. 1181");
});

test("chamber result supports nested and top-level public response shapes", () => {
  assert.equal(getPublicChamberResult({ vote_context: { final_result: "passed" } }), "passed");
  assert.equal(getPublicChamberResult({ final_result: "failed" }), "failed");
  assert.equal(getPublicChamberResult({ vote_result: "agreed to" }), "agreed to");
});

function governedRow(roll, episodeId) {
  return {
    canonical_action_id: `house:119:2:${roll}`,
    governed_receipt_projection: { episode_id: episodeId },
  };
}

function ledgerRow(roll, voteType, { control = false } = {}) {
  return {
    canonical_action_id: `house:119:2:${roll}`,
    chamber: "house",
    congress: 119,
    rollcall_number: roll,
    position: "nay",
    interpretation_status: "interpreted",
    bill_title: "National Defense Authorization Act for Fiscal Year 2027",
    description: `House roll ${roll}`,
    amendment_purpose: "Limit military speed-camera funding",
    vote_type: voteType,
    governed_receipt_projection: control ? null : { member_action: "Nay" },
    governed_receipt_control: control
      ? { status: "noncounting_control" }
      : undefined,
  };
}
