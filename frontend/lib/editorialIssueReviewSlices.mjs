import { economyEpisodeByRoll, economyEpisodePresentation } from "./editorialEpisodeMetadata.mjs";
import { commissioningDomainReviewSlices } from "./commissioningDomainReviewSlices.mjs";
import { justiceReviewCandidateForMember } from "./justiceCrossMemberReviewSlices.mjs";
import { valerieFousheeEconomyEditorialGold } from "./valerieFousheeEconomyEditorialGold.mjs";

const economySource = Object.freeze({
  ...valerieFousheeEconomyEditorialGold,
  inference_candidate: {
    inference_level: "bounded_repeated_pattern",
    coverage: {
      substantive_rolls_expected: 6,
      substantive_rolls_observed: 6,
      substantive_yes_no_actions: 6,
      present_actions: 0,
      not_voting_actions: 1,
      missing_actions: 0,
      independent_episodes_expected: 4,
      independent_episodes_complete: 4,
      independent_episodes_partial: 0,
      independent_episodes_missing: 0,
    },
  },
});

const economyCandidate = Object.freeze({
  source: economySource,
  identity: Object.freeze({
    memberId: "F000477",
    memberDisplayName: "Valerie P. Foushee",
    issueId: "ECONOMY_TAXES",
    issueDisplayName: "Economy & Taxes",
    congress: 119,
    reviewedPeriod: "119th Congress",
  }),
  episodeByRoll: economyEpisodeByRoll,
  episodePresentation: economyEpisodePresentation,
  standardizationFixture: Object.freeze({
    designation: "human_reviewed_presentation_fixture",
    fixtureId: "foushee-economy-reference-v1",
  }),
  memberEpisodeTrajectories: Object.freeze([
    trajectory("government_funding_hr5371", "Opposed both reviewed stages of the 2025 government-funding episode.", "Foushee voted Nay on the September House proposal and Nay on the materially revised Senate package the House accepted in November."),
    trajectory("budget_framework_hconres14", "Opposed both reviewed stages of the FY2025–FY2034 budget-framework episode.", "Foushee voted Nay on the initial House budget framework and Nay on the later Senate-revised framework."),
    trajectory("milcon_va_hr3944", "Opposed the reviewed House military-construction and veterans funding proposal."),
    trajectory("sba_loan_eligibility_hr2966", "Opposed the reviewed immigration-status restrictions on SBA-backed loan eligibility."),
  ]),
  publication: pendingPublication("Editorial review preview — not published"),
  synthesis: Object.freeze({
    primary: "Across the reviewed record, Foushee consistently opposed the House proposals examined here, including both stages of the budget-framework and government-funding episodes. Her other reviewed choices concerned veterans funding and small-business eligibility; together, these varied mechanisms do not establish one overarching economic philosophy.",
    evidenceBreadth: "A consistent pattern in the reviewed record",
    readerFacingLabel: "Consistent opposition without an overarching economic philosophy",
    analyticalSections: Object.freeze({
      repeatedPatterns: Object.freeze([
        finding("government_funding_hr5371", "Opposed both stages of the 2025 government-funding episode."),
        finding("budget_framework_hconres14", "Opposed both stages of the FY2025–FY2034 budget-framework episode."),
      ]),
      otherNotableChoices: Object.freeze([
        finding("milcon_va_hr3944", "Opposed the reviewed military-construction and veterans funding proposal."),
        finding("sba_loan_eligibility_hr2966", "Opposed the reviewed immigration-status restrictions on SBA-backed loan eligibility."),
      ]),
    }),
    votingContext: "Foushee voted with the majority of House Democrats on all 6 substantive actions reviewed.",
  }),
});

const fousheeJusticeCandidateSource = justiceReviewCandidateForMember("F000477", Object.freeze({
  primary: "Across the reviewed record, Foushee supported public-safety measures tied to reporting, research, or explicit safeguards, while opposing proposals that expanded police tools or authority or rolled back D.C. policing protections. Her fentanyl votes show that this was not blanket opposition to enforcement: she supported a certification condition, opposed the earlier House bill, and later supported a related permanent framework with research provisions.",
  evidenceBreadth: "A selective pattern in the reviewed record",
  readerFacingLabel: "A selective pattern in the reviewed record",
  analyticalSections: Object.freeze({
    policyTrajectories: Object.freeze([
      finding("halt-fentanyl-legislative-path", "Supported a certification condition, opposed the earlier House bill after that condition failed, and later supported a related permanent framework with research provisions."),
    ]),
    repeatedPatterns: Object.freeze([
      finding(null, "Supported information gathering, research, or implementation safeguards across the officer-reporting and fentanyl episodes."),
      finding(null, "Opposed the reviewed service-firearm, D.C. pursuit, and D.C. policing-repeal proposals."),
    ]),
  }),
  votingContext: "Foushee voted with the majority of House Democrats on all 7 substantive actions reviewed.",
}));

const fousheeJusticeCandidate = Object.freeze({
  ...fousheeJusticeCandidateSource,
  standardizationFixture: Object.freeze({
    designation: "human_reviewed_presentation_fixture",
    fixtureId: "foushee-justice-reference-v1",
  }),
});

export const reviewEditorialIssueSlices = Object.freeze([
  economyCandidate,
  fousheeJusticeCandidate,
  ...commissioningDomainReviewSlices,
]);

export function inferenceSynthesis(source, context = {}) {
  const inference = source.inference_candidate || {};
  return Object.freeze({
    primary: inference.primary_conclusion,
    patterns: Object.freeze([
      ...(inference.within_episode_trajectories || []).map((item) => item.member_trajectory),
      ...(inference.repeated_cross_episode_themes || []).map((item) => item.finding),
    ]),
    votingContext: context.votingContext,
    evidenceBreadth: inference.evidence_strength_label,
  });
}

function pendingPublication(reviewLabel) {
  return Object.freeze({
    editorialStatus: "human_approval_pending",
    benchmarkStatus: "not_promoted",
    productionEligible: false,
    reviewLabel,
  });
}

function finding(episodeId, text) {
  return Object.freeze({ episodeId, text });
}

function trajectory(episode_id, member_trajectory, member_trajectory_detail = "") {
  return Object.freeze({ episode_id, member_trajectory, member_trajectory_detail, coverage_status: "complete" });
}
