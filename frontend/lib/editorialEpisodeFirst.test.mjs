import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { editorialGoldIssueFixtureData, editorialGoldLegislator } from "./editorialGoldRenderFixture.mjs";
import {
  adaptEditorialIssueSlice,
  buildCompleteRecord,
  EDITORIAL_EXPERIENCE_MODE,
  selectEditorialIssueExperience,
} from "./editorialIssueExperience.mjs";
import { reviewEditorialIssueSlices } from "./editorialIssueReviewSlices.mjs";
import {
  buildMemberActionOverlay,
  memberActionStatusCopy,
  MEMBER_ACTION_STATUS,
  sharedEvidenceHasMemberSpecificText,
} from "./editorialSharedEvidence.mjs";
import {
  justiceCrossMemberReviewSlices,
  justiceSharedLegislativeActions,
} from "./justiceCrossMemberReviewSlices.mjs";
import { justiceEditorialIssueFixtureData } from "./justiceEditorialRenderFixture.mjs";

const cohortNames = ["Valerie P. Foushee", "Thomas Massie", "Robert Aderholt", "Alma Adams"];

test("shared Justice actions are member-neutral and overlays change only identity and action copy", () => {
  assert.equal(justiceSharedLegislativeActions.length, 7);
  assert.equal(sharedEvidenceHasMemberSpecificText(justiceSharedLegislativeActions, cohortNames), false);

  for (const shared of justiceSharedLegislativeActions) {
    const sharedFacts = JSON.stringify({
      practical: shared.ten_second.practical_choice,
      changed: shared.thirty_second,
      detail: shared.two_minute,
    });
    const rendered = [
      ["Yea", "Alex Yea"],
      ["Nay", "Blair Nay"],
      ["Present", "Parker Present"],
      ["Not Voting", "Casey Absent"],
      ["not yet serving", "Drew New"],
      ["no longer serving", "Evan Former"],
      ["missing evidence", "Morgan Missing"],
    ].map(([status, name]) => {
      const overlay = buildMemberActionOverlay({
        ...shared,
        member_action: status,
        action_status: status,
        ten_second: { ...shared.ten_second, headline: `${status} on the action`, member_action_and_result: `${name} recorded ${status}.` },
      }, name);
      return { overlay, sharedFacts };
    });
    assert.ok(rendered[0].overlay.actionAndResult.includes("Yea"));
    assert.ok(rendered[1].overlay.actionAndResult.includes("Nay"));
    assert.ok(rendered[2].overlay.actionAndResult.includes("Present"));
    assert.ok(rendered[3].overlay.actionAndResult.includes("Not Voting"));
    assert.equal(rendered[4].overlay.actionAndResult, "This action occurred before the member began serving in Congress.");
    assert.match(rendered[5].overlay.actionAndResult, /after the member's congressional service ended/i);
    assert.match(rendered[6].overlay.actionAndResult, /expected evidence record is unavailable/i);
    assert.ok(rendered.every((item) => item.sharedFacts === sharedFacts));
  }
});

test("cross-member Justice candidates never inherit another cohort member or opposite action", () => {
  for (const candidate of justiceCrossMemberReviewSlices) {
    const ownLastName = candidate.identity.memberDisplayName.replace(/,?\s+(?:Jr\.?|Sr\.?|II|III|IV)$/i, "").split(/\s+/).at(-1);
    for (const entry of candidate.source.interpretations) {
      const overlayText = `${entry.ten_second.headline} ${entry.ten_second.member_action_and_result}`;
      assert.match(overlayText, new RegExp(ownLastName, "i"));
      for (const other of cohortNames.filter((name) => !name.endsWith(ownLastName))) {
        assert.doesNotMatch(JSON.stringify(entry), new RegExp(other.split(/\s+/).at(-1), "i"));
      }
      if (entry.member_action === "Yea") assert.doesNotMatch(overlayText, /voted Nay|Opposed this action/i);
      if (entry.member_action === "Nay") assert.doesNotMatch(overlayText, /voted Yea|Supported this action/i);
    }
    for (const control of candidate.source.controls) {
      for (const other of cohortNames.filter((name) => !name.endsWith(ownLastName))) {
        assert.doesNotMatch(JSON.stringify(control), new RegExp(other.split(/\s+/).at(-1), "i"));
      }
    }
  }
});

test("service-aware statuses stay distinct and never become support or opposition", () => {
  const cases = [
    [MEMBER_ACTION_STATUS.yea, true, "voted Yea"],
    [MEMBER_ACTION_STATUS.nay, true, "voted Nay"],
    [MEMBER_ACTION_STATUS.present, false, "voted Present"],
    [MEMBER_ACTION_STATUS.notVoting, false, "Not Voting"],
    [MEMBER_ACTION_STATUS.notYetServing, false, "before the member began serving"],
    [MEMBER_ACTION_STATUS.noLongerServing, false, "after the member's congressional service ended"],
    [MEMBER_ACTION_STATUS.missingEvidence, false, "expected evidence record is unavailable"],
  ];
  for (const [status, eligible, copy] of cases) {
    const value = memberActionStatusCopy(status, "Example");
    assert.equal(value.analyticallyEligible, eligible);
    assert.match(value.sentence, new RegExp(copy, "i"));
  }
});

test("policy families keep related Congresses in separate episodes", () => {
  const complete = buildCompleteRecord([
    { id: "family-118", policyFamilyId: "synthetic-family", congress: 118 },
    { id: "family-119", policyFamilyId: "synthetic-family", congress: 119 },
  ]);
  assert.equal(complete.length, 1);
  assert.deepEqual(complete[0].congresses.map((item) => item.congress), [118, 119]);
  assert.deepEqual(complete[0].congresses.map((item) => item.episodes.map((episode) => episode.id)), [["family-118"], ["family-119"]]);
});

test("the three reviewed slices expose the requested bounded episode-first hierarchy", () => {
  const economy = selectEditorialIssueExperience({
    candidates: reviewEditorialIssueSlices,
    domain: "ECONOMY_TAXES",
    evidenceRows: editorialGoldIssueFixtureData.evidenceByDomain.ECONOMY_TAXES.evidence,
    legislator: editorialGoldLegislator,
    mode: EDITORIAL_EXPERIENCE_MODE.review,
  });
  const justice = selectEditorialIssueExperience({
    candidates: reviewEditorialIssueSlices,
    domain: "JUSTICE_PUBLIC_SAFETY",
    evidenceRows: justiceEditorialIssueFixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence,
    legislator: editorialGoldLegislator,
    mode: EDITORIAL_EXPERIENCE_MODE.review,
  });
  const massieCandidate = justiceCrossMemberReviewSlices.find((item) => item.identity.memberId === "M001184");
  const massie = adaptEditorialIssueSlice(massieCandidate, justiceEditorialIssueFixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence, EDITORIAL_EXPERIENCE_MODE.review);

  assert.equal(economy.featuredEpisodes.length, 4);
  assert.equal(economy.episodes.length, 4);
  assert.equal(economy.ungroupedRecords.filter((item) => item.inclusionClass === "not_voting").length, 1);
  assert.equal(justice.featuredEpisodes.length, 5);
  assert.equal(justice.episodes[0].actions.length, 3);
  assert.equal(massie.publicPresentation.strengthLabel, "A clear policy divide in the reviewed record");
  assert.equal(massie.episodes[0].memberTrajectory, "Opposed all three reviewed fentanyl actions.");
  assert.match(massie.episodes[0].memberTrajectoryDetail, /Massie voted Nay.*H\.R\. 27.*Senate framework/i);
  for (const experience of [economy, justice, massie]) {
    assert.ok(experience.featuredEpisodes.length <= 5);
    assert.equal(experience.records.length, experience.episodes.flatMap((item) => item.actions).length + experience.ungroupedRecords.length + experience.proceduralRecords.length);
  }
});

test("rich renderer is bounded by disclosure and omits legacy methodology and tooling", async () => {
  const renderer = await readFile(new URL("../components/EditorialIssueExperience.js", import.meta.url), "utf8");
  const route = await readFile(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  assert.match(renderer, /Explore the complete reviewed record/);
  assert.match(renderer, /Featured policy episodes/);
  assert.doesNotMatch(renderer, /How to read this conclusion|Coverage of this conclusion|Evidence group overview|Official contact metadata|rerun this inference/i);
  assert.match(route, /!editorialExperience \? <EvidenceGroupingPreview/);
  assert.match(route, /!editorialExperience \? \(/);
  assert.match(route, /group\.rows\.filter\(\(row\) => row\.domain !== selectedRow\.domain\)/);
  assert.match(route, /state\.status === "ready" && hasOtherIssueRows/);
});

test("member-neutral shared evidence module contains no reviewed member names", async () => {
  const source = await readFile(new URL("./editorialSharedEvidence.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /Foushee|Massie|Aderholt|Adams/);
});
