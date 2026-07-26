# Editorial Pipeline Dependency Inventory V1

Baseline: `b49d380acd1e1d80dc462a8159d1155c320241f1`

This is a read-only ownership inventory. Phase A does not move, clean up,
regenerate, or change any listed legacy path.

## Representation map

| Semantic layer | Current representation | Classification | Phase A finding |
| --- | --- | --- | --- |
| Exact-action eligibility | `backend/app/summaries/editorial_domain_eligibility.py` | canonical candidate | Deterministic action-level boundary; parent context is insufficient. |
| Exact-action eligibility | corrected `domain_eligibility_report.json` | reusable input | Reviewed accepted/rejected actions and reasons. |
| Action meaning and stage | Economy, Justice, and corrected Environment dossier directories | reusable input | Action-scoped meanings, legislative stages, source IDs, and claim evidence. |
| Episode and policy family | the three reviewed episode-map files | reusable input | Episode identity is shared legislative meaning, not member inference. |
| Structural metadata and traits | corrected `policy_trait_contract.json` | reusable input | Structural attributes remain distinct from policy traits. |
| Trait relationships and shared novelty | corrected `trait_relationship_contract.json` | reusable input | Shared novelty can be reviewed once. |
| Member status and coverage | `editorial_member_overlay.py` | canonical candidate | Closest deterministic member/action boundary. |
| Member status and coverage | corrected `member_overlays.json` and vector evaluations | duplicate representation | Derived review material that can drift from its builder. |
| Evidence patterns and propositions | `editorial_inference.py` | compatibility adapter | Current shape predates a normalized proposition graph. |
| Evidence patterns and propositions | corrected `inference_candidates.json` | duplicate representation | Materialized candidate interpretation. |
| Conclusion planning | `editorial_conclusion_synthesis.py` | canonical candidate | Closest deterministic composition boundary. |
| Section ownership | `editorial_proposition_ownership.py` | canonical candidate | Owns deduplication and primary-section checks. |
| Section ownership | corrected `section_ownership_report.json` | duplicate representation | Audit output, not future semantic authority. |
| Review routing | `editorial_review_routing.py` | canonical candidate | Reusable route selection after an IR adapter exists. |
| Rendered presentation | `editorialIssuePresentation.mjs` and `editorialIssuePublicPresentation.mjs` | compatibility adapter | Presentation boundaries must not add analytical meaning. |
| Review fixtures | corrected `review_render_fixtures.json` and `editorialIssueTestFixtures.mjs` | duplicate representation | Downstream copies expose semantic corrections to drift. |
| Persistence mirror | corrected `persistence_batch_manifest.json` | compatibility adapter | A bounded delivery shape, not semantic authority. |
| Economy and Justice builders | milestone-specific builder scripts | historical generator | Retained for provenance and reproduction. |
| Original Environment builder | `build_commissioning_domain_v1.py` | superseded representation | The corrected generator supersedes its output semantics. |
| Corrected Environment builder | `build_commissioning_domain_v1_correction.py` | historical generator | Retained for the corrected milestone receipt chain. |
| Cross-domain canonical ownership | Semantic IR V1 | unresolved | The proposed contract needs external review before runtime adoption. |

The machine-readable inventory contains exact repository paths and notes for
each row.

## Current correction fan-out

A small correction to action eligibility or episode identity currently
propagates through several separately materialized layers:

```text
dossiers / eligibility / episode and trait maps
  -> member overlays and vector evaluations
  -> inference candidates
  -> conclusion, ownership, and review-routing reports
  -> persistence manifests
  -> review fixtures and frontend fixture copies
  -> mutation checks, rendered comparisons, and receipts
```

This fan-out explains why a local semantic correction can require many changed
files even when no new factual source is introduced. It also makes the source
of a discrepancy difficult to distinguish from a stale downstream copy.

## Proposed strangler sequence

1. Establish the versioned Semantic IR, candidate corpus, held-out inputs, and
   seconds-scale validator.
2. Add a read-only adapter that emits IR from existing reviewed dossiers and
   maps without changing runtime consumers.
3. Derive review packets and fixtures from IR and prove semantic parity.
4. Adapt conclusion planning, proposition ownership, and review routing to
   consume IR.
5. Adapt persistence mirrors to consume reviewed IR while keeping semantic
   acceptance, production, and publication as separate gates.
6. Move frontend adapters to an IR-derived view model; continue forbidding the
   renderer from adding meaning.
7. Retire historical generators and duplicate material only after separately
   reviewed parity and rollback coverage.

No step after the first is implemented by this milestone.

## Ownership conclusion

The V1 proposition graph and conclusion plan are the proposed canonical
semantic output. Existing dossiers and maps remain reusable reviewed inputs.
Current builders, materialized inference files, persistence manifests, and
frontend fixtures remain untouched compatibility or historical layers until a
later milestone explicitly migrates them.
