# Milestone Plan: Valerie Foushee Justice & Public Safety Editorial Gold V1

## Intent

- Immediate task: create a source-grounded, human-review-pending Justice & Public Safety editorial slice for Valerie P. Foushee and validate the generic editorial frontend contract with a second real domain.
- Larger-goal alignment: establish a reusable measure-first research packet and prove that review-only editorial slices can vary by policy mechanism without entering the production dependency path.

## Outcome

- User-visible or operational result: an explicit review-registry Justice slice rendered through `GoldenRenderFixture -> PositionByIssue -> EvidencePanel -> selector -> adapter -> EditorialIssueExperience`, with deterministic research/review artifacts and no production publication.

## Scope And Boundaries

- In scope: all available 119th-Congress Foushee `JUSTICE_PUBLIC_SAFETY` rows; official-source research; measure dossiers; explicit episode/class mapping; layered pending interpretations; deterministic generation; review fixture; focused generic corrections only if evidence requires them; tests, screenshots, documentation, draft PR.
- Out of scope: production registry changes; human approval; benchmark promotion; production eligibility; Economy content changes; multi-member scaling; broad UI redesign; merge; manual deployment.
- Files/systems likely touched: a new `docs/editorial/valerie_foushee_justice_public_safety_gold_v1/` tree, one deterministic builder and tests, review-bundle/fixture modules, the explicit review registry, golden-render harness/tests, and focused workflow/review documentation.

## Decision Envelope

- Codex may decide and execute: conservative record classes, episode relationships, source selection, bounded reader copy, reusable artifact structure, and narrowly reusable contract corrections supported by a real record.
- Explicit approval required for: any production registry entry, `human_approved`, `gold_benchmark`, `productionEligible: true`, production write/deploy, material civic-semantics change, or merge.
- Interpretation boundary: describe exact mechanisms and stage-level actions; do not infer motive or ideology, count procedural/Not Voting controls, equate measures with episodes, or force a unified philosophy.

## Definition Of Done

- [x] Inventory all 13 available rows and independently verify selected stages, member actions, outcomes, versions, lifecycle, and sources.
- [x] Create reusable dossiers, source manifest, claim map, episode map, review controls, and deterministic pending artifacts.
- [x] Render the pending slice through the existing generic path with production fallback and registry isolation intact.
- [x] Complete fresh-pass stage/source and editorial audits; resolve or flag every material issue.
- [x] Tests/build/validation recorded.
- [x] Review packet and final contract-validation documentation updated.
- [x] Commit, push, draft PR, local screenshots, and preview handoff completed without merge or manual production deploy.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/foushee-justice-public-safety-gold-v1` from `c71b9335030ba2edcedcbeca40612d403cb6ddb2`.
- Production/deployment state: production editorial registry is empty; review content is explicit-only; no production writes authorized.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`; preserve and exclude.
- Existing Economy editorial source, counts, copy, mappings, statuses, and rendering are immutable for this milestone.

## Available Evidence And Provisional Scope

All currently available rows are 119th Congress; a cross-Congress contract change is not provisionally necessary.

| Roll | Date | Measure/action | Foushee | Existing state | Provisional class / episode |
|---:|---|---|---|---|---|
| 32 | 2025-02-06 | H.R. 27, Trahan amendment No. 2 | Yea | ambiguous | exclusion/control pending exact amendment-text audit; related to fentanyl episode |
| 33 | 2025-02-06 | H.R. 27 passage | Nay | interpreted | substantive; `halt-fentanyl-legislative-path` pending version audit |
| 130 | 2025-05-15 | H.R. 2255 passage | Nay | interpreted | substantive; `retired-service-weapon-purchases` |
| 131 | 2025-05-15 | H.R. 2240 passage | Yea | interpreted | substantive; `officer-safety-data-reporting` |
| 160 | 2025-06-10 | H.Res. 489 previous question | Nay | insufficient | context-only procedural control |
| 161 | 2025-06-10 | H.Res. 489 rule adoption | Nay | insufficient | context-only procedural control |
| 166 | 2025-06-12 | S. 331 passage after Senate action | Yea | interpreted | substantive; `halt-fentanyl-legislative-path` pending version audit |
| 267 | 2025-09-16 | H.Res. 707 previous question | Nay | insufficient | context-only procedural control |
| 268 | 2025-09-16 | H.Res. 707 rule adoption | Nay | insufficient | context-only procedural control |
| 275 | 2025-09-17 | H.R. 5143 passage | Nay | interpreted | substantive; `dc-police-pursuit-rules` |
| 290 | 2025-11-18 | H.Res. 879 previous question | Nay | insufficient | context-only procedural control |
| 291 | 2025-11-18 | H.Res. 879 rule adoption | Nay | insufficient | context-only procedural control |
| 299 | 2025-11-19 | H.R. 5107 passage | Nay | interpreted | substantive; `dc-policing-reform-repeal` |

