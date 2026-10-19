# Health one-action inert review package

Status: implemented and validated for draft-PR review, 19 October 2026.

## Intent and outcome

Turn the accepted S.2393 example into a reproducible, typed, one-action candidate
review package. Preserve the exact accepted packet wording and existing source
objects while exercising the current shared-corpus adapter and Semantic IR
pipeline. Deliver focused positive/negative tests and a draft PR for review;
new outputs remain unapproved, non-public and ineligible for persistence.

## Baseline and admission

- Worktree: `.w/health-one-action-package`; branch
  `codex/health-one-action-package`.
- Base: `ac22199dff31bd2e271d95be82077c8e7de064c4`, ordinary merge of PR236.
  Parents: `d61146f7cd6055d6ad4b74979bcb575d7b40c97b` and reviewed head
  `004804cb48df0eb45197d2e3d588207835aeb922`.
  Tree: `5b96c60a94ea00302630a0074a4ead6c0813020b`, equal to reviewed head.
  All ten backend jobs and two preview statuses were terminal successful before
  merge. Branch/history preserved; fresh `origin/main` equaled the merge.
- The first merge attempt was rejected because authorization was relayed.
  The human then directly answered in this chat, “Authorize merge and inert
  package milestone.” The authorized retry succeeded; implementation is admitted.
- Packet SHA-256:
  `3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347`.
  Plaintext materialization, unchanged historical blank fields. ZIP unverified.
- Initial tracked tree clean. Other owned worktrees, including `.w/infra` and
  `.w/ib`, are outside the write scope.

## Scope and decision envelope

Exactly `house:119:2:180`, singleton `episode:s2393:119`, F000477 Yea and M001184
Not Voting. Reuse accepted meaning, qualifications, Health membership and exact
packet wording. No broad Health conclusion or additional action. No acceptance
of the newly generated IR/presentation inputs follows from that editorial
decision. Interpretations follow `docs/interpretation_principles.md` and the
editorial standardization workflow.

Allowed: isolated tooling, candidate evidence/inputs/IR and mapped presentation
review inputs, focused tests, review corrections, commit/push and draft PR.
This includes bounded CI test-selection maintenance in the existing full-history
exact-head shared-candidate pytest step. It does not authorize changes to workflow
permissions, secrets, deployment triggers, environments or production configuration.
Existing automatic PR previews are included. Forbidden: successor merge,
database/import or production writes, publication/activation, new artifact
acceptance/promotion, manual deployment, runtime manifests, schema/security/
secret/production-config changes and storage-contract changes.

Expected footprint: one preparation script, one focused test module, this plan
and a bounded review directory (17 new files), plus one existing workflow's
test-list correction. Targeted validation in
seconds; no population regeneration, browser or database loop.

## Representability and implementation sequence

1. Confirm the existing Shared Legislative Corpus V1 definitions can hold a
   one-action core/mapping/two projections without authority changes. Adapt and
   compile only that slice through `run_editorial_pipeline` with candidate state.
2. Preserve exact source records and source/claim bindings from local pinned Git
   objects, explicitly distinct from original archive verification. Preserve
   the original packet as its exact bytes.
3. Build typed mapped presentation review inputs using the existing
   `editorial_public_issue_presentation_v1` analytical-text/mapping definitions
   and pure validation. Do not compile a public presentation or remove candidate
   state to make one. Check exact packet wording parity and IR reference closure.
4. Add positive and adversarial tests for identity, singleton scope, source
   versions/seals, member separation, nondirectional accounting, wording parity,
   immutable upstream bytes and public/persistence rejection. Regeneration must
   be deterministic and bounded to the package directory.
5. Review final diff and evidence; commit/push scoped work; open/attach a draft
   PR and report exact base/head, automatic preview state and remaining limits.

## Progress and definition of done

- [x] Exact-head PR236 merge, parent/tree/main proof and isolated branch.
- [x] Read applicable contracts; candidate compilation is representable.
- [x] Implement bounded preparation and mapped presentation-input validation.
- [x] Exact packet parity, twelve focused positive/negative checks and deterministic replay.
- [x] Final artifact/diff review: 17 new scoped files plus one existing CI pytest
      list correction; candidate/history bytes, runtime, schemas and rejection
      guards are unchanged.
