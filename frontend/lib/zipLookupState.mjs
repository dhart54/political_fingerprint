export const ZIP_LOOKUP_STATES = Object.freeze({
  SINGLE_DISTRICT_READY: "single_district_ready",
  AMBIGUOUS_ZIP: "ambiguous_zip",
  MULTI_STATE_ZIP: "multi_state_zip",
  UNSUPPORTED_ZIP: "unsupported_zip",
  FIXTURE_SAMPLE_ONLY: "fixture_sample_only",
  STALE_OR_UNKNOWN_SOURCE: "stale_or_unknown_source",
  MEMBER_METADATA_UNCERTAIN: "member_metadata_uncertain",
});

const SENATE_STATE_LEVEL_CAVEAT =
  "Senators represent the whole state. We show them from the ZIP's state, not from a district-level address match.";

const COPY = {
  [ZIP_LOOKUP_STATES.SINGLE_DISTRICT_READY]: {
    severity: "info",
    title: "One district found for this ZIP",
    message:
      "ZIPs are not always precise. This ZIP currently has one loaded district match, so you can inspect the returned House member and state-level senators.",
    nextActions: ["Inspect the returned profile.", "Search by representative name if this does not look right."],
  },
  [ZIP_LOOKUP_STATES.AMBIGUOUS_ZIP]: {
    severity: "warning",
    title: "This ZIP may include multiple districts",
    message:
      "This ZIP may include more than one congressional district. To avoid showing the wrong House member, search by representative name.",
    nextActions: ["Search by representative name.", "Wait for address-level lookup before relying on ZIP-only district matching."],
  },
  [ZIP_LOOKUP_STATES.MULTI_STATE_ZIP]: {
    severity: "warning",
    title: "This ZIP may cross state lines",
    message:
      "This ZIP appears in more than one state in the loaded mapping. To avoid showing the wrong officials, search by representative name.",
    nextActions: ["Search by representative name.", "Do not use this ZIP result as a state or district match."],
  },
  [ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP]: {
    severity: "neutral",
    title: "ZIP not loaded yet",
    message:
      "This ZIP is not in the loaded map yet. You can still search by representative name while coverage expands.",
    nextActions: ["Search by representative name.", "Try one of the loaded sample ZIPs if you are reviewing demo coverage."],
  },
  [ZIP_LOOKUP_STATES.FIXTURE_SAMPLE_ONLY]: {
    severity: "warning",
    title: "Sample coverage",
    message: "This is sample coverage, not national coverage yet.",
    nextActions: ["Search by representative name to inspect loaded records.", "Do not treat this as national ZIP coverage."],
  },
  [ZIP_LOOKUP_STATES.STALE_OR_UNKNOWN_SOURCE]: {
    severity: "warning",
    title: "Lookup source needs confirmation",
    message:
      "We found a possible match, but the lookup source date is not confirmed. Please confirm the representative before relying on this result.",
    nextActions: ["Search by representative name.", "Confirm the official before treating this as your representative."],
  },
  [ZIP_LOOKUP_STATES.MEMBER_METADATA_UNCERTAIN]: {
    severity: "warning",
    title: "Representative metadata needs confirmation",
    message:
      "We found the district, but our current representative metadata needs confirmation before we show a profile as your representative.",
    nextActions: ["Search by representative name.", "Inspect loaded records without treating the result as a confirmed match."],
  },
};

