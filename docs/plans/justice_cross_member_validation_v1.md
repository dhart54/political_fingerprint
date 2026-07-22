# Milestone Plan: Justice Cross-Member Validation V1

## Intent

- Immediate task: Validate whether the five Justice & Public Safety policy episodes merged in PR #95 can support distinct, evidence-grounded conclusions for a small vote-selected House cohort without duplicating measure research.
- Larger-goal alignment: Test the reusable editorial architecture before any broader member scaling while preserving civic-integrity and publication gates.
- Pre-merge correction: Remove full-vector template lookup, derive evidence from shared episode-action interpretations, and make expected coverage fail closed against the shared episode-set definition.

## Outcome

- User-visible or operational result: A review-only seven-member comparison, reusable member-overlay contract, deterministic inference tests, and selected profiles rendered through the generic review harness.

## Scope And Boundaries

- In scope: official 119th House actions on rolls 32, 33, 130, 131, 166, 275, and 299; Foushee plus six vote-selected members; shared-research references; overlays; candidate inference; comparison artifacts; review-only frontend fixtures; tests and draft PR.
- Out of scope: new Justice episode research, production registry additions, benchmark promotion, human approval, production eligibility, nationwide generation, frontend redesign, merge, or production deployment.
- Files/systems likely touched: `backend/app/summaries`, `backend/scripts`, `backend/tests`, `docs/editorial/justice_cross_member_validation_v1`, `docs/review_packets`, `frontend/lib`, `frontend/components`, and frontend tests.

## Decision Envelope

- Codex may decide and execute: a vote-vector cohort; a domain-neutral overlay contract; deterministic candidate derivation; synthetic edge cases; narrowly scoped generic corrections; review-only fixture integration; branch, commit, push, and draft PR.
- Explicit approval required for: changing legislative meaning, production writes or registry publication, benchmark/human approval, schema or editorial-semantic expansion beyond the milestone, merge, or manual deployment.

## Definition Of Done

