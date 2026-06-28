import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  RECORD_ACROSS_COPY,
  RECORD_ACROSS_COUNT_FIELDS,
  getDisplayFamilies,
  getFamilyMatchLabel,
  getSparseStateCopy,
  sanitizeRecordAcrossResponse,
} from "./recordAcrossCongresses.mjs";

const COPY_GUARDRAIL = JSON.parse(
  readFileSync(
    new URL("../../docs/review_packets/record_across_congresses_frontend_copy_guardrails.json", import.meta.url),
    "utf8",
  ),
);

function counts(overrides = {}) {
  return {
    cast_substantive_yes_count: 0,
    cast_substantive_no_count: 0,
    not_voting_count: 0,
    present_count: 0,
    missing_no_record_count: 0,
    ...overrides,
  };
}

function family(overrides = {}) {
  return {
    family_id: "direct_family",
    family_name: "Direct Family",
    issue_domain: "NATIONAL_SECURITY_FOREIGN",
    comparability_status: "directly_comparable",
    governing_question: "Whether reviewed assistance restrictions are present in both Congresses.",
    comparability_caveat: "Reviewed caveat text.",
    record_across_congresses_available: true,
    roll_call_ids_considered_by_congress: {
      118: [101],
      119: [201],
    },
    family_evidence_counts_by_congress: {
      118: counts({
        cast_substantive_yes_count: 1,
        not_voting_count: 2,
      }),
      119: counts({
        cast_substantive_no_count: 1,
        present_count: 1,
        missing_no_record_count: 3,
      }),
    },
    ...overrides,
  };
}

function response(overrides = {}) {
  return {
    product_framing: "Record Across Congresses",
    legislator_identifier: "leg_valerie_p_foushee",
    supported_congresses: [118, 119],
    legislator: {
      legislator_identifier: "leg_valerie_p_foushee",
      chamber: "house",
      name_display: "Valerie P. Foushee",
    },
    summary: {
      record_across_congresses_available: true,
      display_eligible_family_count: 2,
      directly_comparable_display_eligible_family_count: 1,
      conditionally_comparable_display_eligible_family_count: 1,
    },
    non_authorization_metadata: {
      internal_response_only: true,
      public_route_exposed: false,
    },
    families: [
      family({
        family_id: "caveated_family",
        family_name: "Caveated Family",
        comparability_status: "conditionally_comparable",
      }),
      family(),
      family({
        family_id: "related_family",
        comparability_status: "related_but_not_comparable",
        record_across_congresses_available: true,
      }),
    ],
    ...overrides,
  };
}

test("sanitized response keeps approved framing and strips internal metadata", () => {
  const sanitized = sanitizeRecordAcrossResponse(response());

  assert.equal(sanitized.product_framing, RECORD_ACROSS_COPY.panelTitle);
  assert.equal(RECORD_ACROSS_COPY.oneSentenceExplanation, "Reviewed House vote evidence exists in both the 118th and 119th Congresses for these policy-question families.");
  assert.equal(sanitized.non_authorization_metadata, undefined);
  assert.equal(sanitized.summary.display_eligible_family_count, 2);
});

test("closest and caveated labels map to approved copy", () => {
  assert.equal(getFamilyMatchLabel("directly_comparable"), RECORD_ACROSS_COPY.directComparableFamilyLabel);
  assert.equal(getFamilyMatchLabel("conditionally_comparable"), RECORD_ACROSS_COPY.conditionalComparableFamilyLabel);
});

test("direct and conditional families are ordered before display", () => {
  const displayFamilies = getDisplayFamilies(sanitizeRecordAcrossResponse(response()));

  assert.deepEqual(
    displayFamilies.map((item) => item.family_id),
    ["direct_family", "caveated_family"],
  );
});

test("counts remain separated across Congresses and buckets", () => {
  const [directFamily] = getDisplayFamilies(sanitizeRecordAcrossResponse(response()));
  const counts118 = directFamily.family_evidence_counts_by_congress["118"];
  const counts119 = directFamily.family_evidence_counts_by_congress["119"];

  assert.equal(counts118.cast_substantive_yes_count, 1);
  assert.equal(counts118.cast_substantive_no_count, 0);
  assert.equal(counts118.not_voting_count, 2);
  assert.equal(counts119.present_count, 1);
  assert.equal(counts119.missing_no_record_count, 3);
  assert.deepEqual(
    RECORD_ACROSS_COUNT_FIELDS.map((field) => field.key),
    [
      "cast_substantive_yes_count",
      "cast_substantive_no_count",
      "not_voting_count",
      "present_count",
      "missing_no_record_count",
    ],
  );
});

