import assert from "node:assert/strict";
import test from "node:test";

import { buildPublicReceipt } from "./publicReceipt.mjs";

test("public receipt projection exposes voter content and excludes governance metadata", () => {
  const receipt = buildPublicReceipt({
    position: "nay",
    uncertainty_note: "Legacy fallback should not override governed caveats.",
    episode_relationship: "This amendment was one step in the bill's legislative path.",
    governed_receipt_projection: {
      exact_action_meaning: "The amendment would preserve the listed exception.",
      policy_question: "Whether to preserve the listed exception.",
      member_action: "Nay",
      episode_id: "internal-policy-episode-id",
      canonical_action_id: "house:119:1:32",
      action_interpretation_id: "action-interpretation:house:119:1:32:v1",
      action_interpretation_sha256: "a".repeat(64),
      implementation_id: "m10r1-implementation",
      milestone_name: "M10R1 launch",
      reviewed_at: "2026-08-04",
      interpretation_receipt_refs: [
        "docs/semantic_ir/accepted/acceptance_receipt.json",
        "user_launch_ratification_receipt.json",
      ],
      caveats: [
        "The exception applies only to the listed institutions.",
        "Human-reviewed on 2026-08-04.",
        "This receipt remains bounded to the reviewed benchmark sample.",
        "Review candidate accepted in the launch ratification milestone.",
      ],
      vote_sources: [{
        name: "House Clerk roll call 32",
        source_id: "clerk_roll_032",
        url: "https://clerk.house.gov/Votes/2025032",
      }],
      action_meaning_sources: [{
        name: "H.Amdt. 5",
        source_id: "congress_hamdt5",
        url: "https://www.congress.gov/amendment/119th-congress/house-amendment/5",
      }],
    },
  });

  assert.deepEqual(receipt, {
    exactActionMeaning: "The amendment would preserve the listed exception.",
    policyQuestion: "Whether to preserve the listed exception.",
    proposedChange: "",
    representativeVote: "Nay",
    episodeRelationship: "This amendment was one step in the bill's legislative path.",
    limitations: [
      "The exception applies only to the listed institutions.",
    ],
    voteSources: [{
      label: "Official vote",
      url: "https://clerk.house.gov/Votes/2025032",
    }],
    actionSources: [{
      label: "Bill or amendment text",
      url: "https://www.congress.gov/amendment/119th-congress/house-amendment/5",
    }],
  });

  const renderedData = JSON.stringify(receipt);
  for (const forbidden of [
    "house:119:1:32",
    "clerk_roll_032",
    "congress_hamdt5",
    "acceptance_receipt",
    "launch_ratification",
    "m10r1",
    "2026-08-04",
    "a".repeat(64),
  ]) {
    assert.equal(renderedData.includes(forbidden), false, forbidden);
  }
});

test("receipt limitations are omitted when they only describe the review process", () => {
  const receipt = buildPublicReceipt({
    uncertainty_note: "About this interpretation: human-reviewed on 2026-08-04.",
    source_url: "https://clerk.house.gov/Votes/2025032",
  });
  assert.deepEqual(receipt.limitations, []);
  assert.deepEqual(receipt.voteSources, [{
    label: "Official vote",
    url: "https://clerk.house.gov/Votes/2025032",
  }]);
});

test("technical episode identifiers are not presented as policy relationships", () => {
  const receipt = buildPublicReceipt({
    episode_relationship: "halt-fentanyl-legislative-path",
  });
  assert.equal(receipt.episodeRelationship, "");
});

test("materially identical receipt fields are deduplicated after punctuation normalization", () => {
  const receipt = buildPublicReceipt({
    governed_receipt_projection: {
      exact_action_meaning: "Whether to preserve the listed exception.",
      policy_question: " Whether to preserve the listed exception ",
      member_action: "Yea",
    },
  });
  assert.equal(receipt.exactActionMeaning, "Whether to preserve the listed exception.");
  assert.equal(receipt.policyQuestion, "");
});

test("generic episode process copy is omitted while substantive relationships remain", () => {
  assert.equal(buildPublicReceipt({
    governed_receipt_projection: {
      episode_relationship: "This action is one independently expandable part of the related policy episode.",
    },
  }).episodeRelationship, "");
  assert.equal(buildPublicReceipt({
    governed_receipt_projection: {
      episode_relationship: "This amendment preceded final passage of the same defense authorization bill.",
    },
  }).episodeRelationship, "This amendment preceded final passage of the same defense authorization bill.");
});

test("receipt caveats omit generic candidate language and structural internals", () => {
  const receipt = buildPublicReceipt({
    governed_receipt_projection: {
      caveats: [
        "The reviewed interpretation remains a candidate because implementation depends on incomplete official amendment text.",
        "See docs/semantic_ir/candidate.json and implementation_id M10R1.",
      ],
    },
  });
  assert.deepEqual(receipt.limitations, []);
});