- Provisional reviewed period: 119th Congress.
- Provisional substantive count: 6 rolls.
- Provisional independent episode count: 5, subject to the H.R. 27/S. 331 version and continuity audit.
- Final inclusion: seven substantive rolls across five explicit policy episodes; no Not Voting row is available.
- Final controls/exclusions: six rule/previous-question votes. Research established that roll 32 was a substantive implementation-condition amendment and promoted it from the provisional control set.
- Resolved research boundaries: H.R. 27 and enacted S. 331 remain related but distinct actions in one episode; H.R. 5107 is described as repealing most, not all, of the D.C. law; roll 131 cleanly omits an opponent argument after an official-source search found no adequate stage-specific case.
- Generic-contract hypothesis: current single-Congress identity, explicit `episode_id`, optional argument fields, and `context_only` controls appear sufficient; no modification is justified before rendered evidence proves otherwise.

## Implementation Sequence

1. Complete official-source inventory and create explicit source/stage/episode decisions.
2. Build reusable measure dossiers, claim mappings, layered interpretations, controls, synthesis, and deterministic generator/tests.
3. Integrate the pending bundle into the explicit review registry and golden-render fixture through the shared path.
4. Run independent source-stage/editorial audits; correct only evidence-backed issues.
5. Run the full content/frontend/rendered validation matrix and capture required screenshots.
6. Reconcile documentation, stage intended files, commit, push, and open a draft PR.

## Progress Checklist

- [x] Discovery baseline and provisional inventory.
- [x] Official source and stage research.
- [x] Implementation.
- [x] Independent audit.
- [x] Validation and screenshots.
- [x] Documentation.
- [x] Commit/PR readiness.

## Discoveries

- Existing review packets and enriched interpretation batches already identify 13 current 119th-Congress rows and six interpreted final-passage actions; they are starting leads, not substitutes for this milestone's independent official-source audit.
- The seven substantive rolls span reporting, firearm disposition, D.C. pursuit authority, D.C. policing-law repeal, and three related actions in one fentanyl scheduling episode.
- No Not Voting record exists in the available Justice slice.

## Decisions And Rationale

- Use a coherent 119th-Congress slice with five independent policy episodes and no cross-Congress schema work.
- Treat rolls 160, 161, 267, 268, 290, and 291 as context-only controls; roll 32 is a substantive certification amendment.
- Do not infer a broader philosophy; the evidence supports a bounded, mixed Level 2 finding only.

## Deviations Or Corrections

- Promoted roll 32 from the provisional control set after the official amendment text established a direct implementation condition.
- Described H.R. 5107 as repealing most rather than all of the D.C. law after checking the committee substitute.
- Omitted an opponent case for H.R. 2240 after the official-source search did not find adequate stage-specific evidence.

## Validation Results

- Generator drift check and JSON parsing passed.
- New backend contract tests: 5 passed.
- Full frontend Node tests: 95 passed.
- Responsive Playwright tests: 11 passed across the existing suite, including Justice checks at 1440, 1024, 768, and 390 pixels.
- Twelve local review screenshots captured, including one-sided argument omission, procedural control, and production fallback states.

## Production Writes

- Performed: no.
- Scope: none authorized.
- Expected effects: review-only repository artifacts and automatic PR preview only.
- Actual effects: review-only files, local screenshots, draft PR #95, and its automatic Vercel preview; no production write or manual deployment.

## Rollback Paths

- Revert milestone commits; remove the Justice entry from the review registry and fixture. Production registry and ordinary client path remain unchanged throughout.

## Blockers

- None at baseline; official source sufficiency and exact stage/version integrity are hard gates.

## Final Reconciliation

- Definition of done satisfied: yes. Draft PR #95 is open and the automatic Vercel check is Ready.
- Remaining limitations: human factual review, scoring, comprehension testing, approval, benchmark promotion, and production eligibility remain pending.
- Recommended next step: after this milestone, validate shared dossiers across another representative without promoting this slice.
