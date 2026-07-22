export const syntheticEditorialLegislator = Object.freeze({
  id: "synthetic_member_42",
  bioguide_id: "SYNTHETIC42",
  name_display: "Jordan Example",
  chamber: "house",
  state: "ZZ",
  district: "00",
  party: "I",
});

const domain = "ENVIRONMENT_ENERGY";
const congress = 120;

const interpretations = [
  interpretation({ roll: 41, action: "Yes", episodeId: "synthetic-grid-pilot", measureId: "synthetic-shared-measure", position: "yea", headline: "Supported a fictional grid-resilience pilot", result: "The proposal passed." }),
  interpretation({ roll: 57, action: "No", episodeId: "synthetic-permit-deadline", measureId: "synthetic-shared-measure", position: "nay", headline: "Opposed a fictional permitting deadline", result: "The proposal failed." }),
  interpretation({ roll: 63, action: "Not Voting", position: "not_voting", headline: "Did not vote on a fictional reporting proposal", result: "The proposal passed." }),
];

const controls = [{
  roll: 72,
  measure_id: "synthetic-context",
  member_action: "Yes",
  human_approval_status: "human_approved",
  context_summary: "A procedural record bundled several unrelated actions",
  why_not_counted: "This row concerns floor process and does not count as support or opposition.",
  sources: [source("Procedural record", "https://example.test/context/72", "Vote and legislative status")],
}];

export const syntheticEditorialCandidate = Object.freeze({
  source: Object.freeze({
    member: { bioguide_id: syntheticEditorialLegislator.bioguide_id, name: syntheticEditorialLegislator.name_display },
    domain,
    human_approval_status: "human_approved",
    slice_counts: { substantive_rolls: 2, policy_episodes: 2, not_voting_records: 1, context_controls: 1 },
    interpretations,
    controls,
  }),
  identity: Object.freeze({
    memberId: syntheticEditorialLegislator.bioguide_id,
    memberDisplayName: syntheticEditorialLegislator.name_display,
    issueId: domain,
    issueDisplayName: "Energy & Infrastructure",
    congress,
    reviewedPeriod: "January–March 2027",
  }),
  publication: Object.freeze({
    editorialStatus: "human_approved",
    benchmarkStatus: "gold_benchmark",
    productionEligible: true,
    reviewLabel: "Synthetic test content \u2014 never a researched political claim",
  }),
  synthesis: Object.freeze({
    primary: "In the reviewed record, one infrastructure proposal was supported, one was opposed, and one action was Not Voting.",
    patterns: Object.freeze(["The reviewed actions point in more than one direction across two independent policy episodes."]),
    evidenceBreadth: "Mixed but interpretable",
  }),
});

export const syntheticDevelopingEditorialCandidate = Object.freeze({
  ...syntheticEditorialCandidate,
  source: Object.freeze({
    ...syntheticEditorialCandidate.source,
    inference_candidate: Object.freeze({
      inference_level: "contested_candidate",
      independent_episode_count: 2,
      contrary_or_limiting_evidence: Object.freeze([
        Object.freeze({ text: "The two reviewed episodes point in different directions." }),
      ]),
    }),
  }),
  synthesis: Object.freeze({
    ...syntheticEditorialCandidate.synthesis,
    primary: "The reviewed record does not yet support a stable cross-episode conclusion.",
  }),
});

export const syntheticLimitedEditorialCandidate = Object.freeze({
  ...syntheticEditorialCandidate,
  source: Object.freeze({
    ...syntheticEditorialCandidate.source,
    slice_counts: Object.freeze({ substantive_rolls: 1, policy_episodes: 1, not_voting_records: 0, context_controls: 0 }),
    interpretations: Object.freeze(interpretations.slice(0, 1)),
    controls: Object.freeze([]),
    inference_candidate: Object.freeze({
      inference_level: "insufficient_evidence",
      independent_episode_count: 1,
    }),
  }),
  synthesis: Object.freeze({
    primary: "A single reviewed episode is available.",
    evidenceBreadth: "Insufficient evidence",
  }),
});

const syntheticRows = [
  evidenceRow({ roll: 41, position: "yea", title: "Synthetic Grid Pilot Act" }),
  evidenceRow({ roll: 57, position: "nay", title: "Synthetic Permit Deadline Act" }),
  evidenceRow({ roll: 63, position: "not_voting", title: "Synthetic Reporting Act" }),
  evidenceRow({ roll: 72, position: "yea", status: "ambiguous", title: "Synthetic bundled procedure", voteType: "procedural" }),
];

export const syntheticEditorialIssueFixtureData = Object.freeze({
  positions: {
    scope_metadata: { congresses: [congress], requested_congresses: [congress], scope_label: "January–March 2027" },
    positions: [{ domain, recorded_votes: 4, interpreted_support_count: 1, interpreted_oppose_count: 1, interpreted_other_count: 2, yea_share: 0.5, nay_share: 0.5 }],
  },
  evidenceByDomain: { [domain]: { domain, evidence: syntheticRows } },
});

