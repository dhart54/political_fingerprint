# ZIP Source-to-Member Readiness Gate V1

## Outcome

- The exact PR #85 Census artifact was verified before evaluation.
- The production member session and transaction were confirmed read-only.
- Source-to-member-ready pairs: `0`.
- Source-to-member-ready candidate ZCTAs: `0`.
- Final production auto-select eligibility remains `0`.

## Source Identity

- File: `tab20_cd11920_zcta520_natl.txt`
- Expected/actual size: `6195997` / `6195997`
- Expected SHA-256: `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77`
- Actual SHA-256: `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77`
- Identity verified: `True`

## Production Read-Only Audit

- Member rows inspected: `637`
- Current House rows inspected: `441`
- Schema sufficient for currentness gate: `False`
- Missing fields: `congress, member_type, metadata_currentness, metadata_retrieved_at, metadata_source_url, seat_status, term_end, term_start`
- Existing public House lookup does not require `in_office`: `True`.
- Existing public House lookup selects the first row without duplicate detection: `True`.
- Lookup audit evidence: `backend/app/api/precomputed.py::_get_db_house_rep`; Query orders by id with LIMIT 1 and contains no in_office predicate.

## Verification

- `zip_district_mappings` exists: `True`
- Actual `zip_district_mappings` row count: `0`
- Empty status derived from count: `True`
- Database verification method: information_schema existence SELECT followed by bounded SELECT COUNT(*) in the verified read-only transaction
- Route files inspected: `backend/app/api/lookup.py, backend/app/api/precomputed.py`
- Route functions inspected: `lookup_zip, lookup_zip_races, get_zip_lookup_response, get_zip_race_response, _get_db_zip_lookup_response, _get_db_zip_race_response, _get_db_zip_record`
- `/lookup/zip/{zip_code}` reads `zip_district_map`: `True`
- `/lookup/zip/{zip_code}/races` reads `zip_district_map`: `True`
- Either public endpoint reads `zip_district_mappings`: `False`
- Feature flag status: `absent_not_configured`; enabled: `False`
- Feature flag verification method: bounded repository configuration/code scan for ZIP_MULTI_ROW_LOOKUP_ENABLED assignments
- Migration rerun by evaluator: `False`
- Migration rerun in this milestone: `False`

## Readiness Status Distribution

- `nonvoting_delegate_review_required`: `1`
- `schema_insufficient_for_currentness_gate`: `435`

## At-Large And Territory Findings

- Voting at-large source pairs: `6`
- DC delegate source pairs: `1` (review required)
- DC source district code is `98`. Any future conversion to the internal district `00` convention requires a documented normalization rule; this milestone does not perform that conversion.
- Territorial delegate source pairs accepted: `0`
- Resident commissioner source pairs accepted: `0`
- Territory rows rejected during source parsing: `{"AS": 2, "GU": 8, "MP": 4, "PR": 133, "VI": 7}`

## Safety

- database_write_occurred: `False` - Connection default and active transaction were verified read-only; evaluator SQL is limited to SET/SHOW/SELECT.
- database_session_read_only: `True` - Derived from verified default_transaction_read_only and transaction_read_only server settings.
- zip_district_mappings_remains_empty: `True` - Derived from the inspected zip_district_mappings actual_row_count.
- both_public_zip_endpoints_use_zip_district_map: `True` - Derived from AST-bounded inspection of the recorded route/read functions.
- public_endpoints_read_zip_district_mappings: `False` - Derived from SQL table-reference checks in the bounded public lookup function set.
- zip_multi_row_lookup_flag_status: `absent_not_configured` - Derived from the bounded repository configuration/code scan.
- zip_multi_row_lookup_enabled: `False` - Derived from parsed flag assignments; enabled state is a hard failure.
- migration_rerun_by_evaluator: `False` - Evaluator contains no migration invocation or DDL path; runtime database transaction is read-only.
- member_metadata_mutated: `False` - Evaluator issues only bounded member SELECT and schema SELECT queries in the verified read-only transaction.
- production_auto_select_enabled: `False` - Evaluator report contract fixes production_auto_select_eligible_count to zero and changes no runtime route/config files.

## Recommended Next Milestone

**Current House member metadata hardening V1** - Stored member metadata lacks term, vacancy, member-type, source, and retrieval evidence required to prove currentness safely.
