import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  actionReceiptId,
  buildIssueOverviewRows,
  buildPassAUrl,
  canonicalActionId,
  chronologicalActions,
  filterActions,
  isPublicAnalysisAvailable,
  parsePassARouteState,
  resolveExactActionRequest,
  sortAndFilterIssues,
} from "./frontendPassA.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));

function presentation(claim = "reviewed_sample_finding") {
  return {
    tier: "reviewed_conclusion",
    public_status_label: "Reviewed benchmark sample",
    review_state: {
      public_claim_class: claim,
    },
  };
}

function rows() {
  return [
    {
      domain: "ECONOMY_TAXES",
      yea_count: 8,
      nay_count: 2,
      other_count: 1,
      total_votes: 11,
      interpreted_support_count: 5,
      interpreted_oppose_count: 3,
      party: "R",
    },
    {
      domain: "JUSTICE_PUBLIC_SAFETY",
      yea_count: 3,
      nay_count: 4,
      other_count: 0,
      total_votes: 7,
      interpreted_support_count: 3,
      interpreted_oppose_count: 4,
      party: "D",
    },
  ];
}

test("representative, issue, and scope persist through route-ready URL state", () => {
  const url = buildPassAUrl("https://example.test/", {
    legislatorId: "leg_valerie_p_foushee",
    issue: "JUSTICE_PUBLIC_SAFETY",
    scope: "119",
  });
  assert.equal(
    url,
    "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY&scope=119",
  );
  assert.deepEqual(parsePassARouteState(url.split("?")[1]), {
    legislatorId: "leg_valerie_p_foushee",
    issue: "JUSTICE_PUBLIC_SAFETY",
    scope: "119",
  });
  assert.equal(
    buildPassAUrl(`https://example.test${url}`, {
      legislatorId: null,
      issue: null,
      scope: "all",
    }),
    "/",
  );
});

test("recommended prioritizes valid supplied analysis, not direction or party", () => {
  const presentations = new Map([
    ["JUSTICE_PUBLIC_SAFETY", presentation()],
  ]);
  const baseline = sortAndFilterIssues(
    buildIssueOverviewRows({
      rows: rows(),
      presentations,
      stableDomainOrder: ["ECONOMY_TAXES", "JUSTICE_PUBLIC_SAFETY"],
    }),
    "recommended",
  );
  const reversed = rows().map((row) => ({
    ...row,
    party: row.party === "D" ? "R" : "D",
    yea_count: row.nay_count,
    nay_count: row.yea_count,
    interpreted_support_count: row.interpreted_oppose_count,
    interpreted_oppose_count: row.interpreted_support_count,
  }));
  const changed = sortAndFilterIssues(
    buildIssueOverviewRows({
      rows: reversed,
      presentations,
      stableDomainOrder: ["ECONOMY_TAXES", "JUSTICE_PUBLIC_SAFETY"],
    }),
    "recommended",
  );
  assert.deepEqual(
    baseline.map((row) => row.domain),
    ["JUSTICE_PUBLIC_SAFETY", "ECONOMY_TAXES"],
  );
  assert.deepEqual(
    changed.map((row) => row.domain),
    baseline.map((row) => row.domain),
  );
});

test("most evidence, reviewed analysis, and A-Z use their closed rules", () => {
  const overview = buildIssueOverviewRows({
    rows: rows(),
    presentations: new Map([["JUSTICE_PUBLIC_SAFETY", presentation()]]),
    stableDomainOrder: ["ECONOMY_TAXES", "JUSTICE_PUBLIC_SAFETY"],
  });
  assert.deepEqual(
    sortAndFilterIssues(overview, "most_evidence").map((row) => row.domain),
    ["ECONOMY_TAXES", "JUSTICE_PUBLIC_SAFETY"],
  );
  assert.deepEqual(
    sortAndFilterIssues(overview, "reviewed_analysis").map((row) => row.domain),
    ["JUSTICE_PUBLIC_SAFETY"],
  );
  assert.deepEqual(
    sortAndFilterIssues(overview, "a_z").map((row) => row.domain),
    ["ECONOMY_TAXES", "JUSTICE_PUBLIC_SAFETY"],
  );
});

test("analysis availability requires backend review state and a public claim", () => {
  assert.equal(isPublicAnalysisAvailable(presentation()), true);
  assert.equal(
    isPublicAnalysisAvailable({
      ...presentation(),
      tier: "receipts_only",
    }),
    false,
  );
  assert.equal(
    isPublicAnalysisAvailable({
      tier: "reviewed_conclusion",
      public_status_label: "Reviewed benchmark sample",
      review_state: null,
    }),
    false,
  );
});

