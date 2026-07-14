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
- [x] Clerk special-election variants are parsed into separate type/date fields without member-name overcapture.
- [x] Seed previews map directly and deterministically to migration `0014`, including production IDs and schema validation.
- [x] Member/seat evidence has explicit snapshot-scoped artifact lineage with duplicate prevention and cascade rollback.
- [x] Replay independently proves list pagination, detail completeness/identity, statuses, URLs, and exact artifact types.
- [x] Packets/manifests are regenerated, the full requested validation matrix passes, and PR #87 is updated without applying the migration.
- [x] Member-service previews copy exact URL, checksum, retrieval timestamp, and source labels from their allowlisted detail artifact.
- [x] Preview validation fails on date-only or mismatched member/artifact provenance.
- [x] Replay reports 481 detail candidates, 437 normalized current-119th-House members, and 44 skipped historical-House candidates without changing the roster.
- [x] Regenerated artifacts, no-write validation, corrective commit/push, and draft PR #87 description update are complete.

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
6. Correct Clerk parsing and add manipulated-source failure coverage.
7. Refine migration `0014`, generate directly insertable previews and explicit evidence-artifact links, and validate preview-to-schema mapping.
8. Recompute replay completeness from Congress list pages, regenerate review artifacts, rerun read-only gates, and update existing draft PR #87.

## Progress Checklist

- [x] Baseline and hard-stop checks
- [x] Source retrieval and discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness
- [x] PR #87 correction baseline and branch reconciliation
- [x] Parser and replay-completeness corrections
- [x] Seed-preview and evidence-lineage implementation
- [x] Full no-write validation and artifact regeneration
- [x] Corrective commit, push, and existing-PR description update
- [x] Exact-provenance correction baseline
- [x] Member row/artifact provenance implementation and failure coverage
- [x] Artifact regeneration and full no-write validation
- [x] Corrective commit, push, and existing-PR description update

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
- PR #87 hardening replaced the shared local directory with immutable manifest-authoritative snapshot batches, checksum/allowlist replay, UTC freshness enforcement, and deterministic normalized seed previews.
- Cross-source confirmation now requires exact normalized name or official House-domain equivalence plus seat-role agreement; seat occupancy alone is insufficient.
- Clerk parsing is vacancy-record scoped and records structured official dates. The current four active records are GA-13 (passed away 2026-04-22; special election 2026-07-28), FL-20 (resigned 2026-04-21), TX-23 (resigned 2026-04-14), and CA-14 (resigned 2026-04-14).
- Post-review correction reopened the milestone: the Clerk parser recognized `Special Election` but not `Special General Election`, causing CA-14 former-member overcapture and loss of the scheduled election date/type.
- Existing normalized previews are descriptive rather than directly insertable, and multi-source conclusions require normalized evidence-to-artifact junctions instead of one arbitrary source field.
- Replay must derive its expected detail set and pagination from the Congress list artifacts so a self-consistently edited manifest cannot hide an omitted required detail.
- A follow-up review found member previews retained the parser's date-only batch value instead of the exact detail artifact retrieval timestamp; the seed preview must replace all member source provenance from the matching snapshot-artifact row.
- The 481 replay details are House-term candidates from the list response, not all current 119th-House members; 437 normalize into the current roster and 44 lack a 119th-House term.

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
- Fresh immutable batch: `house-119-20260713T011722Z`, completed `2026-07-13T01:17:45.485100+00:00`, age zero days and fresh under the seven-day policy.
- Exact House universe: 435 voting seats, five delegates, one resident commissioner, 441 total, zero unknown roles.
- Identity reconciliation: 437 cross-source-confirmed members, zero primary-only, zero source conflicts, zero official or production duplicate Bioguide IDs.
- Manifest/checksum/orphan/stale/currentMember disagreement and identity-conflict failure paths have deterministic coverage.
- Snapshot/rollback schema now includes snapshot and artifact tables; service/seat evidence is unique within snapshot and deletable by snapshot ID without blocking later historical snapshots.
- Final corrected combined suite: 74 passed in 9.75 seconds.
- Corrected Clerk contract: CA-14 now parses Eric Swalwell, resigned 2026-04-14, `special_general`, election 2026-08-18; GA-13, FL-20, and TX-23 effective dates remain unchanged.
- Manifest-authoritative replay independently derived offsets 0/250/500, termination, 537 list records, 481 House-term candidate detail files, successful statuses, exact URL/path agreement, and exactly one House plus one Clerk artifact; 437 details normalized into the current 119th-House roster and 44 were skipped for lacking that term.
- Committed normalized seed previews: one snapshot, 486 artifacts, 437 member-service rows, 441 seat-status rows, 874 member-artifact links, and 882 seat-artifact links; zero unmatched or noninsertable rows.
- Preview validation passed by comparing exact insertable columns to migration `0014`, checking required values and enums, and resolving every evidence/artifact target without reading raw sources.
- Final combined metadata/readiness/ZIP suite: 82 passed; eight milestone JSON files validated; Python compilation and `git diff --check` passed.
- Final read-only ZIP postcheck: zero mapping rows, zero unique ZIPs, zero auto-select eligibility, migration not applied, and seed not loaded.
- All six proposed tables (the four core tables plus two evidence-artifact junctions) remain absent; both public ZIP routes still read `zip_district_map`; the multi-row flag remains absent/not enabled.
- Exact member-artifact provenance correction: all 437 member rows now copy source name/type/URL, SHA-256, and full timezone-aware retrieval timestamp from their own allowlisted detail artifact; A000055 is `2026-07-13T01:17:24.356968+00:00` in both rows.
- Provenance validation passed for all rows and deterministically rejected both a changed timestamp and a date-only value.
- Corrected replay terminology reports 481 House-term candidate detail artifacts, 437 normalized current-119th-House members, and 44 skipped details without that term; the normalized roster and all readiness counts are unchanged.
- Final provenance-correction validation: 82 combined tests passed, eight JSON files validated, read-only ZIP postcheck passed with zero rows/eligibility, all six proposed tables remained absent, routes/flag remained unchanged, and `git diff --check` passed.

## Production Writes

- Performed: no.
- Scope/expected/actual effects: official-source reads, local ignored files, production SELECTs, and repository artifacts only.

## Rollback Paths

- Revert branch files and delete ignored local artifacts. No database rollback is applicable because migration/application and data writes are forbidden.

## Blockers

- None currently. Four production `in_office=true` rows conflict with current official vacancy evidence and must not be mutated in this milestone.

## Final Reconciliation

- Definition of done satisfied: yes; exact detail-artifact provenance, failure validation, corrected replay terminology, regenerated artifacts, no-write checks, and existing draft PR #87 delivery are complete.
- Remaining limitations: Congress service dates are year precision; exact vacancy dates exist only where explicitly displayed; four production rows remain stale until an authorized later write.
- Recommended next step: Current House member metadata schema application and bounded seed V1 because official sources reconcile with zero seat conflicts and the additive schema contract passes; do not switch ZIP routes.
