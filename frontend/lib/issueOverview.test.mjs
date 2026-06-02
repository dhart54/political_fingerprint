import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { buildIssueOverview, formatRenderedIssueOverview } from "./issueOverview.mjs";

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

  assert.match(rendered, /If you generally favored these House Republican packages/);
  assert.match(rendered, /The vote record alone does not show her motive/);
  assert.doesNotMatch(rendered, /stored vote context|for-side|against-side|reviewed yes\/no|plus other reviewed measures|leans Nay|is corrupt|character judgment|you should vote|support this candidate|oppose this candidate/i);
});

test("Valerie Foushee Economy & Taxes overview text remains approved copy", () => {
  const overview = buildIssueOverview(valerieEconomyRows, {
    domain: "ECONOMY_TAXES",
    representativeName: "Valerie P. Foushee",
  });

  assert.equal(formatRenderedIssueOverview(overview), `What these votes were about
In this Economy & Taxes sample, the reviewed votes where Foushee cast a Yes or No covered several concrete fiscal questions: whether to advance a budget framework for later tax, spending, deficit, and debt-limit legislation; whether to restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-residency status; whether to fund military construction, military housing, veterans benefits, and Veterans Affairs programs; whether to keep federal agencies operating through temporary government funding; and whether to accept a shutdown-ending funding package. A separate not-voting row concerned an SBA regulatory-cost cap bill, but Foushee was recorded as not voting, so it is explained below and not counted as support or opposition. Two ambiguous or limited-context rows remain visible for an appropriations amendment and a conference instruction, but they are not used to summarize the vote pattern.

What Foushee did
Foushee voted No on all 6 reviewed votes where she cast a Yes or No. Each of those votes matched most House Democrats, and each was against the final House outcome.

What pattern that creates
Foushee consistently opposed the House Republican fiscal, funding, and small-business measures reviewed in this sample. Her record here is best read as opposition to this specific set of Republican-led House measures, not as a simple statement that she is "for" or "against taxes."

How a voter might read that
If you generally favored these House Republican packages, this section may look misaligned with your views. If you generally wanted Democrats to oppose those packages or objected to their terms, this section may look aligned. The vote record alone does not show her motive.

What not to infer
Do not infer motive, ideology, character, corruption, or a voting recommendation from this section. The rows show recorded votes and reviewed bill meaning for this sample, not her full fiscal record. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.`);
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
