# Current House Member Metadata Hardening V1

## Summary

- Retrieval/replay mode: `local_replay`
- API key present: `True`
- Voting representatives: `431`
- Vacant voting seats: `4`
- Delegates: `5`
- Resident commissioners: `1`
- Source conflicts: `0`

## Proposed Schema

- Additive `house_member_service_evidence` and `house_seat_status_evidence` tables.
- Member service and seat vacancy are separate evidence objects.
- Migration prepared but not applied.

## Production Reconciliation

- Exact Bioguide matches: `437`
- Official members unmatched: `0`
- Existing in-office House rows unmatched: `4`
- Former House rows preserved: `77`

## DC Normalization

- Census `DC-98` is associated only for reconciliation with canonical House delegate seat `DC-00` under `dc_census_98_to_house_delegate_00_v1`.
- Raw and canonical values remain separate; delegate auto-select stays blocked.

## Readiness Impact

- Source-to-member-ready pairs: `431`
- Source-to-member-ready candidate ZCTAs: `27617`
- Production auto-select eligible: `0`

## Safety

- Database transaction read-only: `True`
- Migration applied: `False`
- Database/member/ZIP writes: `False`
- Public routes and feature flag unchanged.

## Recommended Next Milestone

Current House member metadata schema application and bounded seed V1
