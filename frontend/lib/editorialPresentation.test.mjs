import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  getCanonicalActionId,
  getEditorialPresentation,
  indexEditorialPresentations,
  receiptAnchorId,
} from "./editorialPresentation.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));

function payload() {
  return {
    presentations: [
      {
        issue_id: "JUSTICE_PUBLIC_SAFETY",
        tier: "reviewed_conclusion",
        tier_badge: "Reviewed conclusion",
        teaser: "Supplied reviewed teaser.",
        conclusion: {
          headline: "Supplied headline",
          body: "Supplied conclusion.",
        },
      },
    ],
  };
}

test("presentation helpers expose only the API-supplied domain object", () => {
  const input = payload();
  assert.equal(
    getEditorialPresentation(input, "JUSTICE_PUBLIC_SAFETY"),
    input.presentations[0],
  );
  assert.equal(getEditorialPresentation(input, "ECONOMY_TAXES"), null);
  assert.equal(indexEditorialPresentations({ presentations: [{}] }).size, 0);
});

test("raw vote reordering and direction reversal cannot alter supplied conclusion", () => {
  const input = payload();
  const baseline = getEditorialPresentation(input, "JUSTICE_PUBLIC_SAFETY");
  const rawVotes = [
    { position: "nay", roll_call_id: "house:119:1:2" },
    { position: "yea", roll_call_id: "house:119:1:1" },
  ].reverse();
  for (const row of rawVotes) {
    row.position = row.position === "yea" ? "nay" : "yea";
  }
  assert.deepEqual(
    getEditorialPresentation(input, "JUSTICE_PUBLIC_SAFETY"),
    baseline,
  );
});

test("canonical action IDs map to stable receipt anchors", () => {
  const row = { roll_call_id: "house:119:1:32" };
  assert.equal(getCanonicalActionId(row), "house:119:1:32");
  assert.equal(
    receiptAnchorId(getCanonicalActionId(row)),
    "vote-receipt-house-119-1-32",
  );
  assert.equal(getCanonicalActionId({ roll_call_id: "opaque-row" }), null);
});

test("frontend presentation helper contains no analytical inference inputs", () => {
  const source = fs.readFileSync(
    path.join(here, "editorialPresentation.mjs"),
    "utf8",
  );
  for (const forbidden of [
    "yea_count",
    "nay_count",
    "interpreted_support_count",
    "interpreted_oppose_count",
    "member_party",
    "keywords",
  ]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});
