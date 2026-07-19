import assert from "node:assert/strict";
import test from "node:test";

import { editorialGoldIssueFixtureData, editorialGoldLegislator } from "./editorialGoldRenderFixture.mjs";
import { getApprovedEditorialSlice, isEditorialSliceRow } from "./editorialGold.mjs";
import {
  buildImportantContext,
  editorialInferenceLadder,
  fousheeEconomyInferenceLevel,
  fousheeEconomyIssueRead,
  groupOfficialSources,
} from "./editorialGoldPresentation.mjs";
import { valerieFousheeEconomyEditorialGold } from "./valerieFousheeEconomyEditorialGold.mjs";


test("approved Foushee economy content is narrowly matched to member, domain, Congress, and roll", () => {
  const evidenceRows = editorialGoldIssueFixtureData.evidenceByDomain.ECONOMY_TAXES.evidence;
  const slice = getApprovedEditorialSlice({
    domain: "ECONOMY_TAXES",
    evidenceRows,
    legislator: editorialGoldLegislator,
  });

  assert.ok(slice);
  assert.equal(slice.interpretations.length, 7);
  assert.equal(slice.controls.length, 2);
  assert.deepEqual(slice.interpretations.map((entry) => entry.roll), [310, 285, 281, 182, 156, 100, 50]);
  assert.deepEqual(slice.controls.map((entry) => entry.roll), [263, 180]);
  assert.equal(slice.interpretations.find((entry) => entry.roll === 310).member_action, "Not Voting");
  assert.ok(slice.interpretations.every((entry) => entry.human_approval_status === "human_approval_pending"));
  assert.ok(slice.controls.every((entry) => entry.human_approval_status === "human_approval_pending"));
  assert.equal(slice.slice_counts.substantive_rolls, 6);
  assert.equal(slice.slice_counts.policy_episodes, 4);

  const roll50 = slice.interpretations.find((entry) => entry.roll === 50);
  const roll100 = slice.interpretations.find((entry) => entry.roll === 100);
  assert.notEqual(roll50.ten_second.headline, roll100.ten_second.headline);
  assert.match(roll50.ten_second.member_action_and_result, /did not itself change taxes/);
  assert.match(roll100.ten_second.member_action_and_result, /did not itself change taxes/);
  assert.ok(roll100.two_minute.sources.some((source) => source.locator.includes("concurrence in the Senate amendment")));
  assert.ok(!roll50.two_minute.sources.some((source) => source.locator.includes("concurrence in the Senate amendment")));

  assert.equal(
    getApprovedEditorialSlice({ domain: "ECONOMY_TAXES", evidenceRows, legislator: { ...editorialGoldLegislator, bioguide_id: "F000000" } }),
    null,
  );
  assert.equal(
    getApprovedEditorialSlice({ domain: "HEALTH_SOCIAL", evidenceRows, legislator: editorialGoldLegislator }),
    null,
  );
  assert.equal(isEditorialSliceRow(evidenceRows.find((row) => row.rollcall_number === 999), slice), false);
});


test("public staged bundle excludes internal review fields and claim IDs", () => {
  const serialized = JSON.stringify(valerieFousheeEconomyEditorialGold);
  for (const forbidden of [
    "claim_id",
    "current_stored_copy",
    "agent_confidence",
    "human_approved",
    "gold_benchmark",
    "review_question",
  ]) {
    assert.equal(serialized.includes(forbidden), false, forbidden);
  }
  assert.equal(valerieFousheeEconomyEditorialGold.source_commit, "db7eb324136866c360a68a2f996e91907eb3d76d");
  assert.equal(valerieFousheeEconomyEditorialGold.human_approval_status, "human_approval_pending");
});


test("episode-aware synthesis stays at the bounded-pattern level without prohibiting earned philosophy reads", () => {
  assert.match(fousheeEconomyIssueRead.primarySummary, /six substantive votes represent four policy episodes/i);
  assert.match(fousheeEconomyIssueRead.primarySummary, /several specific voting patterns/i);
  assert.match(fousheeEconomyIssueRead.primarySummary, /not yet broad enough to establish one overarching/i);
  assert.equal(fousheeEconomyIssueRead.patterns.length, 4);
  assert.equal(fousheeEconomyIssueRead.patterns.filter((pattern) => /both reviewed stages/i.test(pattern)).length, 2);
  assert.equal(fousheeEconomyInferenceLevel, "boundedVotingPattern");
  assert.equal(editorialInferenceLadder.recordedAction.level, 1);
  assert.equal(editorialInferenceLadder.boundedVotingPattern.level, 2);
  assert.equal(editorialInferenceLadder.broaderPoliticalPhilosophy.level, 3);
  assert.equal(editorialInferenceLadder.broaderPoliticalPhilosophy.allowedWhenSupported, true);
  assert.doesNotMatch(
    JSON.stringify({ fousheeEconomyIssueRead, editorialInferenceLadder }),
    /voting records can never|cannot support (a )?philosophy/i,
  );
  assert.match(fousheeEconomyIssueRead.votingContextBoundary, /does not explain why/i);
  assert.match(fousheeEconomyIssueRead.votingContextBoundary, /repeated stages are not separate policy positions/i);
});


test("public presentation deduplicates sources and consolidates motive and advocacy boundaries", () => {
  const grouped = groupOfficialSources([
    { group: "Vote and legislative status", name: "House Clerk roll call", locator: "Roll 100", url: "https://example.test/roll100/" },
    { group: "Vote and legislative status", name: "House Clerk roll call", locator: "Roll 100 duplicate", url: "https://example.test/roll100" },
    { group: "Competing arguments", name: "Congressional Record", locator: "Debate", url: "https://example.test/debate" },
  ]);
  assert.equal(grouped.reduce((total, group) => total + group.items.length, 0), 2);
  assert.deepEqual(grouped.map((group) => group.name), ["Vote and legislative status", "Competing arguments"]);

  const roll285 = valerieFousheeEconomyEditorialGold.interpretations.find((entry) => entry.roll === 285);
  const context = buildImportantContext(roll285);
  assert.equal(context.filter((item) => /why foushee|motive/i.test(item)).length, 2);
  assert.ok(context.some((item) => /attributed advocacy/i.test(item)));
  assert.ok(context.some((item) => /materially different from roll 281/i.test(item)));
});
