import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  blindEditorialPipelineReviewProfile,
  blindEditorialPipelineValidationFixture,
} from "./blindEditorialPipelineReviewSlice.mjs";
import { blindEditorialPipelineValidationData } from "./blindEditorialPipelineValidationData.mjs";
import { adaptEditorialIssueSlice, EDITORIAL_EXPERIENCE_MODE } from "./editorialIssueExperience.mjs";
import { editorialReferenceFixtures } from "./editorialStandardizationFixtures.mjs";
import { justiceSharedLegislativeActions } from "./justiceCrossMemberReviewSlices.mjs";

const profile = blindEditorialPipelineReviewProfile;
const candidate = profile.candidate;
const evidenceRows = profile.fixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence;
const experience = adaptEditorialIssueSlice(candidate, evidenceRows, EDITORIAL_EXPERIENCE_MODE.review);

test("blind candidate is locked, pending, unpromoted, and production-ineligible", () => {
  assert.equal(profile.memberId, "G000586");
  assert.equal(blindEditorialPipelineValidationData.selectedMember.member_id, profile.memberId);
  assert.deepEqual(candidate.publication, {
    editorialStatus: "human_approval_pending",
    benchmarkStatus: "not_promoted",
    productionEligible: false,
    reviewLabel: "Cross-member validation candidate — not published",
  });
  assert.equal(candidate.source.human_approval_status, "human_approval_pending");
  assert.equal(blindEditorialPipelineValidationFixture.designation, "reference_render_fixture");
});

test("candidate reuses identical shared facts, arguments, and sources with no member leakage", () => {
  assert.strictEqual(candidate.source.shared_legislative_actions, justiceSharedLegislativeActions);
  for (const interpretation of candidate.source.interpretations) {
    const shared = justiceSharedLegislativeActions.find((item) => item.roll === interpretation.roll);
    assert.strictEqual(interpretation.two_minute, shared.two_minute);
    assert.deepEqual(interpretation.thirty_second, shared.thirty_second);
    assert.equal(
      interpretation.member_action,
      blindEditorialPipelineValidationData.overlay.roll_actions.find((item) => item.roll === interpretation.roll).action,
    );
  }
  const sharedText = JSON.stringify(justiceSharedLegislativeActions);
  for (const name of ["García", "Chuy", "Foushee", "Massie"]) {
    assert.equal(sharedText.includes(name), false);
  }
});

test("public model preserves coverage, episode grouping, receipts, and secondary context", () => {
  assert.equal(experience.publicPresentation.coverage.expectedVotes, 7);
  assert.equal(experience.publicPresentation.coverage.expectedEpisodes, 5);
  assert.equal(experience.episodes.length, 5);
  assert.equal(experience.featuredEpisodes.length, 5);
  assert.equal(experience.episodes.find((item) => item.id === "halt-fentanyl-legislative-path").actions.length, 3);
  assert.equal(experience.episodes.flatMap((item) => item.actions).length, 7);
  assert.equal(
    experience.completeRecord
      .flatMap((family) => family.congresses)
      .flatMap((congress) => congress.episodes)
      .flatMap((episode) => episode.actions).length,
    7,
  );
  assert.equal(experience.proceduralRecords.length, 6);
  assert.equal(experience.featuredEpisodes.every((episode) => !episode.dateSpan.includes("2025-")), true);
  const episodeIds = new Set(experience.episodes.map((item) => item.id));
  for (const section of Object.values(candidate.synthesis.analyticalSections)) {
    for (const item of section) {
      if (item.episodeId) assert.equal(episodeIds.has(item.episodeId), true);
    }
  }
  for (const action of experience.episodes.flatMap((item) => item.actions)) {
    assert.ok(action.impactAndOutcome.affected);
    assert.ok(action.whatChanged.changeAtStake);
    assert.ok(action.impactAndOutcome.outcome);
    assert.ok(action.sources.length >= 2);
  }
});

test("the correction uses the uniform-direction archetype without changing reference fixture membership", () => {
  assert.equal(blindEditorialPipelineValidationData.inference.candidate_id, "uniform_direction_without_common_policy_rationale");
  assert.equal(candidate.synthesis.evidenceBreadth, "Uniform opposition across the reviewed proposals");
  assert.match(candidate.synthesis.primary, /does not establish one overarching public-safety philosophy/);
  assert.deepEqual(
    candidate.synthesis.analyticalSections.repeatedPatterns.map((item) => item.text),
    ["Opposed both reviewed D.C. policing policy proposals."],
  );
  assert.equal(editorialReferenceFixtures.length, 3);
  assert.deepEqual(
    editorialReferenceFixtures.map((item) => item.id),
    [
      "foushee-economy-reference-v1",
      "foushee-justice-reference-v1",
      "massie-justice-reference-v1",
    ],
  );
});

test("production registry and generic runtime contain no blind-candidate branch", async () => {
  const production = await readFile(new URL("./editorialIssueProductionSlices.mjs", import.meta.url), "utf8");
  assert.equal(production.includes("G000586"), false);
  const sources = await Promise.all([
    readFile(new URL("./editorialIssueExperience.mjs", import.meta.url), "utf8"),
    readFile(new URL("./blindEditorialPipelineReviewSlice.mjs", import.meta.url), "utf8"),
  ]);
  const runtime = sources.join("\n").toLowerCase();
  for (const forbidden of ["g000586", "garcía", "party ===", "nay/nay/nay/nay/nay/nay/nay"]) {
    assert.equal(runtime.includes(forbidden), false);
  }
});