- [x] Cohort selection documents every eligible member vector and explains the six additions.
- [x] Shared dossiers remain unchanged and are referenced through stable episode/roll identifiers.
- [x] Generic overlay contract produces seven member trajectories and independent candidate conclusions.
- [x] Anti-template, missing-vote, episode-counting, load-bearing, contrary-evidence, and party-independence tests pass.
- [x] Comparison packet and selected review profiles make differences inspectable without ranking members.
- [x] All new artifacts remain `human_approval_pending`, `not_promoted`, and `productionEligible: false`; production registry remains isolated.
- [x] Required tests/build/validation recorded.
- [x] Review packet and final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/justice-cross-member-validation-v1` from exact commit `a484b2f5d5bb3434d63f0970a6d33e9acb611693` (PR #95 merge).
- Production/deployment state, if relevant: no production write or manual deployment authorized; automatic Vercel draft-PR preview is allowed.
- Tracked working tree: clean isolated worktree at milestone start.
- Known unrelated untracked artifacts: `_analysis_house_votes/` contains temporary official House Clerk XML used only for local cohort analysis and will not be committed.

## Implementation Sequence

1. Derive a cohort from official roll actions using completeness and vote-vector variation only.
2. Implement a reusable overlay contract and deterministic member-specific episode/candidate builder referencing shared research.
3. Generate review-only overlays, comparison matrices, and selected generic frontend fixtures.
4. Add backend/frontend regressions for template leakage, party independence, missing actions, shared episode counting, and production isolation.
5. Run targeted and full required validation, rendered review, documentation reconciliation, commit, push, and draft PR.

## Progress Checklist

- [x] Discovery
- [x] Pre-merge architecture correction
- [x] Corrected validation
- [x] Corrected documentation
- [x] Correction commit/PR update

## Discoveries

- PR #95 stores Foushee's extracted actions but not chamber-wide rows, so official House Clerk XML was retrieved read-only for the seven substantive rolls.
- Across members appearing in the reviewed rolls, 370 have seven Yes/No actions; 31 have six; the remaining rows have five or fewer.
- The complete cohort contains meaningful action-structure diversity, including an exact Foushee match and a fentanyl-versus-police-action split, without using party as an inference input.
- The official union contains 437 members appearing on at least one substantive roll; 370 have complete seven-roll Yes/No coverage.
- Real contrary evidence remains atomic episode evidence: Moskowitz's safeguard-repeal opposition weakens the broad-support candidate rather than disappearing into a raw vote total.
- Pre-merge review found that `_select_pattern` still keyed conclusions from exact seven-action tuples and that overlay denominators shrank with omitted caller data. Both are blockers despite the valid cohort and evidence boundaries.

## Decisions And Rationale

- Selected additions: Alma S. Adams (`Y/N/N/Y/Y/N/N`, exact Foushee match); Robert B. Aderholt (`N/Y/Y/Y/Y/Y/Y`, dominant action contrast); Thomas Massie (`N/N/Y/Y/N/Y/Y`, fentanyl-versus-police-action split); Sanford D. Bishop, Jr. (`N/Y/Y/Y/Y/N/N`, different fentanyl trajectory); Jesús G. "Chuy" García (`N/N/N/N/N/N/N`, all-Nay but policy-mechanism-specific record); Jared Moskowitz (`Y/Y/Y/Y/Y/Y/N`, mostly-Yea with opposition to the policing-reform repeal).
- Within-vector tie-breaking uses the smallest Bioguide ID after a vector is chosen for methodological value; identity, fame, reputation, caucus, ratings, and party are not selection scores.
- Party remains descriptive overlay metadata and is excluded from candidate derivation.
- Interpretation boundary: conclusions describe only the five reviewed episodes and concrete mechanisms; no motive, ideology, moral ranking, prediction, or cross-time movement is inferred.
- Correction architecture: shared episode-action interpretations emit member-independent semantic themes; a generic evaluator scores bounded candidates from independent-episode support, competing themes, mechanism diversity, and coverage; member identity is inserted only after selection.
- Coverage source of truth: expected substantive rolls, controls, episodes, and episode-to-roll relationships live in the shared episode-set contract. Missing caller data cannot reduce a denominator.
- Cohort role labels will describe action structure only. Party remains post-selection descriptive metadata.

## Deviations Or Corrections

- House procedural controls use `Aye/No` while substantive rolls use `Yea/Nay`; ingestion normalizes only these equivalent Clerk labels before the controls remain non-counting.
- The first Playwright run reused a stale port-3100 server from another checkout. After stopping only the verified listener and forcing a fresh worktree-local server, the complete suite passed. No product code changed in response to the stale render.
- The old candidate-preselection join was replaced by a domain-neutral theme evaluator; the existing PR #95 Foushee output remains unchanged.
- The initial concurrent Node test command hit a Windows `spawn EPERM`; the identical 106-test suite passed with `--test-concurrency=1`.
- A broad backend run reached 653 passes but also reported unrelated missing local source caches, global pytest-temp permissions, and a pre-existing manifest-pin mismatch. The focused milestone backend suite is the hard gate.

## Validation Results

- Deterministic artifact generation: pass (`build_justice_cross_member_validation.py --check`).
- Corrected generic inference, overlay, and cross-member Python regressions: 29 passed.
- Python compilation: pass for backend app and the new builder.
- JSON parsing: all 7 generated milestone artifacts parsed.
- Frontend Node tests: 106 passed, run directly because the sandbox intermittently blocked Node test-worker spawning.
- ESLint: pass with 8 pre-existing React Hook warnings and zero errors.
- Next production build and validity-of-types check: pass.
- Responsive Playwright: 13 passed, including the selected Justice cross-member profiles and mobile receipt interactions.
- Generic runtime scan: no selected IDs/names, party decision branches, Justice conclusions, current rolls, or fixed seven-roll/five-episode assumptions.
- `git diff --check`: pass.
- Shared Foushee dossier/interview artifacts and production registry: unchanged.

## Production Writes

- Performed: no
- Scope: none authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- All milestone changes are isolated on the milestone branch and can be reverted by commit; no data or production rollback is needed.

## Blockers

- None. Official roll data matched selected members reliably across all seven substantive rolls.

## Final Reconciliation

- Definition of done satisfied: yes; implementation, review artifacts, rendered validation, and publication isolation are complete.
- Remaining limitations: a seven-member, five-episode cohort cannot establish nationwide validity; selected real members all have complete coverage, so missing-vote behavior is synthetic.
- Recommended next step: run a larger review-only multi-member batch with naturally incomplete records before public-product polish.