export function classifyZipLookupState(payload = null) {
  const mappings = normalizeMappings(payload);
  const uniqueStates = uniqueValues(mappings.map((row) => row.state).filter(Boolean));
  const uniqueDistrictKeys = uniqueValues(
    mappings
      .filter((row) => row.state && row.district)
      .map((row) => `${row.state}-${row.district}`),
  );
  const metadata = {
    ...(payload?.source_metadata || {}),
    ...(payload?.sourceMetadata || {}),
    ...(payload?.lookup_metadata || {}),
    ...(payload?.lookupMetadata || {}),
  };
  const hasHouseRep = Boolean(payload?.house_rep);
  const hasSenators = Array.isArray(payload?.senators) && payload.senators.length > 0;
  const isUnsupported =
    !payload ||
    payload.status === ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP ||
    payload.lookup_state === ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP ||
    payload.error === "unsupported_zip";
  const isFixtureSample =
    payload?.data_source === "fixtures" ||
    payload?.dataSource === "fixtures" ||
    metadata.fixture_sample_only === true ||
    metadata.source_type === "fixture_sample" ||
    metadata.source_currentness === "fixture_sample";
  const sourceKnown = hasKnownSourceMetadata(metadata);
  const sourceIsStaleOrUnknown =
    metadata.stale_or_unknown_source === true ||
    metadata.source_currentness === "stale_or_unknown" ||
    metadata.currentness === "stale_or_unknown" ||
    (!isFixtureSample && !sourceKnown);
  const memberMetadataUncertain =
    metadata.member_metadata_uncertain === true ||
    payload?.member_metadata_uncertain === true ||
    payload?.house_rep?.metadata_currentness === "uncertain";

  let state = ZIP_LOOKUP_STATES.SINGLE_DISTRICT_READY;
  if (isUnsupported) {
    state = ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP;
  } else if (uniqueStates.length > 1) {
    state = ZIP_LOOKUP_STATES.MULTI_STATE_ZIP;
  } else if (uniqueDistrictKeys.length > 1) {
    state = ZIP_LOOKUP_STATES.AMBIGUOUS_ZIP;
  } else if (isFixtureSample) {
    state = ZIP_LOOKUP_STATES.FIXTURE_SAMPLE_ONLY;
  } else if (sourceIsStaleOrUnknown) {
    state = ZIP_LOOKUP_STATES.STALE_OR_UNKNOWN_SOURCE;
  } else if (memberMetadataUncertain) {
    state = ZIP_LOOKUP_STATES.MEMBER_METADATA_UNCERTAIN;
  }

  const copy = COPY[state];
  const caveats = buildCaveats({
    hasSenators,
    isFixtureSample,
    mappings,
    state,
    uniqueStates,
  });
  const canAutoSelectHouse =
    state === ZIP_LOOKUP_STATES.SINGLE_DISTRICT_READY &&
    hasHouseRep &&
    !isFixtureSample &&
    !sourceIsStaleOrUnknown &&
    !memberMetadataUncertain &&
    uniqueStates.length <= 1 &&
    uniqueDistrictKeys.length <= 1;
  const canAutoSelectSenate =
    state === ZIP_LOOKUP_STATES.SINGLE_DISTRICT_READY &&
    hasSenators &&
    uniqueStates.length === 1 &&
    !isFixtureSample &&
    !sourceIsStaleOrUnknown;

  return {
    state,
    canAutoSelectHouse,
    canAutoSelectSenate,
    severity: copy.severity,
    title: copy.title,
    message: copy.message,
    nextActions: copy.nextActions,
    caveats,
    districtMappings: mappings,
    knownStates: uniqueStates,
    knownDistricts: uniqueDistrictKeys,
    hasHouseRep,
    hasSenators,
  };
}

export function getSenateStateLevelCaveat() {
  return SENATE_STATE_LEVEL_CAVEAT;
}

function normalizeMappings(payload) {
  const rawMappings =
    payload?.district_mappings ||
    payload?.districtMappings ||
    payload?.zip_district_mappings ||
    payload?.mappings ||
    [];
  const mappings = Array.isArray(rawMappings)
    ? rawMappings
        .map((row) => normalizeMapping(row, payload?.zip))
        .filter((row) => row.zip || row.state || row.district)
    : [];

  if (!mappings.length && (payload?.zip || payload?.state || payload?.district)) {
    mappings.push(normalizeMapping(payload, payload?.zip));
  }

  const seen = new Set();
  return mappings.filter((row) => {
    const key = `${row.zip || ""}:${row.state || ""}:${row.district || ""}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function normalizeMapping(row, fallbackZip) {
  return {
    zip: row?.zip ? String(row.zip) : fallbackZip ? String(fallbackZip) : "",
    state: row?.state ? String(row.state) : "",
    district: row?.district ? String(row.district) : "",
  };
}

function uniqueValues(values) {
  return [...new Set(values)];
}

function hasKnownSourceMetadata(metadata) {
  if (metadata.source_currentness === "current" || metadata.currentness === "current") {
    return true;
  }
  return Boolean(
    metadata.source_retrieved_at ||
      metadata.sourceRetrievedAt ||
      metadata.retrieved_at ||
      metadata.source_effective_date ||
      metadata.sourceEffectiveDate ||
      metadata.source_version ||
      metadata.sourceVersion ||
      metadata.version,
  );
}

function buildCaveats({ hasSenators, isFixtureSample, mappings, state, uniqueStates }) {
  const caveats = [];
  if (hasSenators && uniqueStates.length === 1 && state !== ZIP_LOOKUP_STATES.MULTI_STATE_ZIP) {
    caveats.push(SENATE_STATE_LEVEL_CAVEAT);
  }
  if (isFixtureSample && state !== ZIP_LOOKUP_STATES.FIXTURE_SAMPLE_ONLY) {
    caveats.push("This is sample coverage, not national coverage yet.");
  }
  if (mappings.length > 1 && state === ZIP_LOOKUP_STATES.AMBIGUOUS_ZIP) {
    caveats.push(`Loaded district matches: ${mappings.map((row) => `${row.state}-${row.district}`).join(", ")}.`);
  }
  return caveats;
}
