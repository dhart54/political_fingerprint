import assert from "node:assert/strict";
import test from "node:test";

import {
  commissioningDomainRenderProfiles,
  commissioningDomainReviewSlices,
} from "./commissioningDomainReviewSlices.mjs";
import { productionEditorialIssueSlices } from "./editorialIssueProductionSlices.mjs";
import {
  EDITORIAL_EXPERIENCE_MODE,
  selectEditorialIssueExperience,
} from "./editorialIssueExperience.mjs";

test("commissioning slices remain review-only and render through the generic selector", () => {
  assert.equal(commissioningDomainReviewSlices.length, 7);
  assert.equal(commissioningDomainRenderProfiles.length, 4);

  for (const profile of commissioningDomainRenderProfiles) {
    const evidenceRows = profile.fixtureData.evidenceByDomain.ENVIRONMENT_ENERGY.evidence;
    const selected = selectEditorialIssueExperience({
      candidates: [profile.candidate],
      domain: "ENVIRONMENT_ENERGY",
      evidenceRows,
      legislator: profile.legislator,
      mode: EDITORIAL_EXPERIENCE_MODE.review,
    });
    assert.ok(selected);
    assert.equal(selected.episodes.length, 6);
    assert.equal(selected.records.length, 7);
    assert.equal(selected.reviewContext.isReview, true);
    assert.ok(selected.records.every((record) => record.sources.length >= 2));

    assert.equal(selectEditorialIssueExperience({
      candidates: [profile.candidate],
      domain: "ENVIRONMENT_ENERGY",
      evidenceRows,
      legislator: profile.legislator,
    }), null);
  }
});

test("corrected review fixtures exclude roll 5 and retain shared dependencies separately", () => {
  for (const candidate of commissioningDomainReviewSlices) {
    assert.equal(candidate.source.interpretations.some((item) => item.roll === 5), false);
    assert.equal(candidate.source.slice_counts.substantive_rolls, 7);
    assert.ok(
      candidate.source.inference_candidate.shared_review_dependencies
        .publication_blocked_until_resolved,
    );
    assert.notEqual(
      candidate.source.inference_candidate.shared_review_dependencies.dependency_ids.length,
      0,
    );
    assert.equal(
      candidate.source.inference_candidate.shared_review_dependencies.dependency_ids.length,
      7,
    );
  }
});

test("production registry remains empty", () => {
  assert.deepEqual(productionEditorialIssueSlices, []);
});

test("shared action facts are identical across member overlays", () => {
  const first = commissioningDomainReviewSlices[0].source.interpretations;
  for (const candidate of commissioningDomainReviewSlices.slice(1)) {
    candidate.source.interpretations.forEach((record, index) => {
      assert.equal(record.ten_second.practical_choice, first[index].ten_second.practical_choice);
      assert.deepEqual(record.thirty_second, first[index].thirty_second);
      assert.deepEqual(record.two_minute.sources, first[index].two_minute.sources);
    });
  }
});

test("coverage edge preserves Not Voting as non-substantive", () => {
  const profile = commissioningDomainRenderProfiles.find((item) => item.label === "coverage_edge");
  assert.ok(profile);
  const notVoting = profile.candidate.source.interpretations.filter(
    (item) => item.member_action === "Not Voting",
  );
  assert.ok(notVoting.length >= 1);
  assert.ok(notVoting.every((item) => /neither support nor opposition/i.test(item.two_minute.caveats.at(-1))));
});
