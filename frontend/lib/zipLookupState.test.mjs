import assert from "node:assert/strict";
import test from "node:test";

import {
  ZIP_LOOKUP_STATES,
  classifyZipLookupState,
  getSenateStateLevelCaveat,
} from "./zipLookupState.mjs";

const houseRep = {
  id: "leg_valerie_foushee",
  name_display: "Valerie P. Foushee",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};

const senators = [
  {
    id: "leg_ted_budd",
    name_display: "Ted Budd",
    chamber: "senate",
    state: "NC",
    district: null,
    party: "R",
  },
];

test("single district ready allows House auto-select", () => {
  const result = classifyZipLookupState({
    zip: "27701",
    state: "NC",
    district: "04",
    data_source: "database",
    lookup_metadata: {
      source_type: "reviewed_zip_map",
      source_name: "reviewed_zip_district_source",
      source_retrieved_at: "2026-07-01",
      source_effective_date: "2026-01-03",
      source_version: "reviewed-v1",
      source_currentness: "current",
      fixture_sample_only: false,
      stale_or_unknown_source: false,
      member_metadata_uncertain: false,
      can_represent_multiple_districts: true,
      ambiguity_detection_level: "multi_row_source",
    },
    district_mappings: [
      {
        zip: "27701",
        state: "NC",
        district: "04",
        source_type: "reviewed_zip_map",
        source_name: "reviewed_zip_district_source",
        source_version: "reviewed-v1",
      },
    ],
    house_rep: houseRep,
    senators,
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.SINGLE_DISTRICT_READY);
  assert.equal(result.canAutoSelectHouse, true);
  assert.equal(result.canAutoSelectSenate, true);
});

test("ambiguous ZIP blocks House auto-select", () => {
  const result = classifyZipLookupState({
    zip: "27601",
    data_source: "database",
    source_metadata: {
      source_retrieved_at: "2026-07-01",
      source_version: "reviewed-v1",
    },
    district_mappings: [
      { zip: "27601", state: "NC", district: "02" },
      { zip: "27601", state: "NC", district: "04" },
    ],
    house_rep: houseRep,
    senators,
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.AMBIGUOUS_ZIP);
  assert.equal(result.canAutoSelectHouse, false);
  assert.match(result.message, /more than one congressional district/i);
});

test("multi-state ZIP blocks House and Senate auto-select", () => {
  const result = classifyZipLookupState({
    zip: "42223",
    data_source: "database",
    source_metadata: {
      source_retrieved_at: "2026-07-01",
      source_version: "reviewed-v1",
    },
    district_mappings: [
      { zip: "42223", state: "KY", district: "01" },
      { zip: "42223", state: "TN", district: "07" },
    ],
    house_rep: houseRep,
    senators,
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.MULTI_STATE_ZIP);
  assert.equal(result.canAutoSelectHouse, false);
  assert.equal(result.canAutoSelectSenate, false);
});

test("unsupported ZIP blocks auto-select", () => {
  const result = classifyZipLookupState({
    zip: "99999",
    status: "unsupported_zip",
    data_source: "none",
    lookup_metadata: {
      source_type: "none",
      source_name: null,
      source_retrieved_at: null,
      source_effective_date: null,
      source_version: null,
      source_currentness: "unsupported",
      fixture_sample_only: false,
      stale_or_unknown_source: false,
      member_metadata_uncertain: false,
      can_represent_multiple_districts: false,
      ambiguity_detection_level: "none",
    },
    house_rep: null,
    senators: [],
    district_mappings: [],
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP);
  assert.equal(result.canAutoSelectHouse, false);
  assert.match(result.message, /not in the loaded map yet/i);
});

test("fixture sample-only blocks production-style auto-select", () => {
  const result = classifyZipLookupState({
    zip: "27701",
    state: "NC",
    district: "04",
    data_source: "fixtures",
    lookup_metadata: {
      fixture_sample_only: true,
      source_type: "fixture_sample",
      source_currentness: "fixture_sample",
    },
    house_rep: houseRep,
    senators,
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.FIXTURE_SAMPLE_ONLY);
  assert.equal(result.canAutoSelectHouse, false);
  assert.match(result.message, /sample coverage/i);
});

test("stale or unknown source blocks auto-select when modeled", () => {
  const result = classifyZipLookupState({
    zip: "27701",
    state: "NC",
    district: "04",
    data_source: "database",
    lookup_metadata: {
      stale_or_unknown_source: true,
    },
    house_rep: houseRep,
    senators,
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.STALE_OR_UNKNOWN_SOURCE);
  assert.equal(result.canAutoSelectHouse, false);
});

test("standardized DB payload with missing source metadata stays stale or unknown", () => {
  const result = classifyZipLookupState({
    zip: "27701",
    state: "NC",
    district: "04",
    data_source: "database",
    lookup_metadata: {
      source_type: "database_zip_district_map",
      source_name: "zip_district_map",
      source_retrieved_at: null,
      source_effective_date: null,
      source_version: null,
      source_currentness: "stale_or_unknown",
      fixture_sample_only: false,
      stale_or_unknown_source: true,
      member_metadata_uncertain: false,
      can_represent_multiple_districts: false,
      ambiguity_detection_level: "single_row",
    },
    district_mappings: [
      {
        zip: "27701",
        state: "NC",
        district: "04",
        source_type: "database_zip_district_map",
        source_name: "zip_district_map",
        source_version: null,
      },
    ],
    house_rep: houseRep,
    senators,
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.STALE_OR_UNKNOWN_SOURCE);
  assert.equal(result.canAutoSelectHouse, false);
});

test("member metadata uncertain blocks auto-select", () => {
  const result = classifyZipLookupState({
    zip: "27701",
    state: "NC",
    district: "04",
    data_source: "database",
    source_metadata: {
      source_retrieved_at: "2026-07-01",
      source_version: "reviewed-v1",
    },
    lookup_metadata: {
      member_metadata_uncertain: true,
    },
    house_rep: houseRep,
    senators,
  });

  assert.equal(result.state, ZIP_LOOKUP_STATES.MEMBER_METADATA_UNCERTAIN);
  assert.equal(result.canAutoSelectHouse, false);
});

test("senators are treated as a state-level caveat", () => {
  const result = classifyZipLookupState({
    zip: "27701",
    state: "NC",
    district: "04",
    data_source: "database",
    source_metadata: {
      source_retrieved_at: "2026-07-01",
      source_version: "reviewed-v1",
    },
    house_rep: houseRep,
    senators,
  });

  assert.ok(result.caveats.includes(getSenateStateLevelCaveat()));
});
