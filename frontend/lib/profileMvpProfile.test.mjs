import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("evidence panel exposes grouped preview and confidence labels without changing card source access", () => {
  const source = [
    readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8"),
    readFileSync(new URL("../components/ProfileQuickRead.js", import.meta.url), "utf8"),
  ].join("\n");
  const groupingPreviewStart = source.indexOf("function EvidenceGroupingPreview");
  const interpretationBreakdownStart = source.indexOf("function InterpretationBreakdown");
  const voteRowStart = source.indexOf("function VoteEvidenceRow");
  const sourceButtonStart = source.indexOf("{row.source_url ?", voteRowStart);
  const detailsStart = source.indexOf("<details", voteRowStart);

  assert.ok(source.includes("Record Coverage"), "profile should provide one neutral record coverage summary");
  assert.ok(source.includes("Open vote evidence"), "profile issue links should open source-backed vote evidence");
  assert.ok(source.includes("Available actions"), "profile should expose descriptive evidence counts");
  assert.ok(source.includes("BasicIssueList"), "the issue evidence surface should use neutral navigation");
  assert.ok(source.includes("without combining them into a broader issue conclusion"), "the basic fallback should state its semantic limit");
  assert.ok(source.includes("Evidence group overview"), "grouped evidence preview should be user-visible as a secondary overview");
  assert.ok(source.includes("formatCompactEvidenceGroupingOverview"), "compact grouping summary should be rendered");
  assert.ok(source.includes("IssueNavigation"), "large profiles should expose compact issue navigation");
  assert.ok(source.includes("Reviewed meaning"), "interpreted rows should get a confidence label");
  assert.ok(source.includes("Procedural context"), "procedural rows should get a confidence label");
  assert.ok(source.includes("Limited context"), "ambiguous rows should get a confidence label");
  assert.ok(source.includes("Needs source support"), "insufficient rows should get a confidence label");
  assert.ok(source.includes("Not counted"), "not-voting rows should get a confidence label");
  assert.ok(groupingPreviewStart > 0 && groupingPreviewStart < interpretationBreakdownStart, "grouped preview should be defined before card detail helpers");
  assert.ok(source.includes("Source, caveats, and full context"), "source and caveats should move into expandable detail");
  assert.ok(detailsStart > 0 && sourceButtonStart > detailsStart, "source link should be available inside expanded details");
  assert.doesNotMatch(source, /you should vote|support this candidate|oppose this candidate|is corrupt|bought|radical|extreme|worst/i);
});

test("grouped preview copy preserves limited and not-voting caveats", () => {
  const source = [
    readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8"),
    readFileSync(new URL("./evidenceGrouping.mjs", import.meta.url), "utf8"),
  ].join("\n");

  assert.match(source, /limited/);
  assert.match(source, /procedural context/);
  assert.match(source, /not voting/);
  assert.match(source, /Context rows remain visible but do not drive support\/opposition summaries/);
  assert.match(source, /should not be treated as final policy votes/);
});

test("representative page flow exposes neutral coverage without changing evidence logic", () => {
  const source = [
    readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8"),
    readFileSync(new URL("../components/ProfileQuickRead.js", import.meta.url), "utf8"),
  ].join("\n");

  assert.match(source, /Record Coverage/);
  assert.match(source, /Available actions/);
  assert.match(source, /Recorded action composition/);
  assert.match(source, /Best-covered issue/);
  assert.match(source, /getDomainDescription/);
  assert.match(source, /orderIssueRowsByEvidenceUsefulness/);
  assert.match(source, /These counts do not combine the actions into an analytical conclusion/);
  assert.doesNotMatch(source, /Open Best Read|Strongest evidence|strongest issue|Record read|clearest reviewed issue read/);
  assert.doesNotMatch(source, /QuickMetric eyebrow="Change"|Steady mix|Issue mix changed|fetchDrift/);
  assert.match(source, /Jump to issue/);
  assert.match(source, /without combining them into a broader issue conclusion/);
  assert.match(source, /Open another issue to inspect its available vote receipts/);
  assert.match(source, /Context rows remain visible but do not drive support\/opposition summaries/);
  assert.doesNotMatch(source, /stored vote context|for-side|against-side|leans Nay|plus other reviewed measures|Yes-pattern|No-pattern/);
});

test("quick read ranks coverage without synthesizing an analytical issue read", () => {
  const source = readFileSync(new URL("../components/ProfileQuickRead.js", import.meta.url), "utf8");

  assert.match(source, /hasAvailableIssueEvidence/);
  assert.match(source, /orderIssueRowsByEvidenceUsefulness/);
  assert.match(source, /Best-covered issue/);
  assert.match(source, /Open vote evidence/);
  assert.doesNotMatch(source, /buildRecordNarrative|getBestIssueRead|fillMissingInterpretedCounts|mostly supported|mostly opposed|patternRows/);
});

test("no-preference record views avoid alignment framing in neutral summaries", () => {
  const source = [
    readFileSync(new URL("../components/AlignmentPanel.js", import.meta.url), "utf8"),
    readFileSync(new URL("../components/ComparisonPanel.js", import.meta.url), "utf8"),
    readFileSync(new URL("../components/IssuePreferencePanel.js", import.meta.url), "utf8"),
    readFileSync(new URL("./profileNarrative.mjs", import.meta.url), "utf8"),
  ].join("\n");

  assert.match(source, /Selected Issue Records/);
  assert.match(source, /Compare the record to concrete choices/);
  assert.match(source, /Switch Comparison Pair/);
  assert.match(source, /I generally favored these measures/);
  assert.match(source, /My views differ by measure/);
  assert.match(source, /getDirectionalAlignmentPreferences/);
  assert.match(source, /concrete for-or-against reviewed-measure choices/);
  assert.doesNotMatch(source, /Your Issues vs This Record|Pick what you want this record checked against|Record shown|record check|Change Comparison Pair/);
});

