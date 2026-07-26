import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { buildIssueOverview, formatRenderedIssueOverview } from "./issueOverview.mjs";
import { buildLimitedContextSummary, buildVoteCardSummary } from "./voteCardSummary.mjs";

const partyOutcomeContext = {
  member_party: "D",
  member_voted_with_party_majority: true,
  member_voted_with_winning_side: false,
};

const valerieEconomyRows = [
  row({
    description: "Establishing the congressional budget for the United States Government for fiscal year 2025",
    issue_facet: "budget_reconciliation_and_debt_limit",
    policy_effect: "Budget instructions for later tax, spending, deficit, and debt-limit legislation.",
    rollcall_number: 50,
    what_happened: "The House adopted a budget blueprint that started reconciliation instructions for later budget legislation.",
    why_it_mattered: "The vote opened a fast-track process for later tax, spending, deficit, and debt-limit legislation.",
  }),
  row({
    description: "Establishing the congressional budget for the United States Government for fiscal year 2025",
    issue_facet: "budget_reconciliation_and_debt_limit",
    policy_effect: "Reconciliation instructions for later tax, spending, deficit, and debt-limit legislation.",
    rollcall_number: 100,
    what_happened: "The House agreed to the Senate-amended budget framework for FY2025-FY2034 reconciliation instructions.",
    why_it_mattered: "The vote kept the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation.",
  }),
  row({
    description: "American Entrepreneurs First Act",
    issue_facet: "small_business_loan_eligibility",
    policy_effect: "Eligibility rules for SBA 7(a) and 504 loans.",
    rollcall_number: 156,
    what_happened: "The House passed a bill changing eligibility requirements for SBA 7(a) and 504 small-business loans.",
    why_it_mattered: "The vote concerned whether certain SBA-backed business loans should be limited to citizens, nationals, or lawful permanent residents.",
  }),
  row({
    description: "Carter of Texas Amendment En Bloc No. 2",
    interpretation_status: "ambiguous",
    issue_facet: "appropriations_amendment",
    policy_effect: "",
    rollcall_number: 180,
    uncertainty_note: "The official amendment text was not clear enough to explain the practical change.",
  }),
  row({
    description: "Military Construction, Veterans Affairs, and Related Agencies Appropriations Act, 2026",
    issue_facet: "military_construction_and_va_appropriations",
    policy_effect: "Annual appropriations for military construction and Veterans Affairs programs.",
    rollcall_number: 182,
    what_happened: "The House passed an FY2026 appropriations bill for military construction, Veterans Affairs, and related agencies.",
    why_it_mattered: "The vote concerned House approval of funding for military construction, military housing, veterans benefits, veterans health programs, and related agencies.",
  }),
  row({
    description: "DeLauro Motion to Instruct Conferees",
    interpretation_status: "ambiguous",
    issue_facet: "conference_instruction",
    position: "yea",
    rollcall_number: 263,
    uncertainty_note: "The source did not include enough official instruction text to describe the exact policy effect.",
  }),
  row({
    description: "Continuing Appropriations and Extensions Act, 2026",
    issue_facet: "temporary_government_funding",
    policy_effect: "Continuing appropriations to keep agencies operating temporarily.",
    rollcall_number: 281,
    what_happened: "The House passed an initial short-term FY2026 funding bill before later Senate changes.",
    why_it_mattered: "The vote concerned whether to keep most federal agencies operating temporarily while regular appropriations bills were still unfinished.",
  }),
  row({
    description: "Continuing Appropriations and Extensions Act, 2026",
    issue_facet: "government_funding_and_shutdown",
    policy_effect: "Funding terms for reopening or continuing federal operations.",
    rollcall_number: 285,
    what_happened: "The House agreed to the Senate-amended funding package that ended the 2025 shutdown and sent the measure to the President.",
    why_it_mattered: "The vote affected whether federal operations would reopen or continue.",
  }),
  row({
    description: "Small Business Regulatory Reduction Act",
    issue_facet: "small_business_regulation",
    policy_effect: "A cap on net new SBA regulatory costs for small businesses.",
    position: "not_voting",
    rollcall_number: 310,
    support_position: "yea",
    what_happened: "The House passed a bill that would require the Small Business Administration to keep its annual small-business regulatory budget at zero or below.",
    why_it_mattered: "The vote concerned how much new regulatory cost the SBA could impose on small businesses through its own rulemaking.",
  }),
];

const valerieJusticeRows = [
  row({
    description: "HALT Fentanyl Act",
    issue_facet: "fentanyl_scheduling_and_penalties",
    plain_english_summary: "This was House passage of the HALT Fentanyl Act. The bill would permanently place fentanyl-related substances as a class into Schedule I.",
    policy_effect: "The bill would move fentanyl-related substances from temporary classwide scheduling to permanent Schedule I status, apply fentanyl-analogue quantity thresholds and penalties, and create or revise registration paths for certain Schedule I research.",
    rollcall_number: 33,
    vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
  }),
  row({
    description: "Federal Law Enforcement Officer Service Weapon Purchase Act",
    issue_facet: "federal_law_enforcement_equipment",
    plain_english_summary: "This was House passage of the Federal Law Enforcement Officer Service Weapon Purchase Act.",
    policy_effect: "The bill would require GSA to establish a process for federal law enforcement officers to purchase retired agency-issued firearms from their issuing agencies.",
    rollcall_number: 130,
    vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
  }),
  row({
    description: "Improving Law Enforcement Officer Safety and Wellness Through Data Act",
    issue_facet: "law_enforcement_safety_reporting",
    plain_english_summary: "This was House passage of the Improving Law Enforcement Officer Safety and Wellness Through Data Act.",
    policy_effect: "The bill would create a DOJ reporting requirement rather than directly changing criminal penalties or law enforcement operations.",
    position: "yea",
    rollcall_number: 131,
    vote_context: { ...partyOutcomeContext, final_result: "passed", member_voted_with_winning_side: true, vote_type: "final_passage" },
  }),
  row({
    description: "District of Columbia Policing Protection Act",
    issue_facet: "dc_police_pursuit_policy",
    plain_english_summary: "This was House passage of the District of Columbia Policing Protection Act.",
    policy_effect: "The bill would change D.C. police-pursuit rules by removing current restrictions and adding a general pursuit requirement with exceptions.",
    rollcall_number: 275,
    vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
  }),
  row({
    description: "CLEAN DC Act",
    issue_facet: "dc_policing_reform_repeal",
    plain_english_summary: "This was House passage of the CLEAN DC Act.",
    policy_effect: "The bill would reverse D.C. policing reforms involving neck-restraint limits, body-worn camera procedures, and access to police disciplinary records.",
    rollcall_number: 299,
    vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
  }),
  row({
    description: "Trahan of Massachusetts Part B Amendment No. 2",
    interpretation_status: "ambiguous",
    issue_facet: "administrative_law_and_regulatory_procedures",
    position: "yea",
    rollcall_number: 32,
    support_position: null,
    oppose_position: null,
    uncertainty_note: "The packet identifies an amendment vote, but the cached bill summary describes the underlying bill rather than the exact amendment change.",
  }),
  row({
    description: "Providing for consideration of the bills H.R. 884, H.R. 2056, H.R. 2096, S. 331, and for other purposes",
    interpretation_status: "insufficient_evidence",
    issue_facet: "house_of_representatives",
    rollcall_number: 160,
    support_position: null,
    oppose_position: null,
    uncertainty_note: "The available official text describes a procedural motion or rule rather than a clear final policy choice.",
  }),
];

