# Foushee Justice Semantic IR M5

## Intent and outcome

Construct, compile, review, freeze, and provisionally implement the complete
37-action / 32-episode Foushee Justice 119th-Congress Semantic IR candidate.
Deliver one local unpushed commit and a verified external review package.

## Scope and boundaries

- Use the accepted action and episode implementations as governed inputs.
- Use the canonical Semantic IR compiler and pipeline without semantic-rule changes.
- Keep public prose, accepted-reference, canonical, runtime, persistence,
  publication, network, and database state unchanged.
- Preserve the pre-existing untracked M4B ZIP and exclude it from this milestone.

## Decision envelope

Families and traits must be member-neutral, mechanism-specific, and evidence-bound.
Ambiguity and source constraints remain explicit. Up to two structured-input
correction cycles are permitted. A compiler incapability requiring a universal
method change is a blocker.

## Definition of done

- Exact 37-action accounting and 32 implemented episodes.
- Canonical deterministic compilation and pipeline parity.
- Independent reviews, freeze, benchmark audit, sampling, provisional bundle,
  independent verification, risk/calibration continuity, dossier, and parity.
- Targeted and broad safe offline validation passes.
- One local unpushed commit and one verified external review ZIP.

## Baseline

- Branch: `codex/foushee-justice-action-interpretation-candidates-v1`
- HEAD: `20471c9975573122eb6077b4b6c9a17e025af07a`
- Parent: `fab56892a5b0c2aa8ac7a889802b9dd5f9697dc7`
- Cached `origin/main`: `24a2bcb37347f74c6c40261930024e85676cd8d0`

## Sequence and progress

- [x] Preflight and prior gates.
- [x] Structured projection, families, traits, constraints, and compiler input.
- [x] Reviews, corrections, freeze, and post-freeze audit.
- [x] Provisional implementation and independent verification.
- [x] Final validation, diff review, local commit, and review package.

## Discoveries and decisions

- Rolls 155 and 278 remain non-accepted primary-episode controls. They travel
  through canonical source constraints and method boundaries and receive
  explicit universe-level non-proposition accounting outside the unmodified
  compiler's accepted-action accounting.
- The M4B ZIP in the artifact directory predates M5 and remains user-owned.

## Validation, writes, rollback, blockers, reconciliation

The first direct builder invocation exposed that the script execution path did
not contain the repository root; the builder now inserts its resolved root
before importing the canonical pipeline. No artifacts were written by the
failed invocation. The direct verifier exposed the same script-path issue and
received the same technical correction. A combined regression invocation also
hit the sandbox's Windows temporary-directory permission restriction; it will
be rerun with a repository-local temporary root. Validation results and later
corrections will be recorded as execution proceeds.
The supported broad safe offline suite passed 1,189 tests with four disclosed
baseline-incompatible cases deselected. The unfiltered 1,244-test run passed
1,194 and failed only on database integration against the invalid sentinel,
missing local source fixtures, and those baseline cases. Targeted M5 tests are
5/5, the Semantic IR/full-record regression is 52/52, prior gates pass, Ruff and
formatting pass, Python compilation passes, JSON and schema checks pass, the
credential scan is clean, and `git diff --check` passes.
No production writes are authorized or performed. Rollback is deletion/revert
of this milestone's local commit and external package only. No blockers are
currently known. Final reconciliation: the detached candidate satisfies the
37-action / 32-episode accounting, canonical compilation, review, freeze,
implementation, verifier, risk/calibration, parity, and isolation contracts;
the local commit and its external package complete the milestone without push,
publication, persistence, network, or database activity.
