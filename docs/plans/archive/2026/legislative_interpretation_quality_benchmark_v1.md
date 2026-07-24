# Milestone Plan: Legislative Interpretation Quality Benchmark V1

## Intent

- Immediate task: define and exercise a reproducible quality standard for measure, vote, and issue-level legislative interpretation.
- Larger-goal alignment: make a representative's recorded legislative choices understandable without requiring procedural expertise, while preserving civic-integrity boundaries and receipts.

## Outcome

- Operational result: a deterministic 48-roll-call benchmark, rubric/scorer, eight issue-synthesis slices, pipeline audit, dossier contract, review protocol, and bounded next-milestone recommendation.

## Scope And Boundaries

- In scope: local benchmark assembly from repository-held reviewed artifacts, deterministic scoring/validation, design documentation, tests, and a review packet.
- Out of scope: production reads or writes, schema/migrations, interpretation imports, API/frontend/runtime changes, coverage expansion, paid model calls, and merge.
- Files/systems likely touched: `backend/scripts`, focused `backend/tests`, and benchmark/design/plan/review documentation.

## Decision Envelope

- Codex may decide and execute: benchmark sampling, non-production schemas, rubric mechanics, deterministic audit metrics, documentation structure, and tests.
- Explicit approval required for: production access, civic-semantic changes, schema/runtime/API/frontend changes, treating candidates as approved gold, or merge.

## Definition Of Done

- [x] At least 48 unique roll calls cover the requested benchmark cohorts and eight issue domains.
- [x] Measure, vote, public-render, and issue-synthesis quality are evaluated separately.
- [x] Rubric, fatal defects, comprehension protocol, source dossier, reuse hierarchy, and review statuses are deterministic and documented.
- [x] Existing-system pipeline and public-copy information loss are inventoried.
- [x] Tests/build/validation recorded.
- [x] Review packet and machine-readable scorecard generated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/legislative-interpretation-quality-benchmark-v1` from `main` at `6b218070a7c93a1f979eacc863766887e40151e4`.
- Production/deployment state: not queried; no production access is needed or authorized.
- Tracked working tree: clean at baseline.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`; preserve and exclude.

## Implementation Sequence

1. Map source ingestion, classification, interpretation storage/review, aggregation, and public rendering.
2. Build a deterministic stratified corpus from repository-held reviewed interpretation artifacts.
3. Implement schema validation, rubric scoring, fatal overrides, comprehension gates, and aggregate analysis.
4. Define dossier, quality, public-copy, issue-synthesis, reuse, and human-review contracts.
5. Generate the JSON benchmark and JSON/Markdown review packets.
6. Run focused and existing relevant validation; reconcile scope and publish a draft PR.

## Progress Checklist

- [x] Discovery started.
- [x] Implementation.
- [x] Validation.
- [x] Documentation.
- [x] Commit/PR readiness.

## Discoveries

- The baseline is exactly the requested commit and unrelated artifacts are untracked.
- Older reviewed records contain deterministic title-restatement language; later gold-slice packets contain substantially more mechanism, practical-effect, and lifecycle detail.
- `vote_interpretations` holds useful reviewed evidence fields, while `publicCopyThemes.mjs` intentionally prohibits those raw fields from top-level synthesis and uses curated or generic themes.
- The safety boundary correctly prevents uncontrolled leakage but can replace distinct policy choices with abstract domain/facet language.
- GitHub CLI is installed, but its stored credential is expired; publication will require reauthentication if no connected-app path is available.
- The final corpus has 32 House substantive, 8 Senate substantive, and 8 explicit control cases (36 House and 12 Senate after controls), with 20 amendments, 18 final-passage votes, and all eight domains represented.
- Corrected domain composition preserves all eight grounded domains and reports one additional `UNRESOLVED` case rather than assigning it by index.
- Automated structural diagnostics average 39.6/48 for stored fields, 33.8 for the `public_field_availability_proxy`, and 40.0 for candidate machine drafts. These are not verified editorial-quality judgments; human editorial scoring is pending.
- Dossier field completeness is 40.0%, claim-map structural completeness is 100.0%, and four-question comprehension answerability is 70.8%.
- The broadest deterministic gaps are policy baseline (48/48), affected entities (48/48), and documented credible alternatives (48/48); this explains why even otherwise strong reviewed prose remains generic.

## Decisions And Rationale

- Benchmark candidates remain explicitly `candidate`, not editorially approved gold.
- Ambiguous controls use explicit insufficiency markers instead of fabricated policy effects.
- Cohort counts are independent from chamber counts: 32 House substantive cases, 8 Senate substantive cases, and 8 ambiguity controls split across chambers.
- Stored fields, the `public_field_availability_proxy`, and candidate machine drafts receive separate automated structural/heuristic diagnostics. `strong` means strong under that automated rubric only.
- Source-map presence is reported separately from human-verified factual support and never treated as proof that a source supports a claim.
- Domain assignment uses only explicit or deterministically grounded signals; otherwise the case is `UNRESOLVED`.
- V1 issue-synthesis slices are synthetic fixtures with no real-person attribution because the selected checked-in rows do not establish one named member's position across every slice.
- Measure reuse remains a noncanonical grouping heuristic, not a canonical dossier count.

## Deviations Or Corrections

- Initial fatal-defect detection treated negated caveats such as “not final passage” as positive confusion. The detector now evaluates asserted decision/effect/outcome text and has an adversarial regression test.
- Sandbox pytest runs could execute assertions but could not create/clean `tmp_path` directories. The combined suite was rerun outside the sandbox and passed.
- Integrity correction removed index-based domain assignment, replaced unsupported named slices, relabeled automated diagnostics and the public-field proxy, and qualified reuse as heuristic. The 48-case sample and substantive recommendation remain unchanged.

## Validation Results

- Focused benchmark suite after integrity corrections: `29 passed`.
- Combined relevant backend suite (benchmark, interpretation, manual import validation, positions/fingerprint/summary reads, summary cache, source packets): `80 passed`.
- Full frontend helper suite including issue overview, public-copy themes, issue readiness, evidence grouping, and golden fixture: `84 passed`.
- Python compilation: passed for both scripts and the focused test module.
- JSON parsing: passed for benchmark, rubric, and scorecard.
- Deterministic regeneration SHA-256 equality: passed.
- `git diff --check`: passed.
- No frontend build was required because no frontend/runtime files changed; golden-render helper behavior was exercised without changing output.

## Production Writes

- Performed: no.
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert only the benchmark scripts, tests, and documentation added on this branch; no runtime or data rollback is required.

## Blockers

- GitHub CLI authentication is expired. Commit preparation is complete; push and draft PR require reauthentication or a connected GitHub app path.

## Final Reconciliation

- Definition of done satisfied: local analytical/design milestone and validation are complete; publication remains subject to GitHub authentication.
- Remaining limitations: candidates require bounded human source verification before `gold_benchmark` status; structural source-map completeness is not editorial source verification; the benchmark intentionally does not run external-user research.
- Recommended next step: Valerie Foushee / Economy & Taxes Interpretation Quality V2, implementing one dossier → vote meaning → approved public claim → issue synthesis → rendered comprehension slice end to end.
