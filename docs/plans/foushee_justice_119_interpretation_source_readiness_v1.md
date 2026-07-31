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
- [x] Targeted, governance, deterministic, compilation, and broad backend
  validation is recorded.
- [ ] Final diff is scoped and a draft PR is opened without merge.

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
- [ ] Commit/PR readiness

## Discoveries

- V2 binds all 37 approved actions to one Clerk vote source and at least one
  exact-action source; the approved set uses 48 exact-action bindings and
  currently reports no source gaps.
- Ignored acquisition caches are not governed repository evidence. M2 therefore
  needs governed projections and/or content-addressed official files that the
  repository verifier can validate without production access.

## Decisions And Rationale

- Keep member-action evidence distinct from exact-action interpretation-input
  evidence and derive readiness from closed criteria with deterministic blocker
  precedence.
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

## Validation Results

- M1 authority verifier: passed, 37 actions and all expected authority digests.
- M2 verifier and deterministic builder check: passed.
- Focused M2 tests: 13 passed.
- Existing universe discovery/full-record validators and public-review catalog:
  passed; public-review catalog tests: 11 passed.
- Semantic validation tier: 7/7 commands passed.
- Ruff check/format check, Python compilation, JSON parsing, terminology check,
  and `git diff --check`: passed.
- Broad backend suite with database access disabled: 1053 passed, 33 skipped,
  3 failed. All three failures reproduced exactly at the immutable baseline and
  are therefore unrelated baseline failures.

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

- Definition of done satisfied: implementation and validation complete; draft
  PR delivery pending.
- Remaining limitations: three pre-existing broad-suite failures; the recorded
  read-only production-access boundary incident.
- Recommended next step: review the 37-ready/0-blocked M2 packet; do not begin M3
  without separate authorization.