test("basic issue navigation avoids readiness conclusions and contact follows vote cards", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  const civicActionIndex = source.indexOf("<EvidenceUtilityPanel");
  const reviewedVoteListIndex = source.indexOf("<ReviewedVoteList");

  assert.match(source, /function BasicIssueList/);
  assert.match(source, /getEvidenceCoverageLabel\(row\)/);
  assert.match(source, /getDomainDescription\(row\.domain\)/);
  assert.match(source, /without combining them into a broader issue conclusion/);
  assert.doesNotMatch(source, /buildIssueCardPreview|formatIssueCardStatusLabel|IssueReadinessTile/);
  assert.ok(reviewedVoteListIndex > 0 && civicActionIndex > reviewedVoteListIndex, "utility panel should render after reviewed vote list access");
});

test("show votes proof view starts bounded and keeps the full receipt list available", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  const readyViewStart = source.indexOf('{evidenceState.status === "ready" && isSelected && evidenceRows.length > 0 ? (');
  const readyViewEnd = source.indexOf("function RepresentativeVotesSection", readyViewStart);
  const readyViewSource = source.slice(readyViewStart, readyViewEnd);
  const summaryRenderStart = readyViewSource.indexOf("<IssueEvidenceSummary");
  const representativeRenderStart = readyViewSource.indexOf("<RepresentativeVotesSection");
  const fullListRenderStart = readyViewSource.indexOf("<ReviewedVoteList");
  const groupingRenderStart = readyViewSource.indexOf("<EvidenceGroupingPreview");
  const utilityRenderStart = readyViewSource.indexOf("<EvidenceUtilityPanel");
  const representativeStart = source.indexOf("function RepresentativeVotesSection");
  const fullListStart = source.indexOf("function ReviewedVoteList");
  const billGroupStart = source.indexOf("function BillEvidenceGroup");
  const voteRowStart = source.indexOf("function VoteEvidenceRow");
  const sourceDrawerStart = source.indexOf("Source, caveats, and full context", voteRowStart);

  assert.match(source, /const REPRESENTATIVE_VOTE_LIMIT = 8/);
  assert.match(source, /Representative votes/);
  assert.match(source, /A first set of votes behind this read/);
  assert.match(source, /Show all reviewed votes/);
  assert.match(source, /Full reviewed vote list/);
  assert.match(source, /Evidence group overview/);
  assert.match(source, /showAllVotes \?/);
  assert.match(source, /buildProofView/);
  assert.match(source, /countable Yes\/No votes/);
  assert.ok(summaryRenderStart >= 0 && summaryRenderStart < representativeRenderStart, "issue summary should render before representative votes");
  assert.ok(representativeRenderStart > 0 && representativeRenderStart < fullListRenderStart, "representative votes should render before full reviewed list");
  assert.ok(fullListRenderStart > 0 && fullListRenderStart < groupingRenderStart, "full reviewed list should render before evidence group overview");
  assert.ok(groupingRenderStart > 0 && groupingRenderStart < utilityRenderStart, "evidence group overview should stay secondary to receipts and before tools");
  assert.ok(representativeStart > 0 && representativeStart < fullListStart, "representative votes should be defined before full list");
  assert.ok(fullListStart > 0 && fullListStart < billGroupStart, "full list wrapper should gate grouped bill cards");
  assert.ok(billGroupStart > 0 && billGroupStart < voteRowStart, "bill groups should reuse vote rows");
  assert.ok(sourceDrawerStart > voteRowStart, "vote-level source and caveat drawers should remain inside vote rows");
});

test("secondary profile tools are consolidated below the evidence path", () => {
  const source = readFileSync(new URL("../app/page.js", import.meta.url), "utf8");

  assert.match(source, /Tools: preferences, comparison, and switching officials/);
  assert.match(source, /Search or switch official/);
  assert.match(source, /Procedural votes may appear as context/);
  assert.doesNotMatch(source, /Procedural votes are excluded before issue reads/);
});

test("first-render profile shell avoids stale fallback metrics and labels sample state", () => {
  const source = readFileSync(new URL("../app/page.js", import.meta.url), "utf8");

  assert.match(source, /Reviewed vote evidence with source receipts loads from the live coverage record/);
  assert.match(source, /Sample profile shown until you search your ZIP/);
  assert.match(source, /Sample profile/);
  assert.match(source, /handleSelectLegislator/);
  assert.doesNotMatch(source, /formatNumber\(coverageMetadata\?\.legislator_count, "548"\)/);
  assert.doesNotMatch(source, /formatNumber\(coverageMetadata\?\.eligible_roll_call_count, "8"\)/);
  assert.doesNotMatch(source, /formatPercent\(coverageMetadata\?\.source_url_share\)/);
  assert.doesNotMatch(source, /QuickMetric eyebrow="Best read"|QuickMetric eyebrow="Change"|Steady mix/);
});
