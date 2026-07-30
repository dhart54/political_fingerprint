export const foushee = {
  id: "leg_valerie_p_foushee",
  bioguide_id: "F000477",
  name_display: "Valerie P. Foushee",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};

export const bean = {
  id: "leg_aaron_bean",
  bioguide_id: "B001317",
  name_display: "Aaron Bean",
  chamber: "house",
  state: "FL",
  district: "04",
  party: "R",
};

export const positions = {
  scope_metadata: {
    congresses: [118, 119],
    requested_congresses: [118, 119],
    scope_label: "All available Congresses",
  },
  positions: [
    {
      domain: "ECONOMY_TAXES",
      yea_count: 8,
      nay_count: 4,
      other_count: 1,
      total_votes: 13,
      recorded_votes: 13,
      interpreted_support_count: 7,
      interpreted_oppose_count: 5,
      interpreted_other_count: 0,
      interpreted_total: 12,
    },
    {
      domain: "JUSTICE_PUBLIC_SAFETY",
      yea_count: 3,
      nay_count: 4,
      other_count: 0,
      total_votes: 7,
      recorded_votes: 7,
      interpreted_support_count: 3,
      interpreted_oppose_count: 4,
      interpreted_other_count: 0,
      interpreted_total: 7,
    },
    {
      domain: "EDUCATION_WORKFORCE",
      yea_count: 0,
      nay_count: 0,
      other_count: 1,
      total_votes: 1,
      recorded_votes: 0,
      interpreted_support_count: 0,
      interpreted_oppose_count: 0,
      interpreted_other_count: 1,
      interpreted_total: 1,
    },
  ],
};

export const reviewState = {
  catalog_key:
    "F000477:JUSTICE_PUBLIC_SAFETY:119:f000477:justice_public_safety:119:v1",
  member_id: "F000477",
  issue_id: "JUSTICE_PUBLIC_SAFETY",
  congress_scope: [119],
  published_artifact_identity: "f000477:justice_public_safety:119:v1",
  semantic_tier: "reviewed_conclusion",
  review_scope: "benchmark_sample",
  review_completion_state: "complete",
  public_claim_class: "reviewed_sample_finding",
  total_recorded_actions: 7,
  review_friendly_actions: 7,
  interpreted_actions: 7,
  unresolved_actions: 0,
  procedural_context_actions: 0,
  present_actions: 0,
  not_voting_actions: 0,
  complete_episode_count: 5,
  partial_episode_count: 0,
  full_issue_synthesis_eligible: false,
  benchmark_sample_available: true,
  scope_bounded_teaser: {
    text: "The reviewed 119th-Congress sample shows support for reporting and for evidence, research, or implementation conditions in two independent episodes, alongside opposition to three specific proposals concerning retired-service firearm access, broader D.C. police pursuit authority, or repeal of most reviewed D.C. policing restrictions.",
    valid_scope: "benchmark_sample",
  },
  public_status_label: "Reviewed benchmark sample",
};

