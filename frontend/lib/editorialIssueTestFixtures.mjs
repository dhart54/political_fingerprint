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
  interpretation({ roll: 41, action: "Yes", position: "yea", headline: "Supported a fictional grid-resilience pilot", result: "The synthetic measure passed." }),
  interpretation({ roll: 57, action: "No", position: "nay", headline: "Opposed a fictional permitting deadline", result: "The synthetic measure failed." }),
  interpretation({ roll: 63, action: "Not Voting", position: "not_voting", headline: "Did not vote on a fictional reporting proposal", result: "The synthetic measure passed." }),
];

const controls = [{
  roll: 72,
  measure_id: "synthetic-context",
  member_action: "Yes",
  human_approval_status: "synthetic_test_only",
  context_summary: "Fictional procedural context bundled several unrelated actions",
  why_not_counted: "This synthetic row is context-only and does not count as support or opposition.",
  sources: [source("Synthetic context record", "https://example.test/context/72", "Vote and legislative status")],
}];

export const syntheticEditorialCandidate = Object.freeze({
  source: Object.freeze({
    member: { bioguide_id: syntheticEditorialLegislator.bioguide_id, name: syntheticEditorialLegislator.name_display },
    domain,
    human_approval_status: "synthetic_test_only",
    slice_counts: { substantive_rolls: 2, policy_episodes: 2, not_voting_records: 1, context_controls: 1 },
    interpretations,
    controls,
  }),
  identity: Object.freeze({
    memberId: syntheticEditorialLegislator.bioguide_id,
    memberDisplayName: syntheticEditorialLegislator.name_display,
    issueId: domain,
    issueDisplayName: "Synthetic Energy Choices",
    congress,
    reviewedPeriod: "Synthetic test period",
  }),
  publication: Object.freeze({
    editorialStatus: "human_approved",
    benchmarkStatus: "gold_benchmark",
    productionEligible: true,
    reviewLabel: "Synthetic test content \u2014 never a researched political claim",
  }),
  synthesis: Object.freeze({
    primary: "This synthetic sample is deliberately mixed: one fictional proposal was supported, one was opposed, and one was Not Voting.",
    patterns: Object.freeze(["Mixed actions across two independent fictional policy episodes."]),
    evidenceBreadth: "Synthetic mixed pattern",
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
    scope_metadata: { congresses: [congress], requested_congresses: [congress], scope_label: "Synthetic test period" },
    positions: [{ domain, recorded_votes: 4, interpreted_support_count: 1, interpreted_oppose_count: 1, interpreted_other_count: 2, yea_share: 0.5, nay_share: 0.5 }],
  },
  evidenceByDomain: { [domain]: { domain, evidence: syntheticRows } },
});

function interpretation({ roll, action, position, headline, result }) {
  return {
    roll,
    measure_id: `synthetic-episode-${roll}`,
    stage: "Synthetic House action",
    member_action: action,
    human_approval_status: "synthetic_test_only",
    ten_second: {
      headline,
      practical_choice: "This is a fictional practical choice used only to exercise the generic renderer.",
      member_action_and_result: `Jordan Example recorded ${action}. ${result}`,
    },
    thirty_second: {
      prior_baseline: "A fictional baseline existed before this synthetic vote.",
      mechanism: "The fictional proposal would change a test-only rule.",
      affected: "Imaginary agencies and example residents.",
      scale_or_timing: roll === 57 ? undefined : "A fictional two-year test window.",
      what_happened_next: result,
    },
    two_minute: {
      detail: "No real person, bill, jurisdiction, or political claim is represented by this fixture.",
      supporter_argument: { attribution: "Synthetic supporters", argument: "Supporters offered a fictional benefit argument." },
      opponent_argument: roll === 57 ? undefined : { attribution: "Synthetic opponents", argument: "Opponents offered a fictional implementation concern." },
      later_history: "No real legislative history exists.",
      caveats: [action === "Not Voting" ? "Not Voting is neither support nor opposition." : "This is synthetic test content."],
      sources: roll === 41
        ? [
            source("Synthetic roll source", "https://example.test/roll/41", "Vote and legislative status"),
            source("Duplicate synthetic roll source", "https://example.test/roll/41/", "Vote and legislative status"),
            source("Synthetic text", "https://example.test/text/41", "Bill or resolution text"),
          ]
        : [source(`Synthetic roll ${roll}`, `https://example.test/roll/${roll}`, "Vote and legislative status")],
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
    description: title,
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
  return { name, locator: "Synthetic locator", group, url };
}
