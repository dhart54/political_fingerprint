import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  EDITORIAL_EXPERIENCE_MODE,
  selectEditorialIssueExperience,
} from "./editorialIssueExperience.mjs";
import {
  justiceCrossMemberRenderProfiles,
  justiceCrossMemberReviewSlices,
} from "./justiceCrossMemberReviewSlices.mjs";
import { justiceCrossMemberValidationData } from "./justiceCrossMemberValidationData.mjs";


test("every cross-member candidate stays pending and production-ineligible", () => {
  assert.equal(justiceCrossMemberReviewSlices.length, 6);
  for (const candidate of justiceCrossMemberReviewSlices) {
    assert.deepEqual(candidate.publication, {
      editorialStatus: "human_approval_pending",
      benchmarkStatus: "not_promoted",
      productionEligible: false,
      reviewLabel: "Cross-member validation candidate — not published",
    });
    assert.equal(candidate.source.human_approval_status, "human_approval_pending");
  }
});


test("selected profiles reuse one selector and render adapter", () => {
  assert.deepEqual(justiceCrossMemberRenderProfiles.map((item) => item.memberId), ["A000370", "A000055", "M001184"]);
  for (const profile of justiceCrossMemberRenderProfiles) {
    const evidence = profile.fixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence;
    const selected = selectEditorialIssueExperience({
      candidates: [profile.candidate],
      domain: "JUSTICE_PUBLIC_SAFETY",
      evidenceRows: evidence,
      legislator: profile.legislator,
      mode: EDITORIAL_EXPERIENCE_MODE.review,
    });
    assert.ok(selected);
    assert.equal(selected.identity.memberId, profile.memberId);
    assert.deepEqual(selected.indicators.map((item) => item.label), [
      "7 substantive votes",
      "5 policy episodes",
      "6 context-only records",
    ]);
  }
});


test("different overlays preserve shared facts while changing member actions and conclusions", () => {
  const byId = new Map(justiceCrossMemberReviewSlices.map((item) => [item.identity.memberId, item]));
  const adams = byId.get("A000370");
  const aderholt = byId.get("A000055");
  assert.strictEqual(adams.source.interpretations[0].two_minute, aderholt.source.interpretations[0].two_minute);
  assert.equal(adams.source.interpretations[0].member_action, "Yea");
  assert.equal(aderholt.source.interpretations[0].member_action, "Nay");
  assert.match(adams.synthesis.primary, /selective boundary/);
  assert.match(aderholt.synthesis.primary, /proposals expanding enforcement or police authority/);
  assert.doesNotMatch(aderholt.synthesis.primary, /selective boundary/);
});


test("equivalent Foushee and Adams vectors retain structurally consistent evidence", async () => {
  const overlays = new Map(justiceCrossMemberValidationData.overlays.map((item) => [item.member.bioguide_id, item]));
  const inferences = new Map(justiceCrossMemberValidationData.inferences.map((item) => [item.member.bioguide_id, item]));
  assert.deepEqual(
    overlays.get("F000477").episode_trajectories.map((item) => item.action_signature),
    overlays.get("A000370").episode_trajectories.map((item) => item.action_signature),
  );
  assert.equal(inferences.get("F000477").candidate_id, inferences.get("A000370").candidate_id);
  assert.deepEqual(
    inferences.get("F000477").repeated_cross_episode_themes.map((item) => item.theme_id),
    inferences.get("A000370").repeated_cross_episode_themes.map((item) => item.theme_id),
  );
});


test("production registry contains none of the new validation members", async () => {
  const source = await readFile(new URL("./editorialIssueProductionSlices.mjs", import.meta.url), "utf8");
  for (const memberId of ["A000370", "A000055", "M001184", "B000490", "G000586", "M001217"]) {
    assert.equal(source.includes(memberId), false);
  }
});


test("generic selector contains no selected-member, party, or Justice conclusion conditions", async () => {
  const source = (await readFile(new URL("./editorialIssueExperience.mjs", import.meta.url), "utf8")).toLowerCase();
  for (const forbidden of ["a000370", "a000055", "m001184", "foushee", "selective boundary", "party ===", "rollcall_number === 32"]) {
    assert.equal(source.includes(forbidden), false);
  }
});