export const justicePresentation = {
  issue_id: "JUSTICE_PUBLIC_SAFETY",
  requested_scope: "all",
  reviewed_scope: "119",
  tier: "reviewed_conclusion",
  tier_badge: "Reviewed conclusion",
  teaser: reviewState.scope_bounded_teaser.text,
  coverage_text:
    "This conclusion covers 7 reviewed substantive actions across 5 independent policy episodes in the 119th Congress.",
  scope_boundary:
    "This conclusion remains bounded to the reviewed 119th-Congress sample. The conclusion remains bounded to the reviewed 119th-Congress record.",
  public_status_label: "Reviewed benchmark sample",
  review_state: reviewState,
  conclusion: {
    headline: "A divide by policy mechanism in the reviewed sample",
    body: "In this reviewed 119th-Congress sample, Foushee supported reporting and evidence, research, or implementation conditions in two independent episodes, while opposing three specific proposals concerning retired-service firearm access, broader D.C. police pursuit authority, and repeal of most reviewed D.C. policing restrictions.",
  },
  repeated_patterns: [
    {
      proposition_id: "prop:support",
      semantic_role: "behavioral",
      direction: "support",
      heading: "Certification, fentanyl research provisions, and officer-safety reporting",
      body: "Across independent episodes, the reviewed wording describes support for these mechanisms.",
      action_ids: ["house:119:1:32", "house:119:1:131", "house:119:1:166"],
    },
    {
      proposition_id: "prop:oppose",
      semantic_role: "behavioral",
      direction: "opposition",
      heading: "Retired-service firearm access, D.C. pursuit authority, and policing-rule rollbacks",
      body: "Across independent episodes, the reviewed wording describes opposition to these specific proposals.",
      action_ids: ["house:119:1:130", "house:119:1:275", "house:119:1:299"],
    },
  ],
  policy_trajectories: [
    {
      proposition_id: "prop:mixed",
      semantic_role: "behavioral",
      direction: "mixed",
      heading: "The fentanyl episode is mixed",
      body: "The related stages include Yea, Nay, and Yea actions and do not establish a change in position or motive.",
      action_ids: ["house:119:1:32", "house:119:1:33", "house:119:1:166"],
    },
  ],
  limitations: [
    {
      heading: "Limits of this read",
      body: "The record does not establish motive, ideology, character, future behavior, or a broad Justice philosophy.",
    },
  ],
  policy_episodes: [],
};

export const episodePresentation = {
  ...justicePresentation,
  policy_episodes: [
    {
      episode_id: "newer-episode",
      latest_action_date: "2025-11-19",
      title: "Newer reviewed episode",
      practical_policy_question: "What should the newer policy do?",
      member_record: "One supplied Nay action.",
      outcome: "Supplied opposition outcome.",
      what_would_change: "The supplied implementation rule would change.",
      affected_people_or_institutions: "Named public institutions.",
      current_status: "The supplied episode is complete.",
      supporter_argument_summary: "Supporters supplied an implementation argument.",
      opponent_argument_summary: "Opponents supplied a scope argument.",
      one_sided_source_limitation: "Only one stakeholder source was supplied.",
      context_and_caveats: "This episode remains bounded to the listed actions.",
      official_sources: [
        {
          label: "Official episode source",
          url: "https://www.congress.gov/example/episode",
        },
      ],
      exact_actions: [
        { action_id: "newer-2", action_date: "2025-11-19", label: "Second action" },
        { action_id: "newer-1", action_date: "2025-09-17", label: "First action" },
      ],
    },
    {
      episode_id: "older-episode",
      latest_action_date: "2025-05-15",
      title: "Older reviewed episode",
      practical_policy_question: "What should the older policy do?",
      member_record: "One supplied Yea action.",
      outcome: "Supplied support outcome.",
      exact_actions: [],
    },
  ],
};

export function vote(roll, overrides = {}) {
  const position = [32, 131, 166].includes(roll) ? "yea" : "nay";
  const date = {
    32: "2025-02-06",
    33: "2025-02-06",
    130: "2025-05-15",
    131: "2025-05-15",
    166: "2025-06-12",
    275: "2025-09-17",
    299: "2025-11-19",
  }[roll] || "2025-01-10";
  return {
    chamber: "house",
    classification_reason: "policy_vote",
    congress: 119,
    description: `Justice measure ${roll}`,
    episode_relationship: "This exact action is one part of the supplied policy episode.",
    interpretation_status: "interpreted",
    issue_domain: "JUSTICE_PUBLIC_SAFETY",
    issue_facet: "justice_public_safety",
    oppose_position: "nay",
    plain_english_summary: `Justice measure ${roll} exact-action summary.`,
    policy_effect: `Justice measure ${roll} policy effect.`,
    position,
    question: `Whether to adopt Justice measure ${roll}.`,
    provenance_refs: [`receipt-${roll}`, `proposition-${roll}`],
    roll_call_id: `house:119:1:${roll}`,
    rollcall_number: roll,
    source_basis: [
      {
        label: "Official action-meaning source",
        url: `https://www.congress.gov/example/${roll}`,
      },
    ],
    source_url: `https://clerk.house.gov/Votes/2025${roll}`,
    support_position: "yea",
    uncertainty_note: "",
    vote_context: {
      final_result: "passed",
      member_party: "D",
      member_party_majority_position: position,
      vote_type: roll === 32 ? "amendment" : "final_passage",
    },
    vote_date: date,
    vote_type: roll === 32 ? "amendment" : "final_passage",
    what_happened: `Justice measure ${roll} action.`,
    why_it_mattered: `Justice measure ${roll} stakes.`,
    ...overrides,
  };
}

