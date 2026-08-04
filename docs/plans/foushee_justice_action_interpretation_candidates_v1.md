# Milestone Plan: Foushee Justice Action-Interpretation Candidates V1

## Intent

- Produce a source-bound, blind, non-authorizing candidate interpretation for each of the 37 externally authorized actions.
- Freeze and evaluate the complete batch for generalization review without changing canonical full-record, Semantic IR, persistence, or publication state.

## Outcome

- A detached, schema-validated JSON/Markdown/parity bundle supporting the mandatory M3A human generalization decision.

## Scope And Boundaries

- In scope: authority/readiness preflight; closed per-action evidence maps and packets; primary candidates; adversarial review; one correction cycle; freeze; post-freeze benchmark comparison; deterministic random/challenge sampling; review dossier and empty decision template; validation and one local snapshot commit.
- Out of scope: acceptance, approval receipts, canonical review-state edits, episodes, propositions, Semantic IR, synthesis, public copy, persistence, publication, deployment, push, PR, and merge.
- Files touched: a detached `docs/editorial/full_record_reviews/interpretation_candidates/` tree, focused builder/validator code and tests, and this plan.

## Decision Envelope

- Codex may make evidence-bounded candidate and review judgments under the supplied neutral methodology.
- Human authority is required for `generalization_pass`, `global_revision_required`, or `generalization_rejected`, and for every downstream milestone.

## Definition Of Done

- [x] Exactly 37 evidence maps, isolated packets, primary candidates, reviews, and frozen final candidates validate.
- [x] Original/revised provenance and field-level corrections are preserved.
- [x] Accepted benchmark content was accessed only after the final batch was frozen and could not modify it.
- [x] Random/challenge selection is reproducible and benchmark-excluding where required.
- [x] Markdown is deterministically generated and substantive JSON/Markdown parity passes.
- [x] Candidate artifacts remain detached and unselectable by current/public/persistence paths.
- [x] Required focused regressions, offline tests, secret scan, parsing, and diff checks pass; unrelated broad-suite baseline failures are recorded separately.
- [x] One local non-authorizing snapshot commit is created; no push or PR occurs.

## Baseline

- Branch: `codex/foushee-justice-action-interpretation-candidates-v1`.
- Base/HEAD/origin-main at preflight: `24a2bcb37347f74c6c40261930024e85676cd8d0`.
- Worktree entering milestone: clean.
- Production/deployment: untouched; offline invalid database sentinel required.

## Candidate Architecture And Input Isolation

- Build a content-addressed evidence map and worker packet per action from only M2-governed neutral projections, eligible operative files, exact stage/member action, and applicable scope limits.
- Record the full allowlist and digest in each packet; forbid party, generic bill metadata, benchmark meanings, public conclusions, Semantic IR, episodes, and other candidates.
- Generate and review each record against its own packet plus the shared neutral prompt contract. Logical roles remain separated by artifacts and phase gates; agent agreement is never authority.
- Preserve difficult evidence as an explicit limitation or `no_safe_candidate`; never drop an action.

## Freeze, Benchmark, And Sampling

- Freeze the validated post-correction batch by subject SHA-256 before opening the accepted seven-action reference.
- Benchmark comparison is read-only evaluation and cannot regenerate candidates.
- Derive the sample seed from the frozen subject hash, M2 artifact hash, and fixed audit label; sample 12 of 30 non-benchmark actions without replacement using the versioned deterministic algorithm.
- Build the separate deduplicated challenge set with all mandated inclusion reasons.

## Implementation Sequence

1. Complete hard preflight and create this plan.
2. Scaffold closed schemas, builder/renderer/verifier, and focused tests.
3. Generate evidence maps and isolated worker packets; audit forbidden inputs and hashes.
4. Author primary candidates from per-action governed inputs only; adversarially review all 37; apply one bounded correction cycle.
5. Freeze and validate the final batch, then perform benchmark comparison and deterministic sampling.
6. Generate dossier, parity manifest, decision template, and artifact index.
7. Run focused, semantic, public-boundary, offline, and repository validation; inspect diff and behavior.
8. Create one local snapshot commit and stop for human decision.

## Progress Checklist

- [x] Repository/authority preflight
- [x] Planning
- [x] Evidence mapping
- [x] Candidate generation and adversarial review
- [x] Freeze, benchmark, and sampling
- [x] Bundle generation
- [x] Validation and final reconciliation
- [x] Local snapshot commit

## Discoveries

- The initially checked-out M2 topic branch was not the requested baseline; the clean worktree was switched to a new branch at the exact merged baseline.
- Direct execution of `offline_database_preflight.py` is not its supported entry point; the fail-closed runner performed the valid preflight with all ordinary database targets set to the invalid sentinel.
- Adversarial review found an internal raw-XML title mismatch for S. 4465 and insufficient isolation of H.R. 8800's complete final passed package; these became one ambiguous and one no-safe candidate.
- Post-freeze comparison found roll 299 broader than the accepted exception-aware reference. This evaluation did not alter the frozen candidate.

## Decisions And Rationale

- Candidate outputs live under a detached documentation root and receive no runtime loader or catalog registration.
- Structured JSON remains canonical; Markdown is generated and parity-verified rather than independently authored.

## Deviations Or Corrections

- A first direct legacy test run failed because the managed Windows sandbox denied Python-created temporary directories. The identical focused set passed 65/65 through the repository's escalated offline runner; no test rule was weakened.

## Validation Results

- Preflight: M1 authority pass (37 actions); M2 readiness pass (37 ready, 0 blocked, artifact SHA `62a33bcbb1c4eecc267f33be1740c7ee4db59e617a150b6d837c1aa30930bd91`); deterministic M2 builder check pass; offline database preflight pass.
- Candidate validator: pass; 37 records, 12 random selections, 6 challenge actions, 2 corrections, parity pass.
- Candidate unit tests: 11/11 pass.
- Focused full-record/source-readiness/authority/public-catalog/editorial-pipeline/manual-interpretation/candidate-evidence regressions: 65/65 pass through the fail-closed offline runner.
- Editorial semantic pipeline: 7 coordinated checks pass.
- Full-record artifact validator and terminology governance: pass.
- Complete offline backend suite: 1,063 passed, 33 skipped, 17 unrelated baseline failures. Failures are confined to absent local House/Senate source caches, two existing editorial API fixture expectations, and an existing ZIP source-manifest byte-hash mismatch; changed M3A files are not involved.
- Python compilation, JSON parsing, credential-pattern scan, and `git diff --check`: pass.

## Production Writes

- Performed: no.
- Expected/actual effects: none.

## Rollback Paths

- All milestone outputs are new detached files on an unpushed local branch; no production rollback is applicable.

## Blockers

- None at preflight.

## Final Reconciliation

- Definition of done satisfied: yes, subject to the authorized local snapshot commit.
- Remaining limitations: candidate methods remain non-authorizing; roll 155 is ambiguous, roll 278 has no safe candidate, and roll 299 showed a major post-freeze benchmark breadth mismatch.
- Required next step after completion: mandatory human M3A generalization decision; do not begin M3B.