- [x] Prepare authorized feature-branch commit/push and draft-PR handoff. Exact
      remote head and PR state are recorded by PR metadata and the delivery report.

## Boundaries, rollback and remaining gates

Compiler `case_scope=full_record` accounts for all explicitly supplied inputs;
it is not the issue-review scope. Documentary review scope is
`bounded_partial_record`. Existing candidate guards at pipeline, adapter and
public compiler remain unchanged. A valid mapped review input is not a completed
public presentation or a production authority binding.

No persistence proposal/importer, database or environment file is needed. The
historical seed-specific importer cannot be repurposed for Health. Any later
storage incompatibility requires a separate decision. Local rollback removes
only newly added package/tool/test/plan files; closing the unmerged successor PR
is sufficient to abandon this inert milestone. No cleanup is automatic.

Production writes performed: none. No production state is inspected or certified
by these offline checks. The ZIP, newly generated artifact acceptance and later
publication/storage gates remain explicit limitations.

## Discoveries and validation

The existing core/projection IDs require numeric chamber/Congress revisions;
descriptive scope suffixes are not valid. The package uses candidate collection
revision `v4` under that unchanged syntax, preserves the exact action seal, and
reserves no canonical production identity. The issue mapping/manifest carries
the bounded selection. No contract or schema change was required for the inert
package. Full public-authoring/acceptance and storage remain later gates.

Twelve focused tests pass, including packet/text parity, source/membership and
singleton closure, Foushee support and Massie non-directional accounting, all
candidate guards, adverse mapping/scope mutations, immutable upstream files,
and deterministic generated-object comparisons. Seven generation rules remain
identical to the reconciled base and are hash-bound in provenance.
`validate_editorial_semantic_ir.py` passes all 12 development and 4 held-out
accepted references plus 4 held-out cases. Independent review identified that
the initial hosted workflow did not select the new module. The bounded correction
adds it to the existing exact-head/full-history shared-candidate pytest list;
all other workflow structure and operational settings remain unchanged.

The focused package, shared-corpus and pipeline regression run passes 35 tests:
`python -m pytest -q backend/tests/test_health_one_action_review.py
backend/tests/test_shared_legislative_corpus.py backend/tests/test_editorial_pipeline.py`.
The initial run reported two local cache-write permission warnings; a final run
with `-p no:cacheprovider` passed all 35 tests without warnings after the final
source-capture assertion/documentation correction. No product/test assertion
failed. Package `--check` is deterministic and read-only.

Generated source fan-out retains the complete governed Clerk object as stored:
the two reviewed member rows, metadata and party totals. It is not a new full-XML
download. This adds no other action, member projection or behavioral finding.

## Final reconciliation

The inert package is represented and validated under existing corpus, IR,
analytical-text and source-contract definitions. No production/storage contract
or schema was added or changed. Public/persistence rejection is tested rather
than bypassed. Exact accepted packet text is bound to typed review mappings;
the new graph and mappings still require independent review and separate
content-bound acceptance. No independent review of the successor head is claimed
yet; corrections supplied during this milestone remain in scope.

Automatic PR previews are authorized but display only the existing application,
not this unintegrated package. Original ZIP identity, complete public-authoring
implementation, new artifact approval and any later compatible storage path
remain unresolved release gates, not authorities conferred by passing tests.

## Independent review correction: hosted selection

At initial head `2957e307f146c711516802c0036ed0d2c58e358c`, independent review
correctly found the new module absent from all explicit hosted lists. The scoped
fix adds `backend/tests/test_health_one_action_review.py` to
`m14h-exact-head` / “Validate shared candidate preparation at exact head”.
Workflow YAML structure is compared against the prior head with only that run
string allowed to change. The exact selected invocation is run locally, then
the resulting exact-head hosted step is inspected for actual execution evidence.
Hosted results and the correction head are retained in the delivery report and
PR evidence, without claiming editorial acceptance or changing any artifact.

Local correction validation passed: workflow YAML parses, and structural
comparison to the prior head permits exactly the single pytest run-string
addition. Full-history exact-head checkout is preserved. The unmodified selected
command passes 160 tests (including all 12 package tests); two existing local
cache-write permission warnings remain non-failing. Separate collection confirms
the 12 Health test identities. Package regeneration `--check` still passes.