test("Valerie Foushee Economy & Taxes overview names required measure groups and limits", () => {
  const overview = buildIssueOverview(valerieEconomyRows, {
    domain: "ECONOMY_TAXES",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.votePattern.interpretedYesNoCount, 6);
  assert.equal(overview.votePattern.opposeCount, 6);
  assert.equal(overview.votePattern.supportCount, 0);
  assert.equal(overview.votePattern.notVotingCount, 1);
  assert.equal(overview.votePattern.ambiguousCount, 2);

  for (const expected of [
    "budget framework",
    "small-business loan eligibility",
    "military and veterans appropriations",
    "temporary government funding",
    "shutdown-ending",
    "not-voting row",
    "ambiguous or limited-context rows",
  ]) {
    assert.match(rendered, new RegExp(expected, "i"));
  }

  assert.match(rendered, /In this reviewed sample, Foushee mostly opposed the reviewed Economy & Taxes measures: 6 opposed and 0 supported across 6 interpreted Yes\/No votes\./);
  assert.match(rendered, /The reviewed Yes\/No votes covered budget framework and reconciliation, small-business loan eligibility/);
  assert.match(rendered, /A voter who favored those measures would read Foushee's votes as mostly opposition in this sample\./);
  assert.match(rendered, /All of those votes matched most Democrats\./);
  assert.ok(
    rendered.indexOf("A voter who favored those measures") <
      rendered.indexOf("How to read this"),
    "concrete policy-substance voter read should appear before broad scope limits",
  );
  assert.doesNotMatch(rendered, /If you generally favored these House Republican/);
  assert.match(rendered, /^Finding\nIn this reviewed sample, Foushee mostly opposed/m);
  assert.match(rendered, /How to read this\nThis read is based on the reviewed votes shown here/);
  assert.doesNotMatch(rendered, /The vote record alone does not show her motive/);
  assert.doesNotMatch(rendered, /stored vote context|for-side|against-side|plus other reviewed measures|leans Nay|is corrupt|character judgment|you should vote|support this candidate|oppose this candidate/i);
});

test("Valerie Foushee Economy & Taxes overview text remains approved copy", () => {
  const overview = buildIssueOverview(valerieEconomyRows, {
    domain: "ECONOMY_TAXES",
    representativeName: "Valerie P. Foushee",
  });

  assert.equal(formatRenderedIssueOverview(overview), `Finding
In this reviewed sample, Foushee mostly opposed the reviewed Economy & Taxes measures: 6 opposed and 0 supported across 6 interpreted Yes/No votes. The reviewed votes centered on budget framework and reconciliation, small-business loan eligibility, military and veterans appropriations, temporary government funding, and shutdown-ending government funding. All of those votes matched most Democrats. All were against the final House outcome. Open the representative votes below to inspect the record behind this read.

What these votes were about
The reviewed Yes/No votes covered budget framework and reconciliation, small-business loan eligibility, military and veterans appropriations, temporary government funding, and shutdown-ending government funding. A separate not-voting row concerned small-business regulatory-cost limits, but Foushee was recorded as not voting, so it is explained below and not counted as support or opposition. Two ambiguous or limited-context rows remain visible for appropriations amendments and conference instructions, but they are not used to summarize the vote pattern.

How a voter might read that
A voter who favored those measures would read Foushee's votes as mostly opposition in this sample. A voter who opposed those measures or objected to their terms would read this record as mostly aligned with that view.

How to read this
This read is based on the reviewed votes shown here. Vote records show actions, not motive, ideology, character, corruption, or a voting recommendation. The rows show recorded votes and reviewed bill meaning for this sample, not her full fiscal record. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.`);
});

test("evidence card disclosure keeps public summary visible and audit details collapsed", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  const cardStart = source.indexOf("<InterpretationBreakdown");
  const sourceButtonStart = source.indexOf("{row.source_url ?", cardStart);
  const cardEnd = source.indexOf("</div>", sourceButtonStart);
  const breakdownStart = source.indexOf("function InterpretationBreakdown");
  const breakdownEnd = source.indexOf("function InsightCard", breakdownStart);
  const breakdownSource = source.slice(breakdownStart, breakdownEnd);
  const detailsStart = breakdownSource.indexOf("<details");
  const detailsEnd = breakdownSource.indexOf("</details>", detailsStart);
  const officialVoteRecordStart = breakdownSource.indexOf("Official Vote Record");
  const voteSummaryStart = breakdownSource.indexOf('label="Vote summary"');
  const whyThisMatteredStart = breakdownSource.indexOf('label="Why this mattered"');

  assert.ok(voteSummaryStart > 0, "vote summary must be rendered by the card");
  assert.ok(whyThisMatteredStart > voteSummaryStart, "why-it-mattered should follow the vote summary");
  assert.ok(detailsStart > whyThisMatteredStart, "details should come after the public summary layer");
  assert.ok(sourceButtonStart > cardStart && sourceButtonStart < cardEnd, "source link should stay in the default-visible card layer");
  assert.doesNotMatch(breakdownSource, /Source basis|source_basis|Included as|classification reason/i);
  assert.ok(officialVoteRecordStart > detailsStart && officialVoteRecordStart < detailsEnd, "official vote record action should stay inside details");
});

test("basic issue navigation does not rebuild issue-card conclusions", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");

  assert.match(source, /function BasicIssueList/);
  assert.match(source, /without combining them into a broader issue conclusion/);
  assert.doesNotMatch(source, /buildIssueCardPreview|formatIssueCardStatusLabel|IssueReadinessTile/);
  assert.doesNotMatch(source, /from "\.\.\/lib\/issueReadiness\.mjs"/);
});

