# Milestone Plan: Current-Congress Freshness And Automated Ingestion

## Intent

- Immediate task: refresh production with safely supported 119th Congress House and Senate activity through the latest available official source date.
- Larger-goal alignment: keep the accountability profile current while preserving source-grounded, deterministic, non-persuasive civic methodology.

## Outcome

- Production roll-call identity is session-aware.
- Supported 2026 House and Senate vote facts, contexts, classifications, and conservative interpretation placeholders are imported.
- Derived precomputed output windows are refreshed so public position/evidence endpoints can include the new current-Congress rows.
- Unsupported categories remain deferred rather than guessed.
- A repeatable bounded refresh command exists for future current-Congress updates.

## Scope And Boundaries

- In scope: 119th Congress, 2025 and 2026 through the inspected source cutoff, House and Senate, supported fact rows, deterministic classifications, conservative `insufficient_evidence` interpretation placeholders.
- Out of scope: prior Congresses, PN/treaty/executive semantics beyond current support, substantive interpretation expansion, methodology changes, support/opposition/readiness/alignment changes.
- Production writes were permitted only under the milestone decision envelope after rollback artifacts and preflight validation.

## Decision Envelope

- Codex could apply the bounded session-aware identity migration because every existing roll call mapped unambiguously and rollback existed.
- Codex could perform the bounded 2026 refresh write because preflight reproduced the expected table effects and planned no support/opposition/readiness/alignment methodology change.
- Codex had to stop on ambiguous source meaning, unsupported civic category, incomplete rollback, or material preflight/runtime divergence.

## Definition Of Done

- [x] Production coverage audited against official House/Senate roll calls through source cutoff.
- [x] Roll-call identity made session-aware.
- [x] Existing 2025 IDs and evidence remained intact.
- [x] Missing supported 2026 vote facts fetched/cached and imported.
- [x] Amendment, final-passage, procedural, nomination, treaty distinctions preserved by current adapters/classifiers.
- [x] Deterministic classifications generated where current rules support them.
- [x] Bounded conservative interpretation placeholders imported where current rules apply.
- [x] Unsupported categories deferred explicitly.
- [x] Repeatable command/workflow added.
- [x] Idempotency proves zero additional writes on rerun.
- [x] Derived precompute outputs refreshed and idempotency validated.
- [x] Review packet documents baseline, writes, validation, cadence, and backlog.
- [x] Tests/build/production validation pass.
- [ ] PR opened, checks pass, merged, deployment verified.

## Baseline

- Base branch: `main`.
- Base commit: `1f5e145ec69139dba6b2ff1eccbc65db5fa04522`.
- Known unrelated untracked artifacts preserved: chamber filtering audit, frontend grounding bundle, pytest temp directories.
- Pre-migration production counts:
  - bills: 267
  - roll_calls: 624
  - votes_cast: 175,264
  - vote_contexts: 175,264
  - vote_classifications: 475
  - vote_interpretations: 123
  - support_position non-null: 97
  - oppose_position non-null: 97

## Implementation Sequence

1. Audited existing source, fact-import, classification, and interpretation tooling.
2. Ran production read-only coverage baseline and official-source availability audit.
3. Identified roll-call identity collision across 119th Congress sessions.
4. Added migration `0012_roll_call_session_identity.sql`.
5. Updated Senate fact/amendment import lookup and conflict paths to use session-aware roll keys.
6. Added repeatable `current_congress_refresh` orchestration CLI.
7. Generated rollback artifacts before production writes.
8. Applied session-aware production migration after gates passed.
9. Fetched/cached 2026 House and Senate official sources.
10. Ran dry-run, corrected member alias/missing-legislator handling, and imported the bounded supported package.
11. Validated production counts, session overlap, support/opposition invariants, and idempotency.
12. Found public API freshness still hidden by stale fingerprint windows.
13. Added and ran a bounded derived precompute refresh for the latest window.

## Progress Checklist

- [x] Base confirmed and branch created.
- [x] Tooling audit.
- [x] Production/source baseline.
- [x] Session-aware identity implementation.
- [x] Migration preflight/rollback.
- [x] Production migration and post-validation.
- [x] Refresh preflight/rollback.
- [x] Production refresh import and post-validation.
- [x] Idempotency validation.
- [x] Final tests and diff checks.
- [ ] Commit, PR, merge, deployment verification.

## Discoveries

