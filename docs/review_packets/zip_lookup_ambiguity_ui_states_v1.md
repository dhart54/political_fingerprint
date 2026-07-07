# ZIP Lookup Ambiguity UI States V1

## Summary

This milestone changes the existing ZIP lookup flow from "successful response means open the House profile" to an explicit lookup-state model.

Implemented recommendation:

- ZIP lookup may auto-select a House profile only for `single_district_ready`.
- Ambiguous, multi-state, unsupported, fixture/sample, stale/unknown-source, and member-metadata-uncertain results do not auto-open a House profile.
- Manual representative search remains visible as the safe fallback.
- No address lookup, provider integration, national data ingestion, schema change, or production write was added.

## Product Behavior Changed

Before:

- Any successful `/lookup/zip/{zip}` response with `house_rep` caused the frontend to call `onSelectLegislator`.
- The result copy said the ZIP mapped to one `state-district`.
- The panel loaded race context and comparison seeds after any successful ZIP lookup.
- Fixture fallback lookup did not identify itself in the ZIP lookup payload.

After:

- The frontend classifies the payload with `classifyZipLookupState`.
- House auto-select, comparison seeding, and ZIP race loading happen only when `canAutoSelectHouse` is true.
- Unsafe states keep the current/sample profile unchanged and show clear copy.
- `/lookup/zip/{zip}` payloads now include additive metadata: `data_source`, `lookup_metadata`, and `district_mappings`.
- Local fixture split-ZIP evidence is exposed in fallback payloads so ZIP `27601` can be classified as ambiguous when local mappings include multiple districts.

## Lookup States Implemented

| State | Trigger | Auto-select behavior | User-facing behavior |
| --- | --- | --- | --- |
| `single_district_ready` | One state/district mapping, non-fixture source, known source metadata, House member present, member metadata not flagged uncertain | House may auto-select; Senate compare may seed | Shows ZIP precision caveat and Senate state-level caveat |
| `ambiguous_zip` | One ZIP maps to more than one district | No House auto-select | Shows: "This ZIP may include more than one congressional district. To avoid showing the wrong House member, search by representative name." |
| `multi_state_zip` | ZIP mappings include more than one state | No House or Senate auto-select | Explains the state cannot be treated as known and points to representative-name search |
| `unsupported_zip` | ZIP lookup returns no loaded mapping | No auto-select | Shows: "This ZIP is not in the loaded map yet. You can still search by representative name while coverage expands." |
| `fixture_sample_only` | Lookup payload comes from `fixtures` or `fixture_sample` metadata | No production-style auto-select | Shows: "This is sample coverage, not national coverage yet." |
| `stale_or_unknown_source` | Source date/version/currentness is missing or explicitly flagged stale/unknown | No auto-select | Asks the user to confirm via representative search |
| `member_metadata_uncertain` | Payload explicitly flags member metadata as uncertain | No auto-select | Avoids presenting the profile as "your representative" |

## Auto-Selection Rules

House auto-selection now requires all of the following:

- `house_rep` is present.
- Lookup state is `single_district_ready`.
- Result is not fixture/sample-only.
- Result is not ambiguous or multi-state.
- Result is not stale/unknown-source.
- Member metadata is not marked uncertain.

All other states leave the currently selected profile unchanged.

Senate behavior:

- Multi-state ZIPs block Senate auto-selection because state is not known.
- Single-state results may show senator cards with the caveat: "Senators represent the whole state. We show them from the ZIP's state, not from a district-level address match."
- This milestone does not make Senate currentness/seat/class claims.

## Copy Added

Required copy or close equivalents added:

- "This ZIP may include more than one congressional district. To avoid showing the wrong House member, search by representative name."
- "This ZIP is not in the loaded map yet. You can still search by representative name while coverage expands."
- "This is sample coverage, not national coverage yet."
- "Senators represent the whole state. We show them from the ZIP's state, not from a district-level address match."

Additional copy:

- "ZIP lookup did not auto-open a House profile. Use manual search or inspect clearly labeled loaded records."
- "We found a possible match, but the lookup source date is not confirmed. Please confirm the representative before relying on this result."
- "We found the district, but our current representative metadata needs confirmation before we show a profile as your representative."

No copy says full address entry is available.

## Tests Added

Frontend helper:

- `frontend/lib/zipLookupState.test.mjs`
- Covers single district ready, ambiguous ZIP, multi-state ZIP, unsupported ZIP, fixture/sample-only, stale/unknown source, member metadata uncertainty, and Senate state-level caveat.

Rendered UI:

- `frontend/app/zip-lookup-state-fixture/page.js`
- `frontend/components/ZipLookupStateFixture.js`
- `frontend/tests/zip-lookup-state.spec.mjs`
- The route is gated behind `ENABLE_ZIP_LOOKUP_STATE_FIXTURE=1`.
- Covers ambiguity copy, sample coverage copy, unsupported ZIP copy, no selection callback for unsafe states, and selection callback for `single_district_ready`.

Backend:

- `backend/tests/test_db_read_layer.py`
- Verifies database lookup payloads include additive source metadata and one district mapping.
- Verifies fixture fallback payloads expose fixture sample metadata and local split-ZIP mappings.

## Known Limitations

- `zip_district_map.zip` remains a primary key, so production database storage still cannot represent multiple districts per ZIP.
- Database ZIP rows currently have no source date/version fields. The frontend therefore treats database lookup payloads without source metadata as `stale_or_unknown_source` and blocks auto-select.
- Member metadata uncertainty can be modeled only when the payload explicitly flags it. This milestone does not add full currentness/term-boundary gates.
- Multi-state ZIP behavior is implemented and tested through the shared state helper, but no repository fixture currently provides a multi-state ZIP through the live fallback route.
- The gated rendered fixture is test-only and not linked from normal UI.
- Full backend suite was locally limited by configured database and temp-directory permissions; focused backend tests passed.

## No-Go Items Honored

- No address lookup added.
- No Census, Google, Smarty, Cicero, or other provider integration added.
- No national ZIP data ingestion.
- No local or production DB mutation.
- No vote interpretation semantics changed.
- No member coverage expansion.
- No Record Across behavior changed.
- No full address storage or collection.

## Validation

- `node --test lib\zipLookupState.test.mjs` from `frontend`: passed, 8/8.
- `npx playwright test tests/zip-lookup-state.spec.mjs` from `frontend`: passed, 4/4.
- `node --test lib\*.test.mjs` from `frontend`: passed, 83/83.
- `npm run lint` from `frontend`: passed with 8 existing hook dependency warnings.
- `npm run build` from `frontend`: passed with the same hook dependency warnings.
- `python -m pytest backend\tests\test_db_read_layer.py -p no:cacheprovider`: passed, 7/7.
- `python -m pytest backend\tests -p no:cacheprovider`: attempted; 341 passed, 6 failed, 25 errors due to local database/temp-directory state. The focused ZIP backend coverage passed.

## Recommended Next Milestone

**ZIP Source Metadata And Ambiguity Payload V1**

Scope:

- Add source/date/version/currentness metadata to ZIP mapping responses from the database path.
- Define the production-ready ambiguity payload shape before schema/data ingestion.
- Add read-only database coverage checks for ZIP source metadata completeness.
- Keep current UI gates: no auto-select for missing source metadata.
- Do not add address lookup yet.
- Do not ingest national ZIP data until schema/source decisions are approved.
