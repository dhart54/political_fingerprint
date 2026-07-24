import { editorialGoldIssueFixtureData } from "./editorialGoldRenderFixture.mjs";
import { reviewEditorialIssueSlices } from "./editorialIssueReviewSlices.mjs";
import { justiceCrossMemberReviewSlices } from "./justiceCrossMemberReviewSlices.mjs";
import { justiceEditorialIssueFixtureData } from "./justiceEditorialRenderFixture.mjs";

const massieJustice = justiceCrossMemberReviewSlices.find((candidate) => candidate.identity.memberId === "M001184");

export const editorialReferenceFixtures = Object.freeze([
  reference("foushee-economy-reference-v1", reviewEditorialIssueSlices[0], editorialGoldIssueFixtureData.evidenceByDomain.ECONOMY_TAXES.evidence),
  reference("foushee-justice-reference-v1", reviewEditorialIssueSlices[1], justiceEditorialIssueFixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence),
  reference("massie-justice-reference-v1", massieJustice, justiceEditorialIssueFixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence),
]);

const largeEpisodes = Object.freeze(Array.from({ length: 12 }, (_, index) => {
  const episodeNumber = index + 1;
  const firstRoll = 700 + index * 2;
  return Object.freeze({
    id: `synthetic-episode-${episodeNumber}`,
    policyFamilyId: index === 0 || index === 6 ? "synthetic-cross-congress-family" : `synthetic-family-${episodeNumber}`,
    congress: index < 6 ? 118 : 119,
    title: `Example policy episode ${episodeNumber}`,
    rolls: Object.freeze([firstRoll, firstRoll + 1]),
    sharedQuestion: `Whether to adopt the two reviewed stages in example policy episode ${episodeNumber}.`,
    relationship: "The second action was a related but materially distinct legislative stage within the same Congress.",
    materialDifferences: "The later action changed the legislative stage while preserving the bounded policy object.",
    conclusionRelevance: index < 2 ? "Supports the repeated pattern" : "",
    selectionRationale: index < 5 ? "Selected upstream to keep the default presentation bounded." : "Retained in the complete record.",
  });
}));

const largeInterpretations = Object.freeze(largeEpisodes.flatMap((episode) => episode.rolls.map((roll, actionIndex) => syntheticInterpretation(episode, roll, actionIndex))));
const notVotingInterpretation = Object.freeze(syntheticInterpretation(null, 799, 0, "Not Voting"));
const largeControls = Object.freeze([800, 801, 802].map((roll) => Object.freeze({
  roll,
  congress: 119,
  measure_id: `synthetic-control-${roll}`,
  stage: "Procedural control",
  member_action: "Yea",
  human_approval_status: "human_approval_pending",
  context_summary: "A floor-process action retained as non-counting context.",
  why_not_counted: "Procedural controls do not establish support or opposition to the underlying policy.",
  sources: Object.freeze([source(`https://clerk.house.gov/Votes/2025${roll}`, `House Clerk roll call ${roll}`)]),
})));

export const syntheticLargeRecordCandidate = Object.freeze({
  source: Object.freeze({
    schema_version: "synthetic_large_editorial_record_v1",
    human_approval_status: "human_approval_pending",
    slice_counts: Object.freeze({ substantive_rolls: 24, policy_episodes: 12, not_voting_records: 1, context_controls: 3 }),
    interpretations: Object.freeze([...largeInterpretations, notVotingInterpretation]),
    controls: largeControls,
    inference_candidate: Object.freeze({ coverage: Object.freeze({
      substantive_rolls_expected: 24,
      substantive_rolls_observed: 24,
      substantive_yes_no_actions: 24,
      not_voting_actions: 1,
      present_actions: 0,
      missing_actions: 0,
      independent_episodes_expected: 12,
      independent_episodes_complete: 12,
      independent_episodes_partial: 0,
      independent_episodes_missing: 0,
    }) }),
  }),
  identity: Object.freeze({
    memberId: "SYNTHETIC-LARGE",
    memberDisplayName: "Large Record Example",
    issueId: "PUBLIC_ADMINISTRATION_EXAMPLE",
    issueDisplayName: "Public Administration",
    congress: 119,
    reviewedPeriod: "118th and 119th Congresses",
  }),
  standardizationFixture: Object.freeze({ designation: "standardization_regression_fixture", fixtureId: "synthetic-large-record-v1" }),
  episodePresentation: Object.freeze({ featuredEpisodeIds: Object.freeze(largeEpisodes.slice(0, 5).map((episode) => episode.id)), episodes: largeEpisodes }),
  memberEpisodeTrajectories: Object.freeze(largeEpisodes.map((episode) => Object.freeze({
    episode_id: episode.id,
    coverage_status: "complete",
    member_trajectory: "Supported both related reviewed stages.",
    member_trajectory_detail: "The member voted Yea on the first stage and Yea on the materially distinct later stage.",
  }))),
  publication: Object.freeze({ editorialStatus: "human_approval_pending", benchmarkStatus: "not_promoted", productionEligible: false, reviewLabel: "Large-record scalability review" }),
  synthesis: Object.freeze({
    primary: "Across this example record, the member supported the reviewed stages in multiple Congress-bounded policy episodes.",
    evidenceBreadth: "Large reviewed record",
    readerFacingLabel: "Large reviewed record",
    analyticalSections: Object.freeze({ repeatedPatterns: Object.freeze([{ episodeId: "synthetic-episode-1", text: "Supported both related stages in the first example episode." }]) }),
  }),
});

