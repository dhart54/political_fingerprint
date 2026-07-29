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
- The representative route retains basic vote evidence and source receipts and
  can layer publication-gated IR-native presentation fields. Its top panel
  orders issue cards by available action count, reviewed
  substantive Yes/No count, non-directional or limited/context availability,
  and stable domain order. This is evidence coverage, not an analytical,
  ideological, or vote-direction ranking. Shared member-neutral domain
  descriptions and an accessible `Recorded action composition` bar explain the
  cards. Its Yea, Nay, and combined non-directional/context segments use only
  supplied action counts. The ranked grid is the primary selector and compact
  jump navigation is retained in the evidence section; the duplicative third
  issue list is absent. Party benchmarking remains deferred. Actual Present and
  Not Voting-only issue areas remain selectable. Expected-but-missing actions
  are not emitted by the current API and are not synthesized in React. The former
  `/golden-render-fixture` route is absent. Presentation tiers and wording are
  supplied by the backend; React does not infer them. The human-approved, gold,
  production-eligible F000477 Justice 119th presentation is publication-active:
  `scope=119` and `scope=all` return `reviewed_conclusion`, with `scope=all`
  explicitly bounded to the reviewed 119th-Congress record; `scope=118` remains
  `receipts_only`.
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
