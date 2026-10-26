# Infrastructure exact-head CI compatibility

**Blocked before implementation:** main's Health helper freezes the entire local
`scripts/prepare_shared_domain_candidate.py` to `ac22199d`/blob
`8eb95a54bb95b17009023e851cfdeb26cb9a4573`; Infrastructure132 preserves the
approved nondirectional authored-action fix in blob
`674ec45d22e8f890d654b499e438d4356e0b2227`. The other six frozen rule files
match. Copying the Health closure alone cannot pass both contracts. Replacing
Infrastructure's helper loses its fix; suppressing Health's equality check or
testing different code under an exact-head label is prohibited.

The preparation prototype stopped at a path-count assertion before copying any
dependency or editing the workflow. Branch/index/tracked files remain unchanged;
this new assessment plan and ignored diagnostics preserve partial work. The
independent reviewer found the executable dependency closure is18files (19with
README); the initial broader selected set/count estimate was not applied.

Smallest required decision: a separately reviewed compatibility-baseline/provenance
update for the Health preparation contract to account for the established shared
helper change, preserving immutable packet wording, historical artifacts and
candidate/approval boundaries. Any resulting frozen-package subject change needs
its own explicit scope. This Infrastructure lane does not authorize that update.
Leave the workflow-dependent lane blocked; continue safe retained-source research.

The sequence below records the assessed approach, not executed implementation.

Outcome: remove the single workflow conflict blocking PR232 Actions while
preserving main's Health validation and the Infrastructure suites. No PR merge,
merge/rebase, trigger or permission change, editorial decision or production effect.

Pinned input: Infrastructure132 `f99c44443400722da216a1c8d0c77be4bb9c7ab6`;
actual remote main `c52d121b64d814de3cf684980368bced40e5b4ea`.
Read-only merge-tree confirms only `.github/workflows/backend-tests.yml` conflicts.
PR metadata reports CONFLICTING/DIRTY; its older base OID is preserved separately.

Scope: keep main's exact shared-candidate/Health pytest line and add an exact-head
Infrastructure step in the same job. Copy only main's existing inert Health test,
two helpers, frozen review-package/owner-packet assets and documentary receipts
needed by that test, unchanged. Do not edit Health's branch/worktree, runtime,
schemas, source corpus, decisions or publication bindings. Expected about22
dependency paths plus workflow, this plan and validation/review receipts.

Sequence:

1. Preflight every dependency against pinned-main Git blobs; refuse differing
   existing files. Confirm common runtime/schema dependencies require no changes.
2. Preserve both coverage sets in the workflow with unchanged checkout, triggers,
   permissions, services, secrets, deployment and publication behavior.
3. Verify exact copied bytes/hashes and original packet identity/blank fields.
   Run the complete main-side Health test and helper checks, plus proportional
   Infrastructure validation/collection. Do not relabel inherited tests as fresh.
4. Prove workflow three-way merge compatibility against actual main without
   applying a merge. Inspect final diff and preservation of current132 artifacts.
5. Commit/push this CI prerequisite separately, update draft PR232, obtain
   independent review of the successor, and observe actual exact-head Actions
   execution/checkout and results. Queued/running is not success.

Done: compatible workflow, unchanged main validation assets, both coverage sets
retained, current candidate state untouched, independent review and actual hosted
results recorded with exact heads. If runtime/schema/security/semantic integration
is needed, stop that dependent lane and continue safe retained-source research.

The copied documentary receipts are historical pinned-main inputs. Copying them
does not record any new editorial acceptance. Prepared graphs/review payloads
remain candidates with production/publication/approval flags unchanged.
