import assert from "node:assert/strict";
import test from "node:test";

import {
  deriveInterpretedCountsFromEvidence,
  fillMissingInterpretedCounts,
  hasInterpretedCountFields,
} from "./positionEvidenceCounts.mjs";

test("interpreted count fallback derives support and opposition only from interpreted evidence", () => {
  const counts = deriveInterpretedCountsFromEvidence([
    {
      interpretation_status: "interpreted",
      position: "yea",
      support_position: "yea",
      oppose_position: "nay",
    },
    {
      interpretation_status: "interpreted",
      position: "nay",
      support_position: "yea",
      oppose_position: "nay",
    },
    {
      interpretation_status: "interpreted",
      position: "not_voting",
      support_position: "yea",
      oppose_position: "nay",
    },
    {
      interpretation_status: "insufficient_evidence",
      position: "yea",
      support_position: null,
      oppose_position: null,
    },
  ]);

  assert.deepEqual(counts, {
    interpreted_support_count: 1,
    interpreted_oppose_count: 1,
    interpreted_other_count: 1,
    interpreted_total: 3,
  });
});

test("position payloads with missing interpreted fields are enriched from evidence endpoints", async () => {
  const payload = {
    legislator_id: "leg_valerie_p_foushee",
    positions: [
      {
        domain: "ECONOMY_TAXES",
        recorded_votes: 8,
        total_votes: 9,
      },
      {
        domain: "JUSTICE_PUBLIC_SAFETY",
        recorded_votes: 13,
        total_votes: 13,
        interpreted_support_count: 2,
        interpreted_oppose_count: 4,
        interpreted_other_count: 0,
        interpreted_total: 6,
      },
    ],
  };
  const requestedDomains = [];

  const enriched = await fillMissingInterpretedCounts({
    payload,
    legislatorId: "leg_valerie_p_foushee",
    fetchEvidence: async ({ domain }) => {
      requestedDomains.push(domain);
      return {
        evidence: [
          {
            interpretation_status: "interpreted",
            position: "nay",
            support_position: "yea",
            oppose_position: "nay",
          },
          {
            interpretation_status: "ambiguous",
            position: "nay",
            support_position: null,
            oppose_position: null,
          },
        ],
      };
    },
  });

  assert.deepEqual(requestedDomains, ["ECONOMY_TAXES"]);
  assert.equal(hasInterpretedCountFields(enriched.positions[0]), true);
  assert.equal(enriched.positions[0].interpreted_support_count, 0);
  assert.equal(enriched.positions[0].interpreted_oppose_count, 1);
  assert.equal(enriched.positions[0].interpreted_total, 1);
  assert.equal(enriched.positions[1].interpreted_total, 6);
});