test("family caveat is preserved and related rows are not displayed", () => {
  const displayFamilies = getDisplayFamilies(sanitizeRecordAcrossResponse(response()));
  const serialized = JSON.stringify(displayFamilies);

  assert.match(serialized, /Reviewed caveat text/);
  assert.doesNotMatch(serialized, /related_family/);
});

test("sparse states distinguish no eligible family, 118th-only, and 119th-only", () => {
  const noEligible = sanitizeRecordAcrossResponse(response({
    summary: {
      record_across_congresses_available: false,
      display_eligible_family_count: 0,
      directly_comparable_display_eligible_family_count: 0,
      conditionally_comparable_display_eligible_family_count: 0,
    },
    families: [],
  }));
  const priorOnly = sanitizeRecordAcrossResponse(response({
    families: [
      family({
        record_across_congresses_available: false,
        family_evidence_counts_by_congress: {
          118: counts({ cast_substantive_yes_count: 1 }),
          119: counts({ missing_no_record_count: 1 }),
        },
      }),
    ],
  }));
  const recentOnly = sanitizeRecordAcrossResponse(response({
    families: [
      family({
        record_across_congresses_available: false,
        family_evidence_counts_by_congress: {
          118: counts({ missing_no_record_count: 1 }),
          119: counts({ cast_substantive_no_count: 1 }),
        },
      }),
    ],
  }));

  assert.equal(getSparseStateCopy(noEligible), RECORD_ACROSS_COPY.noEligibleFamiliesState);
  assert.equal(getSparseStateCopy(priorOnly), RECORD_ACROSS_COPY.priorCongressOnlyState);
  assert.equal(getSparseStateCopy(recentOnly), RECORD_ACROSS_COPY.recentCongressOnlyState);
});

test("product framing mismatch refuses renderable data", () => {
  assert.equal(sanitizeRecordAcrossResponse(response({ product_framing: "Other Framing" })), null);
});

test("approved visible copy has no disallowed wording", () => {
  const renderedText = [
    RECORD_ACROSS_COPY.panelTitle,
    RECORD_ACROSS_COPY.oneSentenceExplanation,
    RECORD_ACROSS_COPY.directComparableFamilyLabel,
    RECORD_ACROSS_COPY.conditionalComparableFamilyLabel,
    RECORD_ACROSS_COPY.noEligibleFamiliesState,
    RECORD_ACROSS_COPY.priorCongressOnlyState,
    RECORD_ACROSS_COPY.recentCongressOnlyState,
    RECORD_ACROSS_COPY.notVotingCaveat,
    RECORD_ACROSS_COPY.missingNoRecordCaveat,
    RECORD_ACROSS_COPY.relatedUnavailableNote,
    RECORD_ACROSS_COPY.whyNotInferenceExplanation,
    RECORD_ACROSS_COPY.sourceEvidenceDrilldownPrompt,
  ].join("\n");

  assert.deepEqual(
    COPY_GUARDRAIL.disallowed_terms.filter((term) => renderedText.toLowerCase().includes(term)),
    [],
  );
});

test("panel is collapsed by default and placed below strongest issue evidence", () => {
  const panelSource = readFileSync(new URL("../components/RecordAcrossCongressesPanel.js", import.meta.url), "utf8");
  const pageSource = readFileSync(new URL("../app/page.js", import.meta.url), "utf8");
  const evidenceIndex = pageSource.indexOf("<PositionByIssue");
  const panelIndex = pageSource.indexOf("<RecordAcrossCongressesPanel");

  assert.match(panelSource, /<details className=/);
  assert.doesNotMatch(panelSource, /<details[^>]*open=/);
  assert.ok(evidenceIndex > 0 && panelIndex > evidenceIndex);
});

test("server proxy is the only token boundary and client code calls the local route", () => {
  const routeSource = readFileSync(
    new URL("../app/api/record-across-congresses/house/[legislatorId]/route.js", import.meta.url),
    "utf8",
  );
  const apiSource = readFileSync(new URL("./api.js", import.meta.url), "utf8");
  const componentSource = readFileSync(new URL("../components/RecordAcrossCongressesPanel.js", import.meta.url), "utf8");

  assert.match(routeSource, /process\.env\.INTERNAL_API_TOKEN/);
  assert.match(routeSource, /X-Internal-API-Token/);
  assert.match(routeSource, /status: 503/);
  assert.match(apiSource, /\/api\/record-across-congresses\/house\//);
  assert.doesNotMatch(apiSource, /INTERNAL_API_TOKEN|\/internal\/record-across-congresses/);
  assert.doesNotMatch(componentSource, /INTERNAL_API_TOKEN|\/internal\/record-across-congresses/);
});
