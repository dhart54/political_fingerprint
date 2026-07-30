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
  directions are backend-supplied. The live selector supplies no policy
  episodes until a separately reviewed contract does so.
- The human-approved, gold, production-eligible F000477 Justice 119th
  presentation remains publication-active and semantic tier
  `reviewed_conclusion`, but Pass A displays its independent review state as
  `Reviewed benchmark sample`. `scope=119` and `scope=all` may return that
  bounded sample, with `scope=all` explicitly limited to the reviewed
  119th-Congress record; `scope=118` remains `receipts_only`.
- Full-Record Issue Interpretation V1 now keeps semantic tier, review scope,
  review completion, and public claim class separate. The active F000477 Justice
  artifact remains a valid `reviewed_conclusion` within its completely
  accounted seven-action `benchmark_sample`, with public claim class
  `reviewed_sample_finding`. A content-addressed
  `full_defined_issue_record` has not been established, full-record action
  accounting has not passed, external universe authority and full-record
  semantic-validation/human-approval receipts are absent, and a final full
  issue synthesis is not eligible.
  The machine-readable state is
  `docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json`.
- Before the activation, the 71-artifact seed had no publication-registry row.
  That state remains historical evidence and was not modified by the editorial
  hard cutover.
- The separate deterministic Foushee activation bundle was applied successfully
  on 2026-07-29 as one exact seven-row transaction. Its immutable closeout
  receipt is
  `docs/editorial/publication_activations/foushee_justice_public_safety_119_successful_activation_receipt_v1.json`.
  The rollback was not triggered; its identity-bound guardrails remain
  documented but are not authorized by the receipt.

The exact deletion, test-transfer, preservation, route, and validation record is
`docs/editorial/editorial_hard_cutover_v1_receipt.json`.

Canonical commands:

```powershell
python scripts/run_editorial_pipeline.py validate --tier semantic
python scripts/run_editorial_pipeline.py validate --tier domain --domain ECONOMY_TAXES
python scripts/run_editorial_pipeline.py validate --tier release --include-frontend
```
