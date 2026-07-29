# Milestone Plan: Full-Record Issue Interpretation Contract V1

## Intent

- Immediate task: define and validate the deterministic contract that separates
  semantic quality from review scope, completion, and public claim authority.
- Larger-goal alignment: make benchmark-proven interpretation safely expandable
  across a representative's complete defined issue record before the next
  frontend implementation pass.

## Outcome

- User-visible or operational result: a closed methodology, schema, validator,
  truthful Foushee Justice review-state record, and frontend-facing state
  contract. This milestone does not change runtime behavior.

## Scope And Boundaries

- In scope: review-friendly action rules, complete action accounting, episode
  completion, full-record synthesis gates, benchmark scope, current-state
  documentation, deterministic validation, and terminology governance.
- Out of scope: new Justice interpretation, accepted Semantic IR outcome
  changes, production or registry access, publication mutation, API or React
  work, deployment, and merge.
- Files/systems likely touched: `docs/methodology/`, a new
  `docs/editorial/full_record_reviews/` record, directly affected current
  contracts, semantic validation scripts, and focused backend tests.

## Decision Envelope

- Codex may decide and execute: closed schema structure, deterministic derived
  validation, focused fixtures, exact documentation placement, and proportional
  repository-only validation.
- Explicit approval required for: accepted semantic-reference changes,
  historical receipt rewrites, active publication or registry changes,
  production access, deployment, and merge.

## Definition Of Done

- [x] Four independent axes and review-friendly action criteria are authoritative
  and machine-readable.
- [x] Full action-accounting, episode-completion, synthesis-eligibility, and
  benchmark-role contracts are implemented.
- [x] F000477 Justice 119 is truthfully classified without changing historical
  publication facts.
- [x] Frontend-facing fields and labels are specified without runtime changes.
- [x] Required invariants, byte stability, JSON/schema, and terminology are
  tested.
- [x] Semantic and documentation validation, JSON parsing, and `git diff
  --check` pass.
- [x] Complete diff and behavior are inspected.
- [x] One cohesive commit is pushed and draft PR #120 is opened.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit:
  `codex/full-record-issue-interpretation-contract-v1` from
  `80208ab7050f1af6543185175c68219c5b59ecee`.
- Production/deployment state, if relevant: the successful 2026-07-29 Foushee
  Justice activation is immutable historical truth; this milestone performs no
  production action.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: none.

## Implementation Sequence

1. Reconcile governing semantic, presentation, workflow, benchmark, receipt,
   publication, and incident evidence.
2. Add the methodology, closed schema, and truthful current review-state record.
3. Add deterministic validator, property tests, byte-stability checks, and
   terminology governance; integrate them into the semantic loop.
4. Update only directly affected current-state, workflow, presentation, and
   frontend-contract documentation.
5. Run all required validation, inspect the complete diff, reconcile this plan,
   then commit, push, and open a draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The requested base was initially absent locally. Fetching origin established
  that `origin/main` is exactly `80208ab...` and includes the successful
  publication-history commits.
- The active seven-action/five-episode presentation is publication-active and
  semantically valid within its approved bounded sample. Its immutable approval
  limitation explicitly says it is not the complete Justice record.

## Decisions And Rationale

- Review completion will describe accounting of the declared universe. A
  benchmark sample can therefore be complete within that sample while remaining
  categorically ineligible for a full-record claim.
- Full-record eligibility will be derived from scope, accounting, episode,
  semantic-validation, and human-review gates rather than stored as
  self-authorizing metadata.
- The Foushee state record will preserve three distinct truths: historical
  publication, semantic validity within the reviewed sample, and future
  full-record eligibility.

## Deviations Or Corrections

- The current review packet predates the separately authorized successful
  activation and truthfully records publication inactive at review time.
  Current authoritative contracts were updated to add the later activation
  truth without rewriting that historical packet or its receipts.

## Validation Results

- `python scripts/run_editorial_pipeline.py validate --tier semantic --json`:
  passed all seven coordinated checks, including both Draft-07 schemas, all 16
  accepted semantic references, the new manifest validator, focused tests,
  documentation governance, and terminology governance.
- `python -m unittest backend.tests.test_full_record_issue_interpretation`:
  15 tests passed.
- All changed JSON parsed; Python compilation and `git diff --check` passed.
- Protected accepted corpora, gold dossiers/maps, action-source contract,
  approval and publication artifacts, successful receipt, and incident record
  matched their committed SHA-256 values and have no diff.

## Production Writes

- Performed: no
- Scope: repository-only.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the cohesive repository commit. No production, registry, publication,
  migration, or deployment rollback is applicable.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes. The contract, schema, validator,
  machine-readable current state, governance, tests, and directly affected
  documentation are complete in one cohesive draft PR.
- Remaining limitations: this milestone defines the contract but does not
  reinterpret the remaining Foushee Justice record or implement Frontend Pass A.
- Recommended next step: full-record methodology merge-gate review of draft PR
  #120.
