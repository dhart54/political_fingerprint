import { inferenceSynthesis } from "./editorialIssueReviewSlices.mjs";
import { justiceEditorialIssueFixtureData } from "./justiceEditorialRenderFixture.mjs";
import { justiceCrossMemberValidationData } from "./justiceCrossMemberValidationData.mjs";
import { valerieFousheeJusticePublicSafetyEditorialGold } from "./valerieFousheeJusticePublicSafetyEditorialGold.mjs";

const inferenceByMember = new Map(
  justiceCrossMemberValidationData.inferences.map((item) => [item.member.bioguide_id, item]),
);

export const justiceCrossMemberReviewSlices = Object.freeze(
  justiceCrossMemberValidationData.overlays
    .filter((overlay) => overlay.member.bioguide_id !== "F000477")
    .map((overlay) => buildJusticeMemberReviewCandidate({
      overlay,
      inference: inferenceByMember.get(overlay.member.bioguide_id),
    })),
);

export const justiceCrossMemberRenderProfiles = Object.freeze(
  ["A000370", "A000055", "M001184"].map((memberId) => {
    const overlay = justiceCrossMemberValidationData.overlays.find(
      (item) => item.member.bioguide_id === memberId,
    );
    const candidate = justiceCrossMemberReviewSlices.find(
      (item) => item.identity.memberId === memberId,
    );
    return Object.freeze({
      memberId,
      label: overlay.validation_case,
      candidate,
      legislator: buildLegislator(overlay.member),
      fixtureData: buildMemberFixtureData(overlay),
    });
  }),
);

export function buildJusticeMemberReviewCandidate({ overlay, inference }) {
  const actionsByRoll = new Map(overlay.roll_actions.map((item) => [Number(item.roll), item]));
  const source = {
    ...valerieFousheeJusticePublicSafetyEditorialGold,
    member: {
      name: overlay.member.display_name,
      bioguide_id: overlay.member.bioguide_id,
    },
    slice_counts: {
      substantive_rolls: overlay.coverage.substantive_rolls_expected,
      policy_episodes: overlay.coverage.independent_episodes_expected,
      not_voting_records: overlay.coverage.not_voting_actions,
      context_controls: overlay.roll_actions.filter((item) => !item.counting).length,
    },
    interpretations: valerieFousheeJusticePublicSafetyEditorialGold.interpretations.map(
      (entry) => applyMemberAction(entry, actionsByRoll.get(Number(entry.roll)), overlay.member),
    ),
    controls: valerieFousheeJusticePublicSafetyEditorialGold.controls.map((entry) => ({
      ...entry,
      member_action: actionsByRoll.get(Number(entry.roll))?.action,
    })),
    inference_candidate: inference,
    human_approval_status: "human_approval_pending",
  };
  const aligned = overlay.roll_actions.filter(
    (item) => item.counting && item.aligned_with_party_majority === true,
  ).length;
  const partyName = overlay.member.party === "D" ? "House Democrats" : overlay.member.party === "R" ? "House Republicans" : "the member's party";
  const shortName = memberShortName(overlay.member);
  return Object.freeze({
    source: Object.freeze(source),
    identity: Object.freeze({
      memberId: overlay.member.bioguide_id,
      memberDisplayName: overlay.member.display_name,
      issueId: "JUSTICE_PUBLIC_SAFETY",
      issueDisplayName: "Justice & Public Safety",
      congress: 119,
      reviewedPeriod: "119th Congress",
    }),
    publication: Object.freeze({
      editorialStatus: "human_approval_pending",
      benchmarkStatus: "not_promoted",
      productionEligible: false,
      reviewLabel: "Cross-member validation candidate — not published",
    }),
    synthesis: inferenceSynthesis(source, {
      votingContext: `${shortName} matched the majority of ${partyName} on ${aligned} of ${overlay.coverage.substantive_rolls_expected} substantive roll calls in this sample.`,
      votingContextBoundary: "Party alignment is descriptive metadata only. It did not select the candidate conclusion, and repeated fentanyl stages remain one policy episode.",
    }),
  });
}

function applyMemberAction(entry, actionRow, member) {
  const action = actionRow?.action;
  const originalResult = entry.ten_second?.member_action_and_result || "";
  const resultSuffix = originalResult.includes(". ")
    ? originalResult.slice(originalResult.indexOf(". ") + 2)
    : "";
  return {
    ...entry,
    member_action: action,
    ten_second: {
      ...entry.ten_second,
      headline: actionHeadline(entry.ten_second?.headline, action),
      member_action_and_result: `${memberShortName(member)} ${actionSentence(action)}.${resultSuffix ? ` ${resultSuffix}` : ""}`,
    },
  };
}

function actionHeadline(headline = "", action) {
  const remainder = headline.replace(/^(supported|opposed|did not vote on|voted present on)\s+/i, "");
  const prefix = {
    Yea: "Supported",
    Nay: "Opposed",
    "Not Voting": "Did not vote on",
    Present: "Voted Present on",
  }[action] || "Recorded an action on";
  return `${prefix} ${remainder}`;
}

function actionSentence(action) {
  if (action === "Not Voting") return "did not vote";
  if (action === "Present") return "voted Present";
  return `voted ${action}`;
}

function memberShortName(member) {
  return (member.formal_name || member.display_name)
    .replace(/^(Mr\.|Mrs\.|Ms\.|Miss|Dr\.)\s+/, "");
}

function buildLegislator(member) {
  return Object.freeze({
    id: `leg_${member.bioguide_id.toLowerCase()}`,
    bioguide_id: member.bioguide_id,
    name_display: member.display_name,
    chamber: "house",
    state: member.state,
    district: String(member.district || "").replace(/\D/g, "").padStart(2, "0"),
    party: member.party,
  });
}

function buildMemberFixtureData(overlay) {
  const actionsByRoll = new Map(overlay.roll_actions.map((item) => [Number(item.roll), item]));
  const evidence = justiceEditorialIssueFixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence.map((row) => {
    const action = actionsByRoll.get(Number(row.rollcall_number));
    return {
      ...row,
      position: { Yea: "yea", Nay: "nay", Present: "present", "Not Voting": "not_voting" }[action.action],
      vote_context: {
        ...row.vote_context,
        member_party: overlay.member.party,
        member_voted_with_party_majority: action.aligned_with_party_majority,
      },
    };
  });
  const substantive = overlay.roll_actions.filter((item) => item.counting);
  return Object.freeze({
    positions: {
      ...justiceEditorialIssueFixtureData.positions,
      positions: [{
        domain: "JUSTICE_PUBLIC_SAFETY",
        recorded_votes: overlay.roll_actions.length,
        interpreted_support_count: substantive.filter((item) => item.action === "Yea").length,
        interpreted_oppose_count: substantive.filter((item) => item.action === "Nay").length,
        interpreted_other_count: overlay.roll_actions.length - substantive.filter((item) => ["Yea", "Nay"].includes(item.action)).length,
      }],
    },
    evidenceByDomain: {
      JUSTICE_PUBLIC_SAFETY: { domain: "JUSTICE_PUBLIC_SAFETY", evidence },
    },
  });
}
