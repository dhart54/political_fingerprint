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

  assert.ok(source.includes("Record Summary"), "profile should provide one top-level record summary");
  assert.ok(source.includes("narrative.patternRows"), "reviewed issue patterns should appear inside the top-level summary");
  assert.ok(source.includes("Open Best Read"), "quick read should provide a direct path to the strongest issue read");
  assert.ok(source.includes("Best place to start"), "strong issue cards should be visually prioritized");
  assert.ok(source.includes("Lower priority: read cautiously"), "limited issue cards should be lower priority");
  assert.ok(source.includes("Evidence groups"), "grouped evidence preview should be user-visible");
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

test("representative page flow directs the voter without changing evidence logic", () => {
  const source = [
    readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8"),
    readFileSync(new URL("../components/ProfileQuickRead.js", import.meta.url), "utf8"),
  ].join("\n");

  assert.match(source, /clearest reviewed issue read/);
  assert.match(source, /Record Summary/);
  assert.match(source, /limited issue sections are intentionally lower priority/);
  assert.match(source, /Jump to issue/);
  assert.match(source, /without being forced into a confident pattern/);
  assert.match(source, /Context rows remain visible but do not drive support\/opposition summaries/);
  assert.doesNotMatch(source, /stored vote context|for-side|against-side|leans Nay|plus other reviewed measures|Yes-pattern|No-pattern/);
});

test("quick read separates high-volume issue focus from clearest reviewed issue read", () => {
  const source = readFileSync(new URL("../components/ProfileQuickRead.js", import.meta.url), "utf8");

  assert.match(source, /topFocus\.domain !== topPosition\.domain/);
  assert.match(source, /It has the clearest reviewed vote meaning in this profile/);
  assert.match(source, /has more recorded votes but is not the best first read/);
  assert.match(source, /the clearest evidence is elsewhere/);
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
  assert.match(source, /I generally favored these measures/);
  assert.match(source, /My views differ by measure/);
  assert.match(source, /getDirectionalAlignmentPreferences/);
  assert.match(source, /concrete for-or-against reviewed-measure choices/);
  assert.doesNotMatch(source, /Your Issues vs This Record|Pick what you want this record checked against|Record shown|record check/);
});

test("issue cards use generalized readiness copy and contact follows vote cards", () => {
  const source = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  const civicActionIndex = source.indexOf("<EvidenceUtilityPanel");
  const billGroupIndex = source.indexOf("{billGroups.map");

  assert.match(source, /reviewed Yes\/No .* out of .* recorded/);
  assert.match(source, /Best place to start\./);
  assert.match(source, /Useful comparison read\./);
  assert.match(source, /Read cautiously\./);
  assert.match(source, /not ready for a confident summary/);
  assert.ok(billGroupIndex > 0 && civicActionIndex > billGroupIndex, "utility panel should render after vote cards");
});

test("secondary profile tools are consolidated below the evidence path", () => {
  const source = readFileSync(new URL("../app/page.js", import.meta.url), "utf8");

  assert.match(source, /Tools: preferences, comparison, and switching officials/);
  assert.match(source, /Search or switch official/);
  assert.match(source, /Procedural votes may appear as context/);
  assert.doesNotMatch(source, /Procedural votes are excluded before issue reads/);
});
