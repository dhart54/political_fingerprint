# Editorial Current-State Index

The machine-readable authority is
`docs/editorial/current_state_index.json`.

- Editorial Semantic IR V1 is the only executable editorial semantic
  architecture.
- Accepted references remain 12 development and four held-out cases.
- The pre-IR builders, milestone generators, old frontend adapters, registries,
  review fixtures, and rich renderer are deleted and cannot be replayed.
- Frozen dossiers, source manifests, proof packets, receipts, provenance, and
  generated historical evidence remain in place as noncanonical evidence. A
  119-file whole-tree manifest locks those roots to the cutover base.
- Acquisition capability and tests remain intact.
- Frontend Pass A implements a finder-first, URL-backed representative journey
  on `/`: compact overview, truthful Congress scope, responsive issue discovery,
  conditional reviewed analysis, conditional reviewed policy episodes, and a
  newest-first chronological exact-receipt ledger. No representative or sample
  is automatically selected. Recommended issue ordering uses only
  backend-supplied public claim rank, evidence usefulness, and stable domain
  order; party, ideology, conclusion substance, and Yea/Nay direction do not
  affect it. Shared member-neutral descriptions and the accessible `Recorded
  action composition` display use supplied counts only. Present, Not Voting,
  procedural, and limited-context distinctions remain visible.
  Expected-but-missing actions are not emitted by the current API and are not
  synthesized in React. Comparison, preference/alignment, race, alerts,
  contact, methodology explorers, and across-Congress analytical tools are
  deferred from the primary route without deleting their components. The former
  `/golden-render-fixture` route remains absent.
- A deterministic public-field-only review-state catalog is now generated from
  merged-validator-approved full-record review manifests. It is descriptive,
  not authorizing: public analysis still requires an independently eligible
  active presentation and exact member, issue, artifact, semantic-tier, teaser,
  and scope agreement. Repeated-pattern/trajectory semantic roles and
  directions are backend-supplied. The active Justice full-record presentation
  supplies 32 reviewed policy episodes through that governed contract.
- The human-approved, gold, production-eligible F000477 Justice 119th
  presentation remains publication-active and semantic tier
  `reviewed_conclusion`. The selected issue experience displays the completed
  37-action record as `Full issue interpretation available`. `scope=119` and
  `scope=all` may return that bounded full record, with `scope=all` explicitly limited to the reviewed
  119th-Congress record; `scope=118` remains `receipts_only`.
- Full-Record Issue Interpretation V1 now keeps semantic tier, review scope,
  review completion, and public claim class separate. The active F000477 Justice
  artifact is a `reviewed_conclusion` over the content-addressed 37-action
  `full_defined_issue_record` through July 23, 2026. All 37 actions are
  accounted for as 35 substantive projections and two explicit controls; 32
  policy episodes, the compiled Semantic IR, full-issue synthesis, and public
  presentation have completed their governed acceptance chain. Production now
  selects the human-approved full-record candidate, not the historical
  seven-action presentation. The historical seven-action review-state record
  remains immutable evidence and is no longer the active publication boundary.
- The canonical F000477 Justice V2 universe discovery reconciles 638 official
  House member actions through July 23, 2026
  (latest roll 283) into 172 high-recall candidates: 37 proposed
  substantive/non-directional actions, seven expressive actions, 69 procedural
  actions, 59 exact-action-ineligible actions, and zero unresolved boundary
  cases. Official evidence is sufficient for universe-boundary review; 34
  remaining Congress-metadata gaps are explicitly stage-bounded (zero proposed,
  two expressive, 21 procedural, and 11 ineligible) and do not imply action
  interpretation, episode, Semantic IR, synthesis, or public-wording readiness.
  Human reviewer `dhart54`, acting under
  `full_issue_universe_review_authority_v1`, approved that exact complete issue
  universe. The detached receipt is
  `docs/editorial/full_record_reviews/f000477_justice_public_safety_119_full_issue_universe_authority_receipt_v2.json`.
  That authority originally established membership only; the later governed
  M3-M10 chain completed interpretation, episodes, Semantic IR, synthesis,
  public presentation acceptance, production eligibility, and activation. The current manifest, discovery,
  source inventory, configuration, V1/V2 comparison, repair plan, and review
  packet are the V2 artifacts under
  `docs/editorial/full_record_reviews/proposals/`. V1 remains discoverable only
  as historical, superseded, non-selectable evidence.
- Interpretation-source readiness is now mechanically complete and ready for
  all 37 authorized actions under the detached, non-authorizing artifact
  `docs/editorial/full_record_reviews/source_readiness/f000477_justice_public_safety_119_interpretation_source_readiness_v1.json`.
  This source-readiness artifact remains the immutable M2 input to the now
  completed M3-M10 chain; it does not independently authorize those later
  results.
- Before the activation, the 71-artifact seed had no publication-registry row.
  That state remains historical evidence and was not modified by the editorial
  hard cutover.
- The historical seven-action activation was applied successfully on
  2026-07-29. Its immutable closeout receipt remains
  `docs/editorial/publication_activations/foushee_justice_public_safety_119_successful_activation_receipt_v1.json`.
  It was superseded in the active registry on 2026-08-05 by full-record artifact
  221 (`1c088fc4a98e8442263899faffd7e203967cf60c387944884e4ce755d6ba7943`).
  A fresh read-only production snapshot on 2026-08-08 verified exactly one
  active F000477 publication with that identity. Selected Issue Experience
  V1.1 is the accepted public presentation layer at checkpoint `f16bc73`.
- M11A is now the active content-expansion milestone. It selects National
  Security & Foreign Policy deterministically and constructs only a proposed
  universe boundary; no new action interpretation, Semantic IR, publication,
  deployment, or production write is authorized.

The exact deletion, test-transfer, preservation, route, and validation record is
`docs/editorial/editorial_hard_cutover_v1_receipt.json`.

Canonical commands:

```powershell
python scripts/run_editorial_pipeline.py validate --tier semantic
python scripts/run_editorial_pipeline.py validate --tier domain --domain ECONOMY_TAXES
python scripts/run_editorial_pipeline.py validate --tier release --include-frontend
```
