# Milestone Plan: Foushee Justice 119 Interpretation Source Readiness V1

## Intent

- Mechanically account for interpretation-source readiness across the exact
  M1-authorized 37-action universe.
- Supply a content-addressed, non-authorizing evidence packet for a separately
  authorized M3 interpreter without generating any interpretation.

## Outcome

- A closed Draft-07 contract, deterministic source manifest/artifact/report
  builder, independent verifier, and focused negative tests establish whether
  each approved action has exact official evidence ready for later use.
- The correction pass distinguishes member-action, exact identity/stage, and
  mechanism-bearing operative-content roles and supplies only closed neutral
  projections to a future M3 interpreter.

## Scope And Boundaries

- In scope: M1/V2 artifact bindings, official-source identity and digest
  verification, per-action readiness, FISA scope constraints, current-state
  reconciliation, validation, commit, push, and a draft PR.
- Out of scope: action meaning, direction, episodes, propositions, Semantic IR,
  synthesis, production, persistence, publication, deployment, and merge.
- Likely files: one methodology schema, one source manifest, one JSON artifact,
  one Markdown report, builder/verifier modules, focused tests, and narrow
  current-state/plan indexes.

## Decision Envelope

- Codex may deterministically derive readiness from the approved source
  identities and acquire only already-identified official evidence for the 37
  approved actions.
- New universe membership, source-family policy, semantic decisions, production
  access, publication, deployment, and merge require separate authorization.

## Definition Of Done

- [x] Exactly 37 approved actions have one readiness record and no outside action.
- [x] Source digests, exact-action bindings, stages, constraints, and aggregate
  counts independently verify under a closed schema.
- [x] No semantic, benchmark-conclusion, episode, proposition, synthesis, party,
  production, or publication input enters any packet.
- [x] Every action has independently verified stage-compatible operative
  content; identity-only evidence cannot satisfy the operative-content gate.
- [x] Offline backend validation fails before a subprocess when an inherited
  database target is remote.
- [x] Targeted, governance, deterministic, compilation, and broad backend
  validation is recorded.
- [x] Final diff is scoped and prepared for the existing draft PR without merge.

## Baseline

- Branch/base commit: `codex/foushee-justice-interpretation-source-readiness-v1`
  from `5c330b31293edb148e2023bbc8daddbb023e8f92`.
- M1 verifier: passed for 37 actions and the expected manifest, action-set,
  universe-subject, and authority-receipt digests.
- Production/deployment state: no write or deployment was authorized or
  performed. An initial broad test invocation inadvertently inherited the
  repository's remote `DATABASE_URL` and performed read-only API database
  access before the environment issue was identified; all subsequent broad
  validation forced an invalid URL.
- Tracked working tree: clean at milestone start.

## Implementation Sequence

1. Bind the approved M1 universe to a governed official-source manifest.
2. Build the closed M2 artifact and compact report deterministically.
3. Independently validate schemas, identities, digests, readiness, leakage, and
   FISA constraints with tamper tests.
4. Reconcile current state, run the complete requested validation, inspect the
   diff, and deliver a draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- V2 binds all 37 approved actions to one Clerk vote source and at least one
  exact-action source; the approved set uses 48 exact-action bindings and
  currently reports no source gaps.
- Ignored acquisition caches are not governed repository evidence. M2 therefore
  needs governed projections and/or content-addressed official files that the
  repository verifier can validate without production access.
- The reviewed M2 head overstated readiness for 21 actions whose only
  exact-action source was a title/policy-area bill projection. Three preserved
  `/v3/bill` payloads also contain sponsor, cosponsor, and party metadata.
- Official Congress action lists resolved one exact House action for each of the
  21 gaps. Twenty House bills have action-date-matched `eh` text; S.331 has an
  enrolled version whose action list proves House passage without amendment.

## Decisions And Rationale

- Keep member-action evidence distinct from exact-action interpretation-input
  evidence and derive readiness from closed criteria with deterministic blocker
  precedence.
- Split exact-action evidence into identity/stage and operative-content roles.
  Bind raw official bytes separately from closed neutral M3 projections.
- Preserve generic bill metadata only as explicitly M3-ineligible raw
  provenance.
- Use the reusable offline database preflight runner for every broad backend
  test; disposable integration requires an explicit opt-in and loopback target.
- Treat M2 as detached and non-authorizing; it does not mutate the approved V2
  universe or seven-action benchmark.

## Deviations Or Corrections

- A failed local-main switch briefly left the checkout on the M1 source branch;
  its local pointer was restored exactly to the unchanged remote head before M2
  work began. No repository file or remote branch changed.
- The first broad backend suite inherited a remote database URL loaded from the
  repository environment and exercised read-only API queries. This exceeded
  the milestone's production-access boundary. No write-capable command was
  invoked and no production write occurred. The run was stopped from further
  DB use; subsequent broad and baseline comparisons explicitly used the invalid
  URL `postgresql://invalid`.
- A detached-baseline full-suite comparison was invalidated by Windows pytest
  temporary-directory permissions. The exact three branch failures were then
  rerun directly at baseline and reproduced 3/3, establishing that they are not
  caused by M2.
- The correction pass replaces the accepted-but-insufficient 37/37 result with
  a newly derived result. Readiness was not preserved as a target; it returned
  to 37/37 only after all 21 identity-only gaps acquired and validated exact
  action records plus stage-compatible operative content.

## Validation Results

- M1 authority verifier: passed, 37 actions and all expected authority digests.
- Corrected M2 verifier and deterministic builder check: passed at 37 ready,
  0 blocked; both closed Draft-07 schemas, governed evidence bytes, raw and
  neutral digests, and current-state identity verified.
- Corrected focused M2 and offline-preflight tests: 26 passed; the dedicated
  offline-preflight file contributed 9 passing tests.
- Existing universe-discovery, full-record, and public-catalog validators:
  passed. Full-record tests: 19 passed. Public-catalog tests: 11 passed. The
  universe-discovery cache-parsing test remains unavailable because its ignored
  House source cache is absent from this checkout.
- Semantic validation: Python corpus validation passed; Draft-07 Node validation
  passed after lockfile-pinned local dependencies were installed; Semantic IR
  tests: 26 passed.
- Directly affected Ruff check/format check, Python compilation, JSON parsing,
  and terminology governance: passed. Repository-wide Ruff still reports the
  pre-existing lint backlog and is not a correction regression.
- Broad backend suite through the fail-closed offline runner: 1051 passed,
  33 skipped, 18 failed. Failures are outside this correction: two existing
  editorial API expectations, missing ignored House/Senate source caches,
  one pre-existing source-manifest byte mismatch, and the initially missing
  local `ajv` dependency (subsequently installed and its focused checks passed).
- Correction-pass network access was limited to official Congress.gov/GovInfo/
  House Clerk source acquisition for the approved 37-action set and the local
  lockfile dependency install. No database access occurred during correction.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: no writes. The broad-suite boundary incident performed
  unintended read-only database access as recorded above.

## Rollback Paths

- All M2 work is isolated on the milestone branch and can be reverted as one
  commit before any merge.

## Blockers

- None identified at preread; repository-local official-source digest proof is
  the implementation gate.

## Final Reconciliation

- Definition of done satisfied: implementation, validation, and scoped delivery
  preparation complete; commit/push and draft-PR metadata update are the
  remaining delivery operations.
- Remaining limitations: three pre-existing broad-suite failures; the recorded
  read-only production-access boundary incident.
- Recommended next step: review the 37-ready/0-blocked M2 packet; do not begin M3
  without separate authorization.