export const syntheticLargeRecordRows = Object.freeze([
  ...largeEpisodes.flatMap((episode) => episode.rolls.map((roll) => syntheticRow(episode, roll))),
  syntheticRow({ congress: 119 }, 799, "not_voting"),
  ...largeControls.map((entry) => syntheticRow({ congress: 119 }, entry.roll)),
]);

export const syntheticLargeRecordLegislator = Object.freeze({
  id: "leg_synthetic_large",
  bioguide_id: "SYNTHETIC-LARGE",
  name_display: "Large Record Example",
  chamber: "house",
  state: "ZZ",
  district: "00",
  party: "I",
});

export const syntheticLargeRecordFixtureData = Object.freeze({
  positions: Object.freeze({
    scope_metadata: Object.freeze({ congresses: Object.freeze([118, 119]), requested_congresses: Object.freeze([118, 119]), scope_label: "Example full record", window_start: "2024-05-15", window_end: "2025-05-15" }),
    positions: Object.freeze([{ domain: "PUBLIC_ADMINISTRATION_EXAMPLE", recorded_votes: 28, interpreted_support_count: 24, interpreted_oppose_count: 0, interpreted_other_count: 4, yea_share: 1, nay_share: 0 }]),
  }),
  evidenceByDomain: Object.freeze({ PUBLIC_ADMINISTRATION_EXAMPLE: Object.freeze({ domain: "PUBLIC_ADMINISTRATION_EXAMPLE", evidence: syntheticLargeRecordRows }) }),
});

function reference(id, candidate, evidenceRows) {
  return Object.freeze({ id, designation: candidate.standardizationFixture?.designation, candidate, evidenceRows });
}

function syntheticInterpretation(episode, roll, actionIndex, memberAction = "Yea") {
  const stage = actionIndex === 0 ? "Initial reviewed stage" : "Related later stage";
  return Object.freeze({
    roll,
    congress: episode?.congress || 119,
    measure_id: `synthetic-measure-${roll}`,
    stage,
    episode_id: episode?.id,
    member_action: memberAction,
    action_status: memberAction,
    human_approval_status: "human_approval_pending",
    ten_second: Object.freeze({
      headline: memberAction === "Not Voting" ? "Was not recorded on this example action" : `Supported example action ${roll}`,
      practical_choice: `Whether to adopt example action ${roll} at its exact reviewed stage.`,
      member_action_and_result: memberAction === "Not Voting" ? "The member was recorded as Not Voting." : `The member voted Yea. Example action ${roll} passed.`,
    }),
    thirty_second: Object.freeze({
      prior_baseline: "The prior example baseline remained in effect before this action.",
      mechanism: "The action would change one bounded example mechanism.",
      affected: "The example program and the people covered by it.",
      scale_or_timing: "The change would begin in the next fiscal year.",
      what_happened_next: `Example action ${roll} passed.`,
    }),
    two_minute: Object.freeze({
      supporter_argument: Object.freeze({ attribution: "Example supporter source", argument: "Supporters favored the bounded mechanism." }),
      opponent_argument: Object.freeze({ attribution: "Example opponent source", argument: "Opponents objected to the bounded mechanism." }),
      argument_boundary: "The arguments shown summarize the debate; they do not establish the member's reason for voting.",
      caveats: Object.freeze([]),
      sources: Object.freeze([
        source(`https://clerk.house.gov/Votes/2025${roll}`, `House Clerk roll call ${roll}`),
        source(`https://www.congress.gov/bill/119th-congress/house-bill/${roll}`, `Example measure ${roll}`),
      ]),
    }),
  });
}

function syntheticRow(episode, roll, position = "yea") {
  return Object.freeze({
    congress: episode.congress,
    rollcall_number: roll,
    vote_date: episode.congress === 118 ? "2024-05-15" : "2025-05-15",
    description: `Example measure ${roll}`,
    question: `Example action ${roll}`,
    vote_type: "final_passage",
    position,
    vote_context: Object.freeze({ final_result: "passed" }),
  });
}

function source(url, name) {
  return Object.freeze({ name, locator: "example action identity and status", group: "Vote and legislative status", url });
}
