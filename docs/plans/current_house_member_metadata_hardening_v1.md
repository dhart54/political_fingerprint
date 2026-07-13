# Milestone Plan: Current House Member Metadata Hardening V1

## Intent

- Pin, retrieve, normalize, and reconcile official 119th Congress House member/seat evidence without production writes.
- Prepare an additive service/seat schema so currentness, vacancy, and nonvoting roles can eventually be evaluated safely.

## Outcome

- Reviewed official-source artifacts in ignored local storage, pure normalization/reconciliation logic, an unapplied additive migration, deterministic tests, and JSON/Markdown review packets.

## Scope And Boundaries

- In scope: Congress.gov API, House directory, Clerk vacancy evidence, local replay, checksums, read-only production matching, additive SQL preparation, tests, manifest, and review packets.
- Out of scope: migration application, seeds/ingestion, member mutation, ZIP population, route/flag/frontend changes, and production auto-select.

## Decision Envelope

- Source conflicts and incomplete layouts must block readiness rather than trigger precedence or inference.
- Service years remain year precision; exact dates are stored only when explicitly supplied by an official source.
- Schema may be prepared and tested but must not be executed.

## Definition Of Done

- [x] Official source decisions/endpoints, retrieval metadata, and checksums are pinned.
- [x] Bounded retrieval/local replay and fail-closed parsers are implemented.
- [x] Additive member-service and seat-status migration passes contract tests and remains unapplied.
- [x] Production legislators are reconciled in a verified read-only transaction.
- [x] Vacancies, voting members, delegates, resident commissioner, conflicts, and DC-98-to-00 reconciliation are explicit.
- [x] Readiness is re-evaluated while production auto-select remains zero.
- [x] Required tests, JSON checks, postchecks, static checks, and diff hygiene pass.
- [x] Scoped commits, push, and draft PR are complete (PR #87).

## Baseline

- Branch/base: `codex/current-house-member-metadata-hardening-v1` from `09514fb58a178d5cb7dca79ce6e2b87dafbf1bd9`.
- `zip_district_mappings`: exists with actual row count zero by read-only postcheck.
- Public ZIP endpoints: compatibility `zip_district_map`; multi-row feature flag absent/not enabled.
- Congress API key: present in ignored `backend/.env`; value will not be logged or persisted.
- Latest migration: `0013_zip_district_mappings.sql`; proposed additive migration will be `0014`.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Verify official source contracts and existing repository source-client/schema conventions.
2. Retrieve bounded official artifacts to ignored `.local/` or record a blocked retrieval result.
3. Implement pure normalization/reconciliation and additive schema proposal with fixtures/tests.
4. Run local replay plus verified production read-only reconciliation and readiness evaluation.
5. Generate/reconcile manifest, packets, plan, validation, commits, and draft PR.

## Progress Checklist

- [x] Baseline and hard-stop checks
- [x] Source retrieval and discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Congress API credentials are available through the ignored backend environment.
- Existing production member schema lacks Congress, term years, seat status, member type, and source-currentness evidence.
- Bounded live retrieval produced 537 Congress.gov list records and 481 House detail responses; 437 detail records contain a 119th House term.
- Congress.gov detail JSON uses a direct `terms` array rather than the documentation's illustrated `terms.item` container. The parser supports only these two explicit shapes and otherwise fails closed.
- Congress.gov omits district for some at-large/nonvoting details; canonical `00` is allowed only for the six documented voting-at-large states and explicit Delegate/Resident Commissioner member types.
- House.gov parsed 441 seats: 437 filled and four visibly vacant. The Clerk independently reported the same four vacancies.
- Official normalized roster: 431 voting representatives, five delegates, one resident commissioner, four vacant voting seats, zero duplicate seats, and zero source conflicts.
- Production reconciliation matched all 437 official members by Bioguide ID. Four existing `in_office=true` House rows are contradicted by the official vacancy/roster sources; 77 former House rows remain historical.

## Decisions And Rationale

- Use Congress.gov for identity/service, House.gov for roster/role cross-check, and Clerk evidence for vacancy/succession; no single source proves every field.
- Preserve Congress/Census raw districts and canonical districts separately; only documented reconciliation may associate Census DC-98 with canonical House DC-00.
- Seven days is the configurable evaluation snapshot-age policy for this milestone, not an eternal source truth.

## Deviations Or Corrections

- Live Congress.gov JSON required the documented narrow `terms` container adapter noted above; no field meaning or year precision was inferred.

## Validation Results

- Initial ZIP read-only postcheck passed: migration not rerun, target row count zero, seed not loaded.
- Live retrieval/local replay: passed with API key present but never logged; 486 official artifacts recorded with SHA-256 checksums in the source manifest.
- Dry-run read-only reconciliation: 431 diagnostically ready voting pairs, 27,617 candidate ZCTAs, and production auto-select eligibility fixed at zero.
- Focused metadata/readiness/parser suite: 40 passed.
- Final combined metadata, PR #86 readiness, and ZIP suite: 69 passed in 9.71 seconds.
- New review packet/source manifest, PR #86 packet, and PR #85 source manifest: valid JSON.
- Proposed tables confirmed absent by read-only `information_schema` query; migration remains unapplied.
- Final ZIP postcheck: target row count zero, no migration rerun, no seed load.
- Static route/flag checks: both public endpoints remain on `zip_district_map`; feature flag is not enabled.
- `git diff --check`: passed.

## Production Writes

- Performed: no.
- Scope/expected/actual effects: official-source reads, local ignored files, production SELECTs, and repository artifacts only.

## Rollback Paths

- Revert branch files and delete ignored local artifacts. No database rollback is applicable because migration/application and data writes are forbidden.

## Blockers

- None for this no-write milestone. Four production `in_office=true` rows conflict with current official vacancy evidence and must not be mutated until a later authorized seed/application milestone.

## Final Reconciliation

- Definition of done satisfied: yes; implementation, validation, commit, push, and draft PR #87 are complete.
- Remaining limitations: Congress service dates are year precision; exact vacancy dates exist only where explicitly displayed; four production rows remain stale until an authorized later write.
- Recommended next step: Current House member metadata schema application and bounded seed V1 because official sources reconcile with zero seat conflicts and the additive schema contract passes; do not switch ZIP routes.