test("ledger orders newest first and applies non-analytical filters", () => {
  const actions = [
    {
      roll_call_id: "house:119:1:1",
      vote_date: "2025-01-01",
      position: "yea",
      interpretation_status: "interpreted",
      classification_reason: "policy_vote",
    },
    {
      roll_call_id: "house:119:1:3",
      vote_date: "2025-03-01",
      position: "not_voting",
      interpretation_status: "interpreted",
      classification_reason: "policy_vote",
    },
    {
      roll_call_id: "house:119:1:2",
      vote_date: "2025-02-01",
      position: "nay",
      interpretation_status: "ambiguous",
      classification_reason: "procedural_vote",
      vote_type: "procedural",
    },
  ];
  const ordered = chronologicalActions(actions);
  assert.deepEqual(
    ordered.map((row) => row.roll_call_id),
    ["house:119:1:3", "house:119:1:2", "house:119:1:1"],
  );
  assert.deepEqual(
    filterActions(ordered, "non_directional").map((row) => row.roll_call_id),
    ["house:119:1:3"],
  );
  assert.deepEqual(
    filterActions(ordered, "substantive").map((row) => row.roll_call_id),
    ["house:119:1:1"],
  );
  assert.deepEqual(
    filterActions(ordered, "highlighted", ["house:119:1:2"]).map(
      (row) => row.roll_call_id,
    ),
    ["house:119:1:2"],
  );
  assert.equal(
    actionReceiptId(actions[0]),
    "action-receipt-house-119-1-1",
  );
});

test("live evidence rows derive canonical IDs for reviewed-finding links", () => {
  const liveShapedRows = [
    {
      chamber: "house",
      congress: 119,
      roll_call_id: "1635",
      rollcall_number: 131,
      vote_date: "2025-05-15 00:00:00+00:00",
    },
    {
      chamber: "house",
      congress: 119,
      roll_call_id: "2450",
      rollcall_number: 55,
      vote_date: "2026-02-04 00:00:00+00:00",
    },
  ];
  assert.deepEqual(
    liveShapedRows.map(canonicalActionId),
    ["house:119:1:131", "house:119:2:55"],
  );
  assert.deepEqual(
    filterActions(liveShapedRows, "highlighted", ["house:119:1:131"]),
    [liveShapedRows[0]],
  );
  assert.equal(
    actionReceiptId(liveShapedRows[0]),
    "action-receipt-house-119-1-131",
  );
});

test("exact-action resolution safely preserves the complete ledger for zero matches", () => {
  const actionRows = exactActionRows();
  const resolution = resolveExactActionRequest(
    actionRows,
    ["house:119:1:999"],
  );
  assert.equal(resolution.filter, "all");
  assert.deepEqual(resolution.highlightedIds, []);
  assert.equal(resolution.expandedId, null);
  assert.deepEqual(resolution.matchingRows, []);
  assert.match(resolution.notice, /complete chronological record remains available/);
});

for (const count of [1, 2, 3]) {
  test(`exact-action resolution exposes and opens ${count} matched action${count === 1 ? "" : "s"}`, () => {
    const actionRows = exactActionRows();
    const requested = actionRows.slice(0, count).map(canonicalActionId);
    const resolution = resolveExactActionRequest(actionRows, requested);
    assert.equal(resolution.filter, "highlighted");
    assert.equal(resolution.matchingRows.length, count);
    assert.equal(resolution.highlightedIds.length, count);
    assert.equal(
      resolution.expandedId,
      canonicalActionId(resolution.matchingRows[0]),
    );
    assert.equal(resolution.notice, "");
  });
}

function exactActionRows() {
  return [32, 33, 166].map((rollcall_number) => ({
    chamber: "house",
    congress: 119,
    roll_call_id: `house:119:1:${rollcall_number}`,
    rollcall_number,
    vote_date: rollcall_number === 166 ? "2025-06-12" : "2025-02-06",
  }));
}

test("primary Pass A journey contains no representative profile image", () => {
  for (const relative of [
    "../app/page.js",
    "../components/RepresentativeFinder.js",
    "../components/RepresentativeHeader.js",
    "../components/RepresentativeExperience.js",
  ]) {
    const source = fs.readFileSync(path.join(here, relative), "utf8");
    assert.equal(/<Image|<img/i.test(source), false, relative);
  }
});

test("reviewed-analysis rendering uses supplied finding direction", () => {
  const source = fs.readFileSync(
    path.join(here, "../components/ReviewedAnalysisSection.js"),
    "utf8",
  );
  assert.match(source, /item\.direction === "support"/);
  assert.match(source, /item\.direction === "opposition"/);
  for (const forbidden of ["yea_count", "nay_count", "member_party", "keywords"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});