export const syntheticLimitedEditorialIssueFixtureData = Object.freeze({
  positions: {
    scope_metadata: { congresses: [congress], requested_congresses: [congress], scope_label: "January–March 2027" },
    positions: [{ domain, recorded_votes: 1, interpreted_support_count: 1, interpreted_oppose_count: 0, interpreted_other_count: 0, yea_share: 1, nay_share: 0 }],
  },
  evidenceByDomain: { [domain]: { domain, evidence: syntheticRows.slice(0, 1) } },
});

export const proceduralOnlyIssueFixtureData = Object.freeze({
  positions: {
    scope_metadata: { congresses: [congress], requested_congresses: [congress], scope_label: "January–March 2027" },
    positions: [{ domain, recorded_votes: 1, interpreted_support_count: 0, interpreted_oppose_count: 0, interpreted_other_count: 1, yea_share: 0, nay_share: 0 }],
  },
  evidenceByDomain: {
    [domain]: {
      domain,
      evidence: [evidenceRow({ roll: 72, position: "yea", status: "ambiguous", title: "Rule for floor consideration", voteType: "procedural" })],
    },
  },
});

const limitedHealthRow = Object.freeze({
  ...evidenceRow({ roll: 81, position: "yea", title: "Community clinic pilot" }),
  issue_domain: "HEALTH_SOCIAL",
});
const proceduralEducationRow = Object.freeze({
  ...evidenceRow({ roll: 82, position: "yea", status: "ambiguous", title: "Rule for floor consideration", voteType: "procedural" }),
  issue_domain: "EDUCATION",
});

export const mixedAvailabilityIssueFixtureData = Object.freeze({
  positions: {
    scope_metadata: { congresses: [congress], requested_congresses: [congress], scope_label: "January–March 2027" },
    positions: [
      { domain, recorded_votes: 4, interpreted_support_count: 1, interpreted_oppose_count: 1, interpreted_other_count: 2, yea_share: 0.5, nay_share: 0.5 },
      { domain: "HEALTH_SOCIAL", recorded_votes: 1, interpreted_support_count: 1, interpreted_oppose_count: 0, interpreted_other_count: 0, yea_share: 1, nay_share: 0 },
      { domain: "EDUCATION", recorded_votes: 1, interpreted_support_count: 0, interpreted_oppose_count: 0, interpreted_other_count: 1, yea_share: 0, nay_share: 0 },
    ],
  },
  evidenceByDomain: {
    [domain]: { domain, evidence: syntheticRows },
    HEALTH_SOCIAL: { domain: "HEALTH_SOCIAL", evidence: [limitedHealthRow] },
    EDUCATION: { domain: "EDUCATION", evidence: [proceduralEducationRow] },
  },
});

function interpretation({ roll, action, episodeId, measureId, position, headline, result }) {
  return {
    roll,
    measure_id: measureId || `synthetic-measure-${roll}`,
    ...(episodeId ? { episode_id: episodeId } : {}),
    stage: "House action",
    member_action: action,
    human_approval_status: "human_approved",
    ten_second: {
      headline,
      practical_choice: "The proposal presented a concrete choice about a fictional public program.",
      member_action_and_result: `Jordan Example recorded ${action}. ${result}`,
    },
    thirty_second: {
      prior_baseline: "A fictional baseline existed before this vote.",
      mechanism: "The fictional proposal would change a test-only rule.",
      affected: "Imaginary agencies and example residents.",
      scale_or_timing: roll === 57 ? undefined : "A fictional two-year test window.",
      what_happened_next: result,
    },
    two_minute: {
      detail: "The record explains the proposal's practical mechanism and outcome.",
      supporter_argument: { attribution: "Proposal supporters", argument: "Supporters offered a benefit argument." },
      opponent_argument: roll === 57 ? undefined : { attribution: "Proposal opponents", argument: "Opponents raised an implementation concern." },
      later_history: "No real legislative history exists.",
      caveats: [action === "Not Voting" ? "Not Voting is neither support nor opposition." : "The vote record does not reveal why the member voted this way."],
      sources: roll === 41
        ? [
            source("Roll-call record", "https://example.test/roll/41", "Vote and legislative status"),
            source("Duplicate roll-call record", "https://example.test/roll/41/", "Vote and legislative status"),
            source("Proposal text", "https://example.test/text/41", "Bill or resolution text"),
          ]
        : [source(`Roll-call record ${roll}`, `https://example.test/roll/${roll}`, "Vote and legislative status")],
    },
    _position: position,
  };
}

function evidenceRow({ roll, position, status = "interpreted", title, voteType = "final_passage" }) {
  return {
    roll_call_id: `synthetic-${roll}`,
    congress,
    rollcall_number: roll,
    vote_date: `2027-02-${String(roll % 20 + 1).padStart(2, "0")}`,
    chamber: "house",
    description: title.replace(/^Synthetic /, ""),
    question: title,
    issue_domain: domain,
    interpretation_status: status,
    position,
    support_position: "yea",
    oppose_position: "nay",
    vote_type: voteType,
    source_url: `https://example.test/roll/${roll}`,
    vote_context: { final_result: roll === 57 ? "failed" : "passed" },
  };
}

function source(name, url, group) {
  return { name, locator: "Record locator", group, url };
}
