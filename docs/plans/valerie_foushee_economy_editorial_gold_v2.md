# Milestone Plan: Valerie Foushee Economy & Taxes Editorial Gold V2

## Intent

- Immediate task: Create a source-grounded, reader-first editorial gold-slice proposal for Valerie Foushee's 2025 Economy & Taxes roll-call record, using the existing nine-row batch and keeping two limited-context controls distinct.
- Larger-goal alignment: Establish a reusable human editorial workflow for turning verified legislative evidence into concise civic interpretations without changing product semantics or runtime behavior.

## Outcome

- User-visible or operational result: Five reusable measure dossiers, a nine-roll policy-episode map, a seven-roll interpretation set with one not-voting row, two explicitly limited-context controls, issue synthesis, claim-level source mapping, deterministic review artifacts, and a comprehension-testing protocol ready for human editorial review.

## Scope And Boundaries

- In scope: `docs/interpretation_batches/batch_006_valerie_economy_gold_interpretations.json`; official Congress.gov, House Clerk, and CBO evidence; documentation and deterministic tests for the editorial artifacts.
- Out of scope: Database, schema, migration, production, API, frontend, runtime, counting, alignment, readiness, or deployment changes; production reads or writes; human approval; merge.
- Files/systems likely touched: A new `docs/editorial/valerie_foushee_economy_gold_v2/` bundle, focused backend tests, this active plan, and generated review artifacts.

## Decision Envelope

- Codex may decide and execute: Artifact schema and file layout; source locators; reader-layer copy within the civic-integrity rules; deterministic validation and rendering; assignment of `machine_draft`, `agent_source_checked`, `human_approval_pending`, or `insufficient_evidence` only.
- Explicit approval required for: Any runtime or product-semantics change, production access/write, human-approved or gold-benchmark status, merging the PR, or expanding beyond the named member/domain/rolls.

## Definition Of Done

- [x] Five reusable measure dossiers distinguish measure scope, each roll's procedural/final-passage meaning, later legislative history, and claim-level official evidence.
- [x] Valerie Foushee's actual actions are grounded in checked-in House Clerk records; the one not-voting row is excluded from the six-roll synthesis pattern.
- [x] Seven reader-first interpretation records provide 10-second, 30-second, and 2-minute layers without claiming motive, endorsement, ideology, or automatic policy effects.
- [x] A nine-roll policy-episode map preserves four substantive episodes plus two limited-context controls and explains material improvement over the existing machine drafts.
- [x] Editorial workflow, status constraints, claim/source map, issue-synthesis proposal, and comprehension-testing protocol are documented.
- [x] Deterministic JSON and a human-readable side-by-side review artifact are generated and consistent.
- [x] Focused/backend/frontend validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/valerie-foushee-economy-editorial-gold-v2` at `8b6a690574b91bf5f5d5842979beba12292ff823`.
- Production/deployment state, if relevant: No production access or deployment is permitted or required.
- Tracked working tree: Clean at milestone start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Inventory the existing batch and collect claim-level official evidence for the five measures and nine House roll calls.
2. Author the reusable dossiers, policy-episode map, layered interpretations, synthesis, workflow, source map, and comprehension protocol.
3. Generate and test deterministic JSON/review artifacts; run focused backend and frontend validation.
4. Reconcile the plan, commit only milestone files, push the branch, and open the requested draft PR without merging.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The existing batch contains seven interpreted rolls and two intentionally limited-context controls; House roll 310 records Foushee as not voting and must remain outside the six-vote issue synthesis.
- H.R. 5371 and H.Con.Res. 14 each require separate treatment of two materially different House actions on the same measure.
- The Congressional Record supplies the exact roll 263 instruction: accept the Senate's $8.2 billion WIC level. It is source-grounded but remains nonbinding, procedural, non-counting, and distinct from final funding.
- The Congressional Record identifies all seven roll 180 component amendments. Their mixed effects make one compressed policy-position label unsafe, so the roll remains an ambiguity control.

## Decisions And Rationale

- Use measure dossiers as reusable evidence objects and roll interpretations as separate action-specific objects so later legislative history cannot silently replace what the member voted on.
- Treat automated output only as machine drafts; this milestone produces an agent-source-checked proposal with human editorial scoring and approval still pending.
- Check in a bounded House Clerk field snapshot keyed by Foushee's bioguide ID, while retaining each canonical XML URL, so every named action is directly reviewable without committing large source documents.
- Count six substantive Nay rolls as four episodes; exclude the Not Voting record and both controls.

## Deviations Or Corrections

- None.

## Validation Results

- Focused gold bundle test: 11 passed.
- Final focused editorial and existing interpretation regressions: 46 passed (`test_valerie_foushee_economy_editorial_gold_v2.py`, `test_manual_interpretations.py`, and `test_legislative_interpretation_quality_benchmark.py`).
- Deterministic Markdown generation: `--check` passed; the checked-in side-by-side artifact includes claim text, official URLs, locators, support status, uncertainty, comprehension checks, and per-field decisions.
- JSON validation: all bundle JSON parsed in focused tests; identities, action reconciliation, stage separation, episode deduplication, source references, statuses, and control boundaries passed.
- Python compilation: generator and focused test compiled successfully.
- Full backend fixture suite: 667 passed and 1 unrelated platform failure. The failure is `test_exact_approved_manifest_bytes_pass`: the clean Windows CRLF checkout hashes differently, while the raw `HEAD` Git object exactly matches the expected SHA-256. No unrelated manifest file was changed.
- Frontend production build: passed. Existing React hook dependency warnings remain in unchanged frontend files.
- `git diff --check`: passed before staging; repeated on the staged milestone diff before commit.

## Production Writes

- Performed: no
- Scope: None.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert the milestone commit; no runtime, database, production, or deployment state is affected.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: Yes for the source-checked candidate milestone and draft-PR delivery boundary.
- Remaining limitations: Human comprehension sessions, editorial scoring, approval, and gold-benchmark designation remain outside Codex authority. Roll 180 remains intentionally unsynthesized; roll 263 remains a non-counting procedural control. One unrelated Windows exact-byte backend test remains platform-limited as documented above.
- Recommended next step: Human factual, editorial, and reader-comprehension review of the draft bundle before any runtime schema, import, or rendering milestone.
