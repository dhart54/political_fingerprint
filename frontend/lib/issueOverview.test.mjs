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
    "tax, spending, deficit, and debt-limit legislation",
    "SBA 7\\(a\\) and 504 loan eligibility",
    "citizenship or lawful-residency status",
    "military construction",
    "military housing",
    "veterans benefits",
    "Veterans Affairs",
    "temporary government funding",
    "shutdown-ending",
    "not-voting row",
    "ambiguous or limited-context rows",
  ]) {
    assert.match(rendered, new RegExp(expected, "i"));
  }

  assert.match(rendered, /In this reviewed sample, Foushee mostly opposed fiscal, funding, and small-business measures: 6 opposed and 0 supported across 6 interpreted Yes\/No votes\./);
  assert.match(rendered, /If you favored these reviewed measures — including a budget framework for later tax, spending, deficit, and debt-limit legislation/);
  assert.match(rendered, /All of those votes matched most Democrats\./);
  assert.ok(
    rendered.indexOf("If you favored these reviewed measures — including") <
      rendered.indexOf("How to read this"),
    "concrete policy-substance voter read should appear before broad scope limits",
  );
  assert.doesNotMatch(rendered, /If you generally favored these House Republican/);
  assert.match(rendered, /^Finding\nIn this reviewed sample, Foushee mostly opposed/m);
  assert.match(rendered, /How to read this\nThis read is based on the reviewed votes shown here/);
  assert.doesNotMatch(rendered, /The vote record alone does not show her motive/);
  assert.doesNotMatch(rendered, /stored vote context|for-side|against-side|reviewed yes\/no|plus other reviewed measures|leans Nay|is corrupt|character judgment|you should vote|support this candidate|oppose this candidate/i);
});

test("Valerie Foushee Economy & Taxes overview text remains approved copy", () => {
  const overview = buildIssueOverview(valerieEconomyRows, {
    domain: "ECONOMY_TAXES",
    representativeName: "Valerie P. Foushee",
  });

  assert.equal(formatRenderedIssueOverview(overview), `Finding
In this reviewed sample, Foushee mostly opposed fiscal, funding, and small-business measures: 6 opposed and 0 supported across 6 interpreted Yes/No votes. These reviewed measures included a budget framework for later tax, spending, deficit, and debt-limit legislation, restrictions on SBA loan eligibility tied to citizenship or lawful-residency status, military construction and Veterans Affairs funding, temporary government funding, and a shutdown-ending funding package. All of those votes matched most Democrats. All were against the final House outcome. Start with the representative votes below to inspect the record behind this read.

What these votes were about
In this Economy & Taxes sample, the reviewed votes where Foushee cast a Yes or No covered several concrete fiscal questions: whether to advance a budget framework for later tax, spending, deficit, and debt-limit legislation; whether to restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-residency status; whether to fund military construction, military housing, veterans benefits, and Veterans Affairs programs; whether to keep federal agencies operating through temporary government funding; and whether to accept a shutdown-ending funding package. A separate not-voting row concerned an SBA regulatory-cost cap bill, but Foushee was recorded as not voting, so it is explained below and not counted as support or opposition. Two ambiguous or limited-context rows remain visible for an appropriations amendment and a conference instruction, but they are not used to summarize the vote pattern.

How a voter might read that
If you favored these reviewed measures — including a budget framework for later tax, spending, deficit, and debt-limit legislation, restrictions on SBA loan eligibility tied to citizenship or lawful-residency status, military construction and Veterans Affairs funding, temporary government funding, and a shutdown-ending funding package — Foushee's votes were mostly opposed. If you opposed those measures or objected to their terms, this record was mostly aligned with that view.

How to read this
This read is based on the reviewed votes shown here. Vote records show actions, not motive, ideology, character, corruption, or a voting recommendation. The rows show recorded votes and reviewed bill meaning for this sample, not her full fiscal record. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.`);
});

test("evidence card disclosure keeps public summary visible and audit details collapsed", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  const cardStart = source.indexOf("<InterpretationBreakdown");
  const sourceButtonStart = source.indexOf("{row.source_url ?", cardStart);
  const cardEnd = source.indexOf("</div>", sourceButtonStart);
  const breakdownStart = source.indexOf("function InterpretationBreakdown");
  const breakdownEnd = source.indexOf("function SourceBasisList", breakdownStart);
  const breakdownSource = source.slice(breakdownStart, breakdownEnd);
  const detailsStart = breakdownSource.indexOf("<details");
  const detailsEnd = breakdownSource.indexOf("</details>", detailsStart);
  const sourceBasisStart = breakdownSource.indexOf("<SourceBasisList sourceBasis={row.source_basis} />");
  const eligibilityStart = breakdownSource.indexOf("Included as {formatClassificationReason(row.classification_reason)}");
  const officialVoteRecordStart = breakdownSource.indexOf("Official Vote Record");
  const voteSummaryStart = breakdownSource.indexOf('label="Vote summary"');
  const whyThisMatteredStart = breakdownSource.indexOf('label="Why this mattered"');

  assert.ok(voteSummaryStart > 0, "vote summary must be rendered by the card");
  assert.ok(whyThisMatteredStart > voteSummaryStart, "why-it-mattered should follow the vote summary");
  assert.ok(detailsStart > whyThisMatteredStart, "details should come after the public summary layer");
  assert.ok(sourceButtonStart > cardStart && sourceButtonStart < cardEnd, "source link should stay in the default-visible card layer");
  assert.ok(sourceBasisStart > detailsStart && sourceBasisStart < detailsEnd, "source basis should stay inside details");
  assert.ok(eligibilityStart > detailsStart && eligibilityStart < detailsEnd, "eligibility/methodology note should stay inside details");
  assert.ok(officialVoteRecordStart > detailsStart && officialVoteRecordStart < detailsEnd, "official vote record action should stay inside details");
});

