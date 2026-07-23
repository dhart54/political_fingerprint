import { justiceEpisodePresentation } from "./editorialEpisodeMetadata.mjs";
import { buildSharedLegislativeAction, neutralizeSharedSources } from "./editorialSharedEvidence.mjs";
import { justiceEditorialIssueFixtureData } from "./justiceEditorialRenderFixture.mjs";
import { justiceCrossMemberValidationData } from "./justiceCrossMemberValidationData.mjs";
import { valerieFousheeJusticePublicSafetyEditorialGold } from "./valerieFousheeJusticePublicSafetyEditorialGold.mjs";

const inferenceByMember = new Map(
  justiceCrossMemberValidationData.inferences.map((item) => [item.member.bioguide_id, item]),
);
const overlayByMember = new Map(
  justiceCrossMemberValidationData.overlays.map((item) => [item.member.bioguide_id, item]),
);
const episodeById = new Map(justiceEpisodePresentation.episodes.map((item) => [item.id, item]));
const neutralSharedByRoll = new Map(
  valerieFousheeJusticePublicSafetyEditorialGold.interpretations.map((entry) => [
    Number(entry.roll),
    neutralSharedEntry(entry),
  ]),
);

export const justiceSharedLegislativeActions = Object.freeze(
  [...neutralSharedByRoll.values()].map((entry) => Object.freeze(entry)),
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
    const overlay = overlayByMember.get(memberId);
    const candidate = justiceCrossMemberReviewSlices.find((item) => item.identity.memberId === memberId);
    return Object.freeze({
      memberId,
      label: overlay.validation_case,
      candidate,
      legislator: buildLegislator(overlay.member),
      fixtureData: buildMemberFixtureData(overlay),
    });
  }),
);

export function justiceReviewCandidateForMember(memberId, synthesis) {
  const overlay = overlayByMember.get(memberId);
  if (!overlay) return null;
  return buildJusticeMemberReviewCandidate({ overlay, inference: inferenceByMember.get(memberId), synthesis });
}

export function buildJusticeMemberReviewCandidate({ overlay, inference, synthesis = null }) {
  const actionsByRoll = new Map(overlay.roll_actions.map((item) => [Number(item.roll), item]));
  const source = {
    ...valerieFousheeJusticePublicSafetyEditorialGold,
    member: { name: overlay.member.display_name, bioguide_id: overlay.member.bioguide_id },
    shared_legislative_actions: justiceSharedLegislativeActions,
    slice_counts: {
      substantive_rolls: overlay.coverage.substantive_rolls_expected,
      policy_episodes: overlay.coverage.independent_episodes_expected,
      not_voting_records: overlay.coverage.not_voting_actions,
      context_controls: overlay.roll_actions.filter((item) => !item.counting).length,
    },
    interpretations: justiceSharedLegislativeActions.map(
      (entry) => applyMemberAction(entry, actionsByRoll.get(Number(entry.roll)), overlay.member),
    ),
    controls: valerieFousheeJusticePublicSafetyEditorialGold.controls.map((entry) => ({
      ...entry,
      member_action: actionsByRoll.get(Number(entry.roll))?.action,
      context_summary: neutralControlSummary(entry.context_summary),
      sources: neutralizeSharedSources(entry.sources),
    })),
    inference_candidate: inference,
    human_approval_status: "human_approval_pending",
  };
  const aligned = overlay.roll_actions.filter((item) => item.counting && item.aligned_with_party_majority === true).length;
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
    episodePresentation: justiceEpisodePresentation,
    memberEpisodeTrajectories: Object.freeze(overlay.episode_trajectories),
    publication: Object.freeze({
      editorialStatus: "human_approval_pending",
      benchmarkStatus: "not_promoted",
      productionEligible: false,
      reviewLabel: "Cross-member validation candidate — not published",
    }),
    synthesis: Object.freeze(synthesis || reviewedSynthesisOverride(overlay, aligned, partyName) || inferenceSynthesis(source, {
      votingContext: `${shortName} voted with the majority of ${partyName} on ${aligned} of the ${overlay.coverage.substantive_rolls_expected} substantive actions reviewed.`,
    })),
  });
}

function reviewedSynthesisOverride(overlay, aligned, partyName) {
  if (overlay.member.bioguide_id !== "M001184") return null;
  return {
    primary: "Massie's reviewed record splits clearly by policy mechanism. He opposed all three actions in the fentanyl scheduling episode, while supporting officer-safety reporting and proposals concerning retired service firearms, broader D.C. pursuit authority, and repeal of most of D.C.'s 2022 policing reform law.",
    evidenceBreadth: "A clear policy divide in the reviewed record",
    readerFacingLabel: "A clear policy divide in the reviewed record",
    analyticalSections: {
      policyTrajectories: [{ episodeId: "halt-fentanyl-legislative-path", text: "Opposed all three reviewed actions in the fentanyl scheduling episode." }],
      repeatedPatterns: [{ text: "Supported the three reviewed proposals involving police tools, operational authority, or rollback of policing restrictions." }],
      otherNotableChoices: [{ episodeId: "officer-safety-data-reporting", text: "Supported officer-safety and wellness reporting." }],
    },
    votingContext: `Massie voted with the majority of ${partyName} on ${aligned} of the ${overlay.coverage.substantive_rolls_expected} substantive actions reviewed.`,
  };
}