test("public vote-card runtime has no member or roll-number presentation branches", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  assert.doesNotMatch(source, /Foushee|buildKnownVoteCardSummary|rollNumber\s*===|rollcall_number\s*===/);
  assert.match(source, /buildGenericVoteCardSummary/);
  assert.match(source, /buildGenericLimitedContextSummary/);
  assert.ok(source.includes("Plain-English"));
  assert.ok(source.includes("Official Vote Record"));
});

test("Justice & Public Safety overview uses domain-aware generic language", () => {
  const overview = buildIssueOverview(valerieJusticeRows, {
    domain: "JUSTICE_PUBLIC_SAFETY",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.issueLabel, "Justice & Public Safety");
  assert.equal(overview.votePattern.supportCount, 1);
  assert.equal(overview.votePattern.opposeCount, 4);
  assert.equal(overview.votePattern.ambiguousCount, 2);
  assert.equal(overview.votePattern.predominantPosition, "mostly opposed interpreted measures");
  assert.deepEqual(
    overview.measureGroups.map((group) => group.label),
    [
      "fentanyl scheduling and penalty thresholds",
      "federal law-enforcement retired weapon purchases",
      "law-enforcement safety reporting",
      "D.C. police pursuit policy",
      "D.C. policing reform repeal",
    ],
  );
  assert.match(rendered, /The reviewed Yes\/No votes covered fentanyl scheduling and penalty thresholds/);
  assert.match(rendered, /federal law-enforcement retired weapon purchasing/);
  assert.match(rendered, /law-enforcement safety and wellness reporting/);
  assert.match(rendered, /D\.C\. police pursuit policy/);
  assert.match(rendered, /D\.C\. policing reform repeal/);
  assert.match(rendered, /mostly opposed the reviewed Justice & Public Safety measures: 4 opposed and 1 supported across 5 interpreted Yes\/No votes/);
  assert.match(rendered, /A voter who favored those measures would read Foushee's votes as mostly opposition in this sample\./);
  assert.match(rendered, /Most opposed measures that passed the House\./);
  assert.match(rendered, /Two additional rows remain visible below, including one procedural-context row and one other limited-context row; they are not used to summarize support, opposition, or alignment\./);
  assert.doesNotMatch(rendered, /If you generally favored these House Republican measures|not as a simple statement that she is broadly for or against this issue area/);
  assert.doesNotMatch(rendered, /whether to|concrete fiscal questions|for" or "against taxes|full fiscal record|JUSTICE PUBLIC SAFETY|administrative law and regulatory procedures|house of representatives|Yes-pattern|No-pattern/);
});

test("dominant National Security sample is mostly opposed, not mixed", () => {
  const nationalSecurityRows = [
    ...Array.from({ length: 70 }, (_, index) =>
      row({
        description: `Defense authorization vote ${index}`,
        issue_facet: "Defense authorization",
        position: "nay",
        rollcall_number: 200 + index,
        what_happened: "The House passed defense authorization legislation.",
        why_it_mattered: "The vote concerned annual defense and national-security policy authorization.",
      }),
    ),
    ...Array.from({ length: 38 }, (_, index) =>
      row({
        description: `Foreign military sale vote ${index}`,
        issue_facet: "foreign_military_sales",
        position: "nay",
        rollcall_number: 400 + index,
        what_happened: "The Senate voted on whether to allow a specific foreign military sale to proceed.",
        why_it_mattered: "The vote concerned whether to allow or disapprove a specific foreign military sale.",
      }),
    ),
    ...Array.from({ length: 20 }, (_, index) =>
      row({
        description: `Veterans cemetery vote ${index}`,
        issue_facet: "Veterans cemetery administration",
        position: "nay",
        rollcall_number: 500 + index,
        what_happened: "The House passed a bill affecting veterans cemetery administration.",
        why_it_mattered: "The vote concerned legislation affecting veterans cemetery administration.",
      }),
    ),
    ...Array.from({ length: 22 }, (_, index) =>
      row({
        description: `Motion to commit vote ${index}`,
        issue_facet: "Motion to commit",
        position: "yea",
        rollcall_number: 600 + index,
        what_happened: "The House considered a procedural motion to commit.",
        why_it_mattered: "The vote concerned whether to send the measure back for further consideration.",
      }),
    ),
  ];
  const overview = buildIssueOverview(nationalSecurityRows, {
    domain: "NATIONAL_SECURITY_FOREIGN",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.votePattern.opposeCount, 128);
  assert.equal(overview.votePattern.supportCount, 22);
  assert.equal(overview.votePattern.predominantPosition, "mostly opposed interpreted measures");
  const finding = rendered.split("\n\nWhat these votes were about")[0];

  assert.match(finding, /In this reviewed sample, Foushee mostly opposed the reviewed National Security & Foreign Policy measures: 128 opposed and 22 supported across 150 interpreted Yes\/No votes\./);
  assert.match(finding, /Opposition was concentrated in defense authorization legislation, foreign military sales, and veterans cemetery administration; support appeared in motions to commit\./);
  assert.equal(countOccurrences(finding, "defense authorization legislation, foreign military sales"), 1);
  assert.doesNotMatch(finding, /this was a direct vote|the vote is useful because|records a direct position/i);
  assert.match(rendered, /A voter who favored those measures would read Foushee's votes as mostly opposition in this sample\./);
  assert.doesNotMatch(rendered, /split rather than mostly support|mixed but interpretable|broadly for or against National Security/i);
});

test("National Security public copy blocks raw evidence and audit phrase leakage", () => {
  const unsafeOpposedStrings = [
    "this was a direct vote on Protecting America's Strategic Petroleum Reserve from China Act",
    "the House voted on whether to agree to Biggs of Arizona Part A Amendment No. 149",
    "the amendment decreases funding for the Ukraine Security Assistance Initiative",
    "the vote is useful because it records a direct position",
  ];
  const unsafeSupportedStrings = [
    "this vote is useful because it records a direct position on war powers",
    "official roll call description says whether to agree to the amendment",
    "source basis: classification reason copied from audit text",
  ];
  const nationalSecurityRows = [
    ...Array.from({ length: 70 }, (_, index) =>
      row({
        description: unsafeOpposedStrings[index % unsafeOpposedStrings.length],
        issue_facet: index % 2 === 0 ? "Defense authorization amendment" : "china_related_security_restrictions",
        plain_english_summary: unsafeOpposedStrings[(index + 1) % unsafeOpposedStrings.length],
        policy_effect: unsafeOpposedStrings[(index + 2) % unsafeOpposedStrings.length],
        rollcall_number: 200 + index,
        what_happened: unsafeOpposedStrings[index % unsafeOpposedStrings.length],
        why_it_mattered: unsafeOpposedStrings[(index + 3) % unsafeOpposedStrings.length],
      }),
    ),
    ...Array.from({ length: 38 }, (_, index) =>
      row({
        description: unsafeOpposedStrings[index % unsafeOpposedStrings.length],
        issue_facet: "foreign_military_sales",
        plain_english_summary: unsafeOpposedStrings[index % unsafeOpposedStrings.length],
        rollcall_number: 400 + index,
        what_happened: unsafeOpposedStrings[index % unsafeOpposedStrings.length],
        why_it_mattered: unsafeOpposedStrings[(index + 1) % unsafeOpposedStrings.length],
      }),
    ),
    ...Array.from({ length: 20 }, (_, index) =>
      row({
        description: unsafeOpposedStrings[index % unsafeOpposedStrings.length],
        issue_facet: "Veterans cemetery administration",
        rollcall_number: 500 + index,
        what_happened: unsafeOpposedStrings[(index + 2) % unsafeOpposedStrings.length],
        why_it_mattered: unsafeOpposedStrings[(index + 3) % unsafeOpposedStrings.length],
      }),
    ),
    ...Array.from({ length: 22 }, (_, index) =>
      row({
        description: unsafeSupportedStrings[index % unsafeSupportedStrings.length],
        issue_facet: index % 2 === 0 ? "war_powers_votes" : "unknown_long_raw_facet_that_should_fall_back_because_it_has_far_too_many_words_for_public_copy",
        position: "yea",
        rollcall_number: 600 + index,
        what_happened: unsafeSupportedStrings[index % unsafeSupportedStrings.length],
        why_it_mattered: unsafeSupportedStrings[(index + 1) % unsafeSupportedStrings.length],
      }),
    ),
    row({
      description: "Official context row",
      interpretation_status: "insufficient_evidence",
      issue_facet: "unknown_long_raw_facet_that_should_fall_back_because_it_has_far_too_many_words_for_public_copy",
      position: "nay",
      rollcall_number: 900,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "the amendment redirects funds and source basis text should not be public overview copy",
    }),
  ];
  const overview = buildIssueOverview(nationalSecurityRows, {
    domain: "NATIONAL_SECURITY_FOREIGN",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.votePattern.opposeCount, 128);
  assert.equal(overview.votePattern.supportCount, 22);
  assert.equal(overview.votePattern.predominantPosition, "mostly opposed interpreted measures");
  assert.match(rendered, /mostly opposed the reviewed National Security & Foreign Policy measures: 128 opposed and 22 supported across 150 interpreted Yes\/No votes/);
  assert.match(rendered, /defense authorization amendments/);
  assert.match(rendered, /China-related security restrictions/);
  assert.match(rendered, /foreign military sales/);
  assert.match(rendered, /veterans cemetery administration/);
  assert.match(rendered, /war-powers votes/);
  assert.match(rendered, /other reviewed national-security measures/);
  assertTopPublicCopyIsSafe(rendered);
  assertTopPublicCopyIsSafe(overview.copy.whatRepresentativeDid);
  assertTopPublicCopyIsSafe(overview.copy.whatPatternThatCreates);
  assertTopPublicCopyIsSafe(overview.copy.whatTheseVotesWereAbout);
  assertTopPublicCopyIsSafe(overview.copy.howVoterMightRead);
});

test("issue overview keeps genuinely split interpreted samples out of mostly framing", () => {
  const splitRows = [
    row({
      issue_facet: "fentanyl_scheduling_and_penalties",
      position: "yea",
      support_position: "yea",
      oppose_position: "nay",
      rollcall_number: 301,
    }),
    row({
      issue_facet: "federal_law_enforcement_equipment",
      position: "yea",
      support_position: "yea",
      oppose_position: "nay",
      rollcall_number: 302,
    }),
    row({
      issue_facet: "law_enforcement_safety_reporting",
      position: "nay",
      support_position: "yea",
      oppose_position: "nay",
      rollcall_number: 303,
    }),
    row({
      issue_facet: "dc_police_pursuit_policy",
      position: "nay",
      support_position: "yea",
      oppose_position: "nay",
      rollcall_number: 304,
    }),
  ];
  const overview = buildIssueOverview(splitRows, {
    domain: "JUSTICE_PUBLIC_SAFETY",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.votePattern.predominantPosition, "split interpreted vote pattern");
  assert.match(rendered, /interpreted Justice & Public Safety votes were mixed rather than mostly support or mostly opposition/);
  assert.match(rendered, /Because the reviewed votes point in more than one direction/);
  assert.match(rendered, /instead of reading this as mostly support or mostly opposition/);
  assert.doesNotMatch(rendered, /mostly opposed the reviewed Justice & Public Safety measures|mostly supported the reviewed Justice & Public Safety measures/);
  assert.doesNotMatch(rendered, /mostly opposed public-safety|mostly supported public-safety|If you generally favored these House Republican/);
});

test("generic Justice card summaries use legislator name and clean punctuation", () => {
  const summary = buildVoteCardSummary(valerieJusticeRows[0], {
    representativeName: "Valerie P. Foushee",
  });
  const federalLawEnforcementSummary = buildVoteCardSummary(valerieJusticeRows[1], {
    representativeName: "Valerie P. Foushee",
  });
  const limitedSummary = buildLimitedContextSummary(valerieJusticeRows[6]);

  assert.equal(
    summary,
    "Nay. The House passed the HALT Fentanyl Act, which would permanently place fentanyl-related substances as a class into Schedule I and apply fentanyl-analogue penalty thresholds, while creating or revising research-registration paths. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    federalLawEnforcementSummary,
    "Nay. The House passed a bill directing GSA to create a process for federal law-enforcement officers to buy retired agency-issued firearms. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.",
  );
  assert.doesNotMatch(summary, /This representative|\. matching|interpreted measure/);
  assert.match(limitedSummary, /Procedural-context row/);
  assert.match(limitedSummary, /not counted as support or opposition/);
  assert.match(limitedSummary, /should not be read as final passage/);
});

test("generic card summaries do not lead with audit rationale", () => {
  const summary = buildVoteCardSummary(
    row({
      description: "Public safety bill",
      issue_facet: "unmapped_public_safety_bill",
      plain_english_summary: "The vote is useful because the bill would change public safety grant rules.",
      policy_effect: "The vote records a direct position on whether to change public safety grant rules.",
      rollcall_number: 390,
    }),
    {
      representativeName: "Valerie P. Foushee",
    },
  );

  assert.match(summary, /^Nay\. The bill would change public safety grant rules\./);
  assert.match(summary, /Foushee voted Nay/);
  assert.doesNotMatch(summary, /The vote is useful because|records a direct position/);
});

test("generic card summary templates improve top non-gold interpreted facets", () => {
  const summaryRows = [
    row({
      chamber: "house",
      issue_facet: "law_enforcement_safety_reporting",
      position: "yea",
      rollcall_number: 131,
      vote_context: { ...partyOutcomeContext, final_result: "passed", member_voted_with_winning_side: true, vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "dc_police_pursuit_policy",
      rollcall_number: 275,
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "school_foreign_funding_and_contract_restrictions",
      rollcall_number: 301,
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "medicaid_payment_rules",
      position: "yea",
      rollcall_number: 501,
      vote_context: { ...partyOutcomeContext, final_result: "passed", member_voted_with_winning_side: true, vote_type: "final_passage" },
    }),
    row({
      chamber: "senate",
      issue_facet: "foreign_military_sales",
      rollcall_number: 12,
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "passage" },
    }),
  ];
  const summaries = summaryRows.map((summaryRow) =>
    buildVoteCardSummary(summaryRow, {
      representativeName: "Valerie P. Foushee",
    }),
  );
  const limitedSummary = buildLimitedContextSummary(
    row({
      interpretation_status: "insufficient_evidence",
      issue_facet: "Defense authorization amendment",
      rollcall_number: 202,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available source text identifies an amendment but does not explain the full practical policy effect.",
    }),
  );

  assert.equal(
    summaries[0],
    "Yea. The House passed a bill requiring DOJ reports on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[1],
    "Nay. The House passed a bill changing D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with listed exceptions. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[2],
    "Nay. The House passed a bill adding school restrictions tied to foreign funding, contracts, or influence. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[3],
    "Yea. The House passed a bill restricting federal Medicaid payment for specified procedures involving minors. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[4],
    "Nay. The Senate voted on whether to allow a specific foreign military sale to proceed. Foushee voted against allowing that foreign military sale to proceed, matching most Democrats. The measure passed.",
  );
  assert.match(limitedSummary, /This row remains visible but is not counted in the summarized vote pattern/);

  const publicCopy = [...summaries, limitedSummary].join(" ");
  assert.match(publicCopy, /Foushee voted/);
  assert.doesNotMatch(publicCopy, /This representative|\. matching|stored vote context|for-side|against-side|leans Nay|plus other reviewed measures|Yes-pattern|No-pattern|is corrupt|you should vote/i);
});

test("phase 1 generic templates cover additional high-confidence facets without upgrading limited rows", () => {
  const summaryRows = [
    row({
      chamber: "house",
      issue_facet: "dc_policing_reform_repeal",
      rollcall_number: 299,
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "school_foreign_influence_parent_notifications",
      position: "yea",
      rollcall_number: 302,
      vote_context: { ...partyOutcomeContext, final_result: "passed", member_voted_with_winning_side: true, vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "health_insurance_premium_assistance",
      rollcall_number: 500,
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "defense_authorization",
      position: "yea",
      rollcall_number: 200,
      vote_context: { ...partyOutcomeContext, final_result: "passed", member_voted_with_winning_side: true, vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "natural_gas_pipeline_and_lng_review_coordination",
      rollcall_number: 400,
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "final_passage" },
    }),
    row({
      chamber: "house",
      issue_facet: "federal_employee_collective_bargaining",
      position: "yea",
      rollcall_number: 300,
      vote_context: { ...partyOutcomeContext, final_result: "passed", member_voted_with_winning_side: true, vote_type: "final_passage" },
    }),
  ];
  const summaries = summaryRows.map((summaryRow) =>
    buildVoteCardSummary(summaryRow, {
      representativeName: "Valerie P. Foushee",
    }),
  );
  const limitedSummary = buildLimitedContextSummary(
    row({
      interpretation_status: "insufficient_evidence",
      issue_facet: "House floor procedure",
      rollcall_number: 401,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "This was a floor-rule vote, not final passage of the underlying policies.",
    }),
  );

  assert.equal(
    summaries[0],
    "Nay. The House passed a bill that would repeal D.C.'s 2022 policing and justice reform act, including provisions related to neck restraints, body-worn cameras, and police disciplinary records. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[1],
    "Yea. The House passed a bill requiring parent notifications about foreign-influence issues in schools. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[2],
    "Nay. The House passed a bill addressing health insurance premium assistance and affordability rules. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[3],
    "Yea. The House passed defense and national-security authorization legislation. Foushee voted to pass that defense authorization legislation, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[4],
    "Nay. The House passed a bill coordinating federal review of natural gas pipeline and LNG projects. Foushee voted against passing that review-coordination bill, matching most Democrats. The bill passed the House.",
  );
  assert.equal(
    summaries[5],
    "Yea. The House voted on a measure changing federal employee collective-bargaining rules. Foushee voted to change those collective-bargaining rules, matching most Democrats. The bill passed the House.",
  );
  assert.match(limitedSummary, /not counted in the summarized vote pattern/);

  const publicCopy = [...summaries, limitedSummary].join(" ");
  assert.doesNotMatch(publicCopy, /This representative|\. matching|stored vote context|for-side|against-side|leans Nay|plus other reviewed measures|Yes-pattern|No-pattern|is corrupt|you should vote/i);
});

test("overview readiness gating limits thin or dominated slices without changing counts", () => {
  const thinRows = [
    row({
      issue_facet: "foreign_military_sales",
      what_happened: "The Senate voted on a foreign military sale.",
      why_it_mattered: "The vote concerned whether to allow or disapprove a specific foreign military sale.",
    }),
    row({
      interpretation_status: "insufficient_evidence",
      issue_facet: "House floor procedure",
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available source text describes floor procedure rather than a clear final policy choice.",
    }),
  ];
  const dominatedRows = [
    row({
      issue_facet: "federal_employee_collective_bargaining",
      what_happened: "The House voted on a measure changing federal employee collective-bargaining rules.",
      why_it_mattered: "The vote concerned whether to change collective-bargaining rules for federal employees.",
    }),
    row({
      issue_facet: "school_foreign_influence_parent_notifications",
      what_happened: "The House passed a bill requiring parent notifications about foreign-influence issues in schools.",
      why_it_mattered: "The vote concerned whether to require parent notifications about foreign-influence issues in schools.",
    }),
    row({
      interpretation_status: "insufficient_evidence",
      issue_facet: "floor_rule_for_multiple_bills",
      support_position: null,
      oppose_position: null,
      uncertainty_note: "This was a floor-rule vote for considering multiple bills.",
    }),
    row({
      interpretation_status: "ambiguous",
      issue_facet: "Defense authorization amendment",
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The amendment source text does not explain the full practical policy effect.",
    }),
    row({
      interpretation_status: "insufficient_evidence",
      issue_facet: "house_of_representatives",
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available official text describes a procedural motion or rule.",
    }),
  ];

  const thinOverview = buildIssueOverview(thinRows, {
    domain: "NATIONAL_SECURITY_FOREIGN",
    representativeName: "Valerie P. Foushee",
  });
  const dominatedOverview = buildIssueOverview(dominatedRows, {
    domain: "EDUCATION_WORKFORCE",
    representativeName: "Valerie P. Foushee",
  });
  const thinRendered = formatRenderedIssueOverview(thinOverview);
  const dominatedRendered = formatRenderedIssueOverview(dominatedOverview);

  assert.equal(thinOverview.readiness.status, "limited");
  assert.deepEqual(thinOverview.readiness.reasons, [
    "too_few_counted_interpreted_yes_no_rows",
    "limited_or_ambiguous_rows_dominate",
  ]);
  assert.equal(thinOverview.votePattern.interpretedYesNoCount, 1);
  assert.equal(thinOverview.votePattern.opposeCount, 1);
  assert.match(thinRendered, /limited interpreted evidence/);
  assert.match(thinRendered, /should not be read as a stable pattern/);
  assert.doesNotMatch(thinRendered, /consistently opposed|consistently supported/);

  assert.equal(dominatedOverview.readiness.status, "limited");
  assert.deepEqual(dominatedOverview.readiness.reasons, [
    "too_few_counted_interpreted_yes_no_rows",
    "limited_or_ambiguous_rows_dominate",
  ]);
  assert.equal(dominatedOverview.votePattern.ambiguousCount, 3);
  assert.match(dominatedRendered, /limited-context rows make up much of this sample/);
  assert.match(dominatedRendered, /not forced into the pattern/);
  assert.doesNotMatch(`${thinRendered} ${dominatedRendered}`, /stored vote context|for-side|against-side|leans Nay|plus other reviewed measures|Yes-pattern|No-pattern|is corrupt|you should vote/i);
});

test("large issue sections keep overview measure groups compact", () => {
  const largeRows = [
    row({
      issue_facet: "fentanyl_scheduling_and_penalties",
      what_happened: "The House passed the HALT Fentanyl Act.",
      why_it_mattered: "The vote concerned fentanyl scheduling and penalty-threshold changes.",
    }),
    row({
      issue_facet: "federal_law_enforcement_equipment",
      what_happened: "The House passed a bill about retired federal law-enforcement service weapons.",
      why_it_mattered: "The vote concerned whether federal law-enforcement officers could buy retired agency-issued firearms.",
    }),
    row({
      issue_facet: "law_enforcement_safety_reporting",
      what_happened: "The House passed a bill requiring DOJ law-enforcement safety reporting.",
      why_it_mattered: "The vote concerned DOJ reporting on law-enforcement officer safety and wellness.",
    }),
    row({
      issue_facet: "dc_police_pursuit_policy",
      what_happened: "The House passed a bill changing D.C. police pursuit rules.",
      why_it_mattered: "The vote concerned whether to change D.C. police pursuit rules.",
    }),
    row({
      issue_facet: "dc_policing_reform_repeal",
      what_happened: "The House passed a bill repealing D.C. policing reforms.",
      why_it_mattered: "The vote concerned whether to repeal D.C.'s 2022 policing and justice reform act.",
    }),
    row({
      issue_facet: "foreign_military_sales",
      what_happened: "The Senate voted on a foreign military sale.",
      why_it_mattered: "The vote concerned whether to allow or disapprove specific foreign military sales.",
    }),
  ];
  const overview = buildIssueOverview(largeRows, {
    domain: "JUSTICE_PUBLIC_SAFETY",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.readiness.status, "safe");
  assert.equal(overview.measureGroups.length, 6);
  assert.equal(overview.overviewMeasureGroups.length, 5);
  assert.match(rendered, /One additional measure group is shown in the evidence below\./);
  assert.doesNotMatch(rendered, /whether to allow or disapprove specific foreign military sales/);
  assert.doesNotMatch(rendered, /plus other reviewed measures|stored vote context|for-side|against-side|leans Nay|Yes-pattern|No-pattern/i);
});

test("scale-readiness facet labels avoid raw public overview leakage", () => {
  const nationalSecurityRows = [
    row({
      description: "National Defense Authorization Act",
      issue_facet: "Defense authorization",
      policy_effect: "Would authorize defense and national-security programs.",
      rollcall_number: 200,
      what_happened: "The House passed defense authorization legislation.",
      why_it_mattered: "The vote concerned annual defense and national-security policy authorization.",
    }),
    row({
      description: "Motion to Commit",
      issue_facet: "Motion to commit",
      policy_effect: "Would use a motion to commit before final disposition.",
      rollcall_number: 201,
      what_happened: "The House considered a procedural motion to commit.",
      why_it_mattered: "The vote concerned whether to send the measure back for further consideration.",
    }),
    row({
      description: "Defense authorization amendment",
      interpretation_status: "insufficient_evidence",
      issue_facet: "Defense authorization amendment",
      rollcall_number: 202,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available source text identifies an amendment but does not explain the full practical policy effect.",
    }),
    row({
      description: "House floor procedure",
      interpretation_status: "insufficient_evidence",
      issue_facet: "House floor procedure",
      rollcall_number: 203,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available source text identifies floor procedure rather than a clear final policy choice.",
    }),
  ];
  const educationRows = [
    row({
      description: "Federal employee collective bargaining",
      issue_facet: "federal_employee_collective_bargaining",
      policy_effect: "Would change collective-bargaining rules for federal employees.",
      rollcall_number: 300,
    }),
    row({
      description: "School foreign funding restrictions",
      issue_facet: "school_foreign_funding_and_contract_restrictions",
      policy_effect: "Would add foreign-funding or contract restrictions for schools.",
      rollcall_number: 301,
    }),
    row({
      description: "School foreign influence parent notifications",
      issue_facet: "school_foreign_influence_parent_notifications",
      policy_effect: "Would require parent notifications about foreign-influence issues in schools.",
      position: "yea",
      rollcall_number: 302,
    }),
    row({
      description: "Floor rule for multiple bills",
      interpretation_status: "insufficient_evidence",
      issue_facet: "floor_rule_for_multiple_bills",
      rollcall_number: 303,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "This was a floor-rule vote for considering multiple bills, not final passage of the underlying policies.",
    }),
  ];
  const environmentRows = [
    row({
      description: "Natural gas pipeline review coordination",
      issue_facet: "natural_gas_pipeline_and_lng_review_coordination",
      policy_effect: "Would coordinate federal review of natural gas pipeline and LNG projects.",
      rollcall_number: 400,
    }),
    row({
      description: "Floor rule for energy and budget measures",
      interpretation_status: "insufficient_evidence",
      issue_facet: "floor_rule_for_energy_and_budget_measures",
      rollcall_number: 401,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "This was a floor-rule vote for considering energy and budget measures, not final passage of the underlying policies.",
    }),
  ];
  const healthRows = [
    row({
      description: "Health insurance premium assistance",
      issue_facet: "health_insurance_premiums",
      policy_effect: "Would change health insurance premium assistance or affordability rules.",
      rollcall_number: 500,
    }),
    row({
      description: "Medicaid payment rules",
      issue_facet: "medicaid_payment_rules_for_minor_health_procedures",
      policy_effect: "Would restrict federal Medicaid payment for specified procedures involving minors.",
      position: "yea",
      rollcall_number: 501,
    }),
    row({
      description: "House rule",
      interpretation_status: "insufficient_evidence",
      issue_facet: "house_of_representatives",
      rollcall_number: 502,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available official text describes a procedural motion or rule rather than a clear final policy choice.",
    }),
  ];

  const cases = [
    ["NATIONAL_SECURITY_FOREIGN", nationalSecurityRows],
    ["EDUCATION_WORKFORCE", educationRows],
    ["ENVIRONMENT_ENERGY", environmentRows],
    ["HEALTH_SOCIAL", healthRows],
  ];

  for (const [domain, rows] of cases) {
    const overview = buildIssueOverview(rows, {
      domain,
      representativeName: "Valerie P. Foushee",
    });
    const rendered = formatRenderedIssueOverview(overview);
    const groupLabels = [...overview.measureGroups, ...overview.ambiguousMeasureGroups].map((group) => group.label).join(" | ");

    assert.doesNotMatch(
      rendered,
      /Defense authorization amendment|House floor procedure|floor_rule_for_multiple_bills|house_of_representatives|floor_rule_for_energy_and_budget_measures|federal_employee_collective_bargaining|school_foreign_funding_and_contract_restrictions|school_foreign_influence_parent_notifications|natural_gas_pipeline_and_lng_review_coordination|health_insurance_premiums|medicaid_payment_rules_for_minor_health_procedures|stored vote context|for-side|against-side|leans Nay|plus other reviewed measures|is corrupt|you should vote/i,
    );
    assert.doesNotMatch(groupLabels, /floor_rule|house_of_representatives|federal_employee_collective_bargaining|school_foreign|natural_gas_pipeline|health_insurance_premiums|medicaid_payment_rules/i);
  }

  const nationalSecurityOverview = buildIssueOverview(nationalSecurityRows, {
    domain: "NATIONAL_SECURITY_FOREIGN",
    representativeName: "Valerie P. Foushee",
  });
  assert.match(
    nationalSecurityOverview.ambiguousMeasureGroups.map((group) => group.label).join(" | "),
    /limited-context defense authorization amendments|procedural House floor action/,
  );

  const educationOverview = buildIssueOverview(educationRows, {
    domain: "EDUCATION_WORKFORCE",
    representativeName: "Valerie P. Foushee",
  });
  assert.match(
    [...educationOverview.measureGroups, ...educationOverview.ambiguousMeasureGroups].map((group) => group.label).join(" | "),
    /procedural floor rule for multiple bills|federal employee collective bargaining|school foreign-funding and contract restrictions|school foreign-influence parent notifications/,
  );
});

test("defense authorization amendment labels reflect interpreted versus limited evidence mix", () => {
  const interpretedAmendment = (rollcall_number) =>
    row({
      description: `Defense authorization amendment ${rollcall_number}`,
      issue_facet: "Defense authorization amendment",
      rollcall_number,
      what_happened: "The House voted on whether to agree to a defense authorization amendment.",
      why_it_mattered: "The vote decided whether that amendment would be adopted, not final passage of the full defense authorization bill.",
      policy_effect: "Would change one amendment provision in defense authorization legislation.",
      vote_context: { ...partyOutcomeContext, final_result: "passed", vote_type: "amendment" },
    });
  const limitedAmendment = (rollcall_number) =>
    row({
      description: `Defense authorization amendment ${rollcall_number}`,
      interpretation_status: "insufficient_evidence",
      issue_facet: "Defense authorization amendment",
      rollcall_number,
      support_position: null,
      oppose_position: null,
      uncertainty_note: "The available source text identifies an amendment but does not explain the full practical policy effect.",
    });

  const mostlyInterpretedOverview = buildIssueOverview(
    [interpretedAmendment(244), interpretedAmendment(245), interpretedAmendment(246), limitedAmendment(247)],
    { domain: "NATIONAL_SECURITY_FOREIGN", representativeName: "Valerie P. Foushee" },
  );
  assert.equal(mostlyInterpretedOverview.measureGroups[0].label, "defense authorization amendments");
  assert.match(formatRenderedIssueOverview(mostlyInterpretedOverview), /The reviewed Yes\/No votes covered defense authorization amendments/);

  const mostlyLimitedOverview = buildIssueOverview(
    [interpretedAmendment(244), limitedAmendment(245), limitedAmendment(246), limitedAmendment(247)],
    { domain: "NATIONAL_SECURITY_FOREIGN", representativeName: "Valerie P. Foushee" },
  );
  assert.equal(mostlyLimitedOverview.measureGroups[0].label, "limited-context defense authorization amendments");
  assert.equal(mostlyLimitedOverview.ambiguousMeasureGroups[0].label, "limited-context defense authorization amendments");

  const mixedOverview = buildIssueOverview(
    [interpretedAmendment(244), limitedAmendment(245)],
    { domain: "NATIONAL_SECURITY_FOREIGN", representativeName: "Valerie P. Foushee" },
  );
  assert.equal(mixedOverview.measureGroups[0].label, "mixed-context defense authorization amendments");
  assert.equal(mixedOverview.ambiguousMeasureGroups[0].label, "mixed-context defense authorization amendments");

  const publicCopy = [
    formatRenderedIssueOverview(mostlyInterpretedOverview),
    formatRenderedIssueOverview(mostlyLimitedOverview),
    formatRenderedIssueOverview(mixedOverview),
  ].join(" ");
  assert.doesNotMatch(publicCopy, /final passage of the full defense authorization bill|for or against national security|you should vote/i);
});

test("curated broad facets improve top-level themes without raw fallback text", () => {
  const rows = [
    row({
      issue_facet: "national_security_foreign",
      rollcall_number: 600,
      what_happened: "This was a direct vote on a national-security measure.",
      why_it_mattered: "The vote is useful because it records a direct position.",
    }),
    row({
      issue_facet: "national_security_foreign",
      rollcall_number: 601,
      what_happened: "The House voted on whether to agree to an amendment.",
      why_it_mattered: "The amendment decreases one account and redirects another.",
    }),
    row({
      issue_facet: "Motion to commit",
      rollcall_number: 602,
      what_happened: "This was a direct vote on a motion to commit.",
      why_it_mattered: "The vote records a direct position on floor procedure.",
    }),
    row({
      issue_facet: "House amendment vote",
      rollcall_number: 603,
      what_happened: "The House voted on whether to agree to an amendment.",
      why_it_mattered: "The amendment redirects funding.",
    }),
  ];
  const overview = buildIssueOverview(rows, {
    domain: "NATIONAL_SECURITY_FOREIGN",
    representativeName: "Valerie P. Foushee",
  });
  const rendered = formatRenderedIssueOverview(overview);

  assert.equal(overview.readiness.status, "safe");
  assert.match(rendered, /national-security and foreign-policy measures/);
  assert.match(rendered, /motions to commit/);
  assert.match(rendered, /other reviewed national-security measures/);
  assert.doesNotMatch(rendered, /national security foreign|other reviewed policy measures|House amendment vote/i);
  assertTopPublicCopyIsSafe(rendered);
});

function row(overrides) {
  return {
    interpretation_status: "interpreted",
    issue_facet: "",
    position: "nay",
    support_position: "yea",
    oppose_position: "nay",
    vote_context: partyOutcomeContext,
    ...overrides,
  };
}

function assertTopPublicCopyIsSafe(copy) {
  assert.doesNotMatch(
    copy,
    /this was a direct vote|the vote is useful because|this vote is useful because|records a direct position|the House voted on whether|the Senate voted on whether|whether to agree to|Amendment No\.|the amendment decreases|the amendment redirects|official roll call|source basis|classification reason/i,
  );
}

function countOccurrences(value, pattern) {
  return String(value || "").split(pattern).length - 1;
}