test("approved Valerie Economy vote summaries and limited-row caveats remain unchanged", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");

  for (const expected of [
    "Nay. The House adopted a budget blueprint that helped start a fast-track reconciliation process for later tax, spending, deficit, and debt-limit legislation. Foushee voted against adopting that framework, matching most Democrats. The measure passed narrowly.",
    "Nay. The House agreed to the Senate-amended budget framework, keeping the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation. Foushee voted against agreeing to that framework, matching most Democrats. The measure passed narrowly.",
    "Nay. The House passed a bill that would restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-permanent-residency status. Foushee voted against adding those eligibility restrictions, matching most Democrats. The bill passed the House.",
    "Nay. The House passed an FY2026 funding bill for military construction, military housing, veterans benefits, Veterans Affairs programs, and related agencies. Foushee voted against passing that funding bill, matching most Democrats. The measure passed the House.",
    "Nay. The House passed a temporary funding bill to keep most federal agencies operating while regular appropriations bills were unfinished. Foushee voted against passing that temporary funding bill, matching most Democrats. The measure passed narrowly.",
    "Nay. The House agreed to a Senate-amended funding package that ended the 2025 shutdown and sent the measure to the President. Foushee voted against accepting that shutdown-ending package, matching most Democrats. The measure passed and became law.",
    "Not Voting. The House passed a bill that would require the Small Business Administration to keep its annual small-business regulatory budget at zero or below. Foushee was recorded as not voting, so this row explains the bill's meaning but does not count as support or opposition. The bill passed the House.",
    "Limited-context row. This was an en bloc appropriations amendment, but the available source text does not explain the full practical change. It remains visible below but is not counted in the summarized vote pattern.",
    "Limited-context row. This was a motion to instruct conferees, not final passage of the underlying appropriations bill. It remains visible below but is not counted in the summarized vote pattern.",
  ]) {
    assert.ok(source.includes(expected), `expected approved copy to remain: ${expected}`);
  }

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
  assert.match(rendered, /public-safety and legal-policy questions/);
  assert.match(rendered, /whether to permanently schedule fentanyl-related substances/);
  assert.match(rendered, /whether to create a program for federal law-enforcement officers to buy retired agency-issued firearms/);
  assert.match(rendered, /whether to require DOJ reporting on targeted attacks against law-enforcement officers/);
  assert.match(rendered, /whether to change D\.C\. police pursuit rules/);
  assert.match(rendered, /whether to repeal D\.C\.'s 2022 policing and justice reform act/);
  assert.match(rendered, /mostly opposed public-safety and legal-policy measures: 4 opposed and 1 supported across 5 interpreted Yes\/No votes/);
  assert.match(rendered, /If you favored these reviewed measures — including fentanyl scheduling and penalty-threshold legislation/);
  assert.match(rendered, /Most opposed measures that passed the House\./);
  assert.match(rendered, /Two additional rows remain visible below, including one procedural-context row and one other limited-context row; they are not used to summarize support, opposition, or alignment\./);
  assert.doesNotMatch(rendered, /If you generally favored these House Republican measures|not as a simple statement that she is broadly for or against this issue area/);
  assert.doesNotMatch(rendered, /concrete fiscal questions|for" or "against taxes|full fiscal record|JUSTICE PUBLIC SAFETY|administrative law and regulatory procedures|house of representatives|Yes-pattern|No-pattern/);
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
  assert.match(rendered, /interpreted Yes\/No votes were split across public-safety and legal-policy measures: 2 opposed and 2 supported across 4 interpreted Yes\/No votes/);
  assert.match(rendered, /If your view depends on the specific terms of these reviewed measures — including fentanyl scheduling and penalty-threshold legislation/);
  assert.match(rendered, /this record is split rather than mostly support or mostly opposition/);
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
  assert.match(formatRenderedIssueOverview(mostlyInterpretedOverview), /whether to adopt amendments to defense authorization legislation/);

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