export const justiceEvidence = [32, 33, 130, 131, 166, 275, 299].map(
  (roll) => vote(roll, { roll_call_id: String(9000 + roll) }),
);

export const economyEvidence = Array.from({ length: 13 }, (_, index) => (
  vote(400 + index, {
    description: `Economic measure ${400 + index}`,
    issue_domain: "ECONOMY_TAXES",
    position: index % 2 ? "nay" : "yea",
    roll_call_id: `house:119:1:${400 + index}`,
    rollcall_number: 400 + index,
    vote_date: `2025-01-${String(index + 1).padStart(2, "0")}`,
  })
));

export const educationEvidence = [
  vote(500, {
    description: "Education attendance record",
    issue_domain: "EDUCATION_WORKFORCE",
    position: "not_voting",
    roll_call_id: "house:119:1:500",
    rollcall_number: 500,
    vote_date: "2025-03-20",
  }),
];

export async function installPassARoutes(page, { episodes = false } = {}) {
  const presentation = episodes ? episodePresentation : justicePresentation;
  await page.route("**/*", async (route) => {
    const requestUrl = new URL(route.request().url());
    if (!requestUrl.href.startsWith("http://localhost:8000")) {
      await route.continue();
      return;
    }
    const path = requestUrl.pathname.replace(/\/+$/, "");
    const scope = requestUrl.searchParams.get("scope") || "all";
    if (path.endsWith("/lookup/zip/27701")) {
      await route.fulfill({
        json: {
          zip: "27701",
          house_rep: foushee,
          senators: [],
          district_mappings: [{ state: "NC", district: "04" }],
        },
      });
      return;
    }
    if (path.endsWith("/legislators/search")) {
      await route.fulfill({
        json: { query: requestUrl.searchParams.get("q"), count: 1, results: [foushee] },
      });
      return;
    }
    if (path.endsWith(`/legislators/${foushee.id}/profile`)) {
      await route.fulfill({ json: foushee });
      return;
    }
    if (path.endsWith(`/legislators/${bean.id}/profile`)) {
      await route.fulfill({ json: bean });
      return;
    }
    if (path.endsWith("/editorial-presentations")) {
      const scopedPresentation = scope === "118"
        ? {
            ...justicePresentation,
            tier: "receipts_only",
            tier_badge: "Vote receipts",
            teaser: "Reviewed analytical wording is not published for this record scope.",
            public_status_label: "Vote receipts available",
            review_state: null,
            conclusion: null,
            repeated_patterns: [],
            policy_trajectories: [],
            limitations: [],
            policy_episodes: [],
          }
        : { ...presentation, requested_scope: scope };
      await route.fulfill({
        json: {
          schema_version: "editorial_public_presentations_api_v1",
          legislator_id: foushee.id,
          member_bioguide_id: foushee.bioguide_id,
          scope,
          presentations: [scopedPresentation],
        },
      });
      return;
    }
    if (path.endsWith("/positions")) {
      await route.fulfill({ json: positions });
      return;
    }
    if (path.endsWith("/positions/JUSTICE_PUBLIC_SAFETY/evidence")) {
      await route.fulfill({
        json: { domain: "JUSTICE_PUBLIC_SAFETY", evidence: justiceEvidence },
      });
      return;
    }
    if (path.endsWith("/positions/ECONOMY_TAXES/evidence")) {
      await route.fulfill({
        json: { domain: "ECONOMY_TAXES", evidence: economyEvidence },
      });
      return;
    }
    if (path.endsWith("/positions/EDUCATION_WORKFORCE/evidence")) {
      await route.fulfill({
        json: { domain: "EDUCATION_WORKFORCE", evidence: educationEvidence },
      });
      return;
    }
    await route.fulfill({ json: {} });
  });
}