- Official House and Senate sources restart roll-call numbering by session within a Congress.
- Existing production identity used `(chamber, congress, rollcall_number)` even though migration `0008` had added `session`.
- 2026 House/Senate rolls would collide with valid 2025 rolls without a session-aware key.
- Senate 2026 XML used LIS `S419` for Markwayne Mullin while production uses Bioguide `M001190`; the refresh records this as a deterministic alias.
- Four current officials were absent from production before the 2026 refresh and were inserted from official 2026 member/vote sources.

## Decisions And Rationale

- Canonical roll-call identity: `(chamber, congress, session, rollcall_number)`.
- Rationale: chamber and Congress are necessary but insufficient; official House/Senate roll numbers restart by session, and `session` is the source-faithful identifier already represented in the schema.
- The refresh command imports only source-supported current-Congress rows and keeps all generated interpretation rows `insufficient_evidence` with null support/oppose positions unless existing deterministic interpretation rules prove a countable meaning.
- Local source cache directories are operational inputs, not PR artifacts.

## Deviations Or Corrections

- The milestone initially stopped at a schema blocker. After user authorization, the blocker packet was updated into the completed implementation record.
- A first production write attempt timed out and left a stale backend/transaction concern. The approved termination/check showed no remaining idle transaction, no locks, and no partial committed write from that attempt before the successful retry.
- The retry used the same bounded approval gate and completed with expected table effects.

## Validation Results

- Migration preflight found no session-aware duplicate keys and all existing 2025 rows mapped unambiguously.
- Post-migration counts matched baseline exactly.
- Refresh dry-run planned:
  - bills: 169
  - legislators: 4
  - roll_calls: 282
  - votes_cast: 99,725
  - vote_contexts: 99,725
  - vote_classifications: 282
  - vote_interpretations: 282
- Successful import inserted the same counts.
- Post-import production counts:
  - legislators: 552
  - bills: 436
  - roll_calls: 906
  - votes_cast: 274,989
  - vote_contexts: 274,989
  - vote_classifications: 757
  - vote_interpretations: 405
  - support_position non-null: 97
  - oppose_position non-null: 97
- Session coverage after import:
  - House session 1 / 2025: 339 rolls, roll 3-362
  - House session 2 / 2026: 216 rolls, roll 2-222
  - Senate session 1 / 2025: 285 rolls, roll 1-618
  - Senate session 2 / 2026: 66 rolls, roll 4-175
- Idempotency dry-run after import planned zero additional writes across all refresh tables.
- Derived precompute refresh inserted/updated 4,416 fingerprints, 48 chamber medians, 552 drift rows, and 552 summaries.
- Derived precompute idempotency rerun changed zero rows.
- Final targeted backend tests passed: 32 passed.
- Final post-import idempotency dry-run passed with zero planned writes.
- Final production read-only invariant check passed.
- `git diff --check` passed with normal Windows CRLF notices.

## Production Writes

- Applied additive roll-call identity migration:
  - backfilled session values;
  - added session validity check;
  - replaced old roll-call uniqueness with session-aware uniqueness;
  - preserved existing roll_call IDs.
- Imported 2026 supported refresh rows:
  - bills: 169
  - legislators: 4
  - roll_calls: 282
  - votes_cast: 99,725
  - vote_contexts: 99,725
  - vote_classifications: 282
  - vote_interpretations: 282
- No support/opposition rows changed.
- No readiness/alignment methodology changed.
- Refreshed derived precomputed output rows for window end `2026-06-17`: 4,416 fingerprints, 48 chamber medians, 552 drift rows, and 552 summaries.

## Rollback Paths

- Schema rollback: `docs/review_packets/current_congress_session_identity_rollback.sql`
- Refresh rollback: `docs/review_packets/current_congress_refresh_rollback.sql`
- Derived precompute rollback: `docs/review_packets/current_congress_precompute_rollback.sql`
- Rollback artifacts were generated before the corresponding writes and scoped to the migration or exact session-aware refresh roll keys.

## Blockers

- No current blocker after the session-aware identity migration and refresh import.
- Remaining work is final validation, PR, merge, deployment verification, and public API freshness confirmation after network access is available.

## Final Reconciliation

- The original schema blocker was resolved by making roll-call identity session-aware.
- The bounded refresh imported supported 2026 House/Senate facts and conservative classification/interpretation placeholders.
- Deployment checks remain after PR merge before closing the milestone.