function inferenceSynthesis(source, context = {}) {
  const inference = source.inference_candidate || {};
  return {
    primary: inference.primary_conclusion,
    patterns: [
      ...(inference.within_episode_trajectories || []).map((item) => item.member_trajectory),
      ...(inference.repeated_cross_episode_themes || []).map((item) => item.finding),
    ],
    analyticalSections: {
      policyTrajectories: (inference.within_episode_trajectories || []).map((item) => ({ episodeId: item.episode_id, text: item.member_trajectory })),
      repeatedPatterns: (inference.repeated_cross_episode_themes || []).slice(0, 1).map((item) => ({ text: item.finding })),
      otherNotableChoices: (inference.notable_one_off_choices || []).map((item) => ({ episodeId: item.episode_id, text: item.practical_policy_direction })),
      meaningfulExceptions: (inference.contrary_or_limiting_evidence || []).map((item) => ({ episodeId: item.episode_id, text: item.text })),
    },
    votingContext: context.votingContext,
    evidenceBreadth: inference.evidence_strength_label,
  };
}

function neutralSharedEntry(entry) {
  const episode = episodeById.get(entry.episode_id);
  const shared = buildSharedLegislativeAction(entry, {}, {
    episodeId: entry.episode_id,
    policyFamilyId: episode?.policyFamilyId,
  });
  return {
    roll: entry.roll,
    measure_id: entry.measure_id,
    stage: entry.stage,
    episode_id: entry.episode_id,
    human_approval_status: entry.human_approval_status,
    ten_second: Object.freeze({ practical_choice: shared.practicalChoice }),
    thirty_second: Object.freeze({
      prior_baseline: shared.whatChanged.before,
      mechanism: shared.whatChanged.changeAtStake,
      affected: shared.impactAndOutcome.affected,
      scale_or_timing: shared.impactAndOutcome.scaleAndTiming,
      what_happened_next: shared.impactAndOutcome.outcome,
    }),
    two_minute: Object.freeze({
      detail: shared.additionalDetail.detail,
      supporter_argument: shared.arguments.supporters,
      opponent_argument: shared.arguments.opponents,
      argument_boundary: shared.argumentBoundary,
      one_sided_argument_note: shared.oneSidedArgumentNote,
      later_history: shared.additionalDetail.laterHistory,
      caveats: shared.importantContext,
      sources: shared.sources,
    }),
  };
}

function applyMemberAction(shared, actionRow, member) {
  const action = actionRow?.action || "missing evidence";
  return {
    ...shared,
    member_action: action,
    action_status: action,
    ten_second: {
      ...shared.ten_second,
      headline: actionHeadline(shared.ten_second?.practical_choice, action),
      member_action_and_result: `${memberShortName(member)} ${actionSentence(action)}.${outcomeSentence(shared.thirty_second?.what_happened_next)}`,
    },
  };
}

function actionHeadline(practicalChoice = "this legislative action", action) {
  const object = practicalChoice.replace(/^Whether\s+(?:to\s+)?/i, "").replace(/\.$/, "");
  const prefix = { Yea: "Supported", Nay: "Opposed", "Not Voting": "Was not recorded on", Present: "Voted Present on" }[action] || "Evidence unavailable for";
  return `${prefix} this action: ${object}`;
}

function outcomeSentence(value = "") {
  const first = String(value).split(/(?<=\.)\s+/)[0]?.trim();
  return first ? ` ${first}` : "";
}

function actionSentence(action) {
  if (action === "Not Voting") return "was recorded as Not Voting";
  if (action === "Present") return "voted Present";
  if (action === "Yea" || action === "Nay") return `voted ${action}`;
  return "has no resolved evidence record for this action";
}

function neutralControlSummary(value = "") {
  return value
    .replace(/\bFoushee\s+voted\s+(?:Yes|No|Yea|Nay)\b[^.]*\.?/gi, "This floor-process action was reviewed.")
    .replace(/\bher\b/gi, "the member's");
}

function memberShortName(member) {
  return (member.formal_name || member.display_name)
    .replace(/^(Mr\.|Mrs\.|Ms\.|Miss|Dr\.)\s+/, "")
    .replace(/,?\s+(?:Jr\.?|Sr\.?|II|III|IV)$/i, "");
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
      vote_context: { ...row.vote_context, member_party: overlay.member.party, member_voted_with_party_majority: action.aligned_with_party_majority },
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
        interpreted_other_count: substantive.filter((item) => !["Yea", "Nay"].includes(item.action)).length,
      }],
    },
    evidenceByDomain: { JUSTICE_PUBLIC_SAFETY: { domain: "JUSTICE_PUBLIC_SAFETY", evidence } },
  });
}
