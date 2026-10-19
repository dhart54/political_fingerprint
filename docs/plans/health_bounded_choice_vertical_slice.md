# Bounded Health choice: admission, previews and dormant publication

Status: discovery and implementation, 19 October 2026.

## Intent and result

Deliver the complete one-action Health engineering path for F000477 and M001184:
an exact-subject bounded review contract, a pending owner decision, faithful
desktop/mobile previews, and a dormant initial-publication path validated in an
owned ephemeral PostgreSQL database. The result must be ready for independent
review and subsequent content/rendering acceptance together.

## Authority and boundaries

The new approved milestone explicitly includes bounded admission/presentation
contracts, a narrowly scoped staged database migration, ephemeral validation,
tests, review fixes, commits, pushes and draft PRs. Final content/rendering
acceptance, applying a migration to Supabase/production, public activation,
production writes, manual deployment and successor merge are excluded.

Preserve the original packet and accepted wording, frozen IR, all seven mapping
objects and normalized source identities. Exactly `house:119:2:180`,
`episode:s2393:119`, F000477 Yea (one **supporting** notable choice) and M001184
Not Voting (zero propositions, visible accounting). No overall Health conclusion,
primary promotion, benchmark claim or invented owner decision.

Keep legacy full-universe, gold-benchmark publication and V2R replacement guards
unchanged in meaning. Add a closed explicit `bounded_choice_review` branch and
detached bounded subject/receipt validation. Reuse canonical IR and existing
bounded per-member accounting validation with null full-record authority.
Default live responses must remain unchanged until separately authorized
activation. Automatic deployment must neither apply the staged migration nor
activate the candidate. No production credentials or production database are
needed for this work.

## Baseline and ownership

- Fresh main/base: `c52d121b64d814de3cf684980368bced40e5b4ea` (PR238 merge).
- Branch `codex/health-bounded-choice-feature`, worktree `.w/hbc`.
- Starting tracked tree clean. Preserve all other worktrees and unrelated work;
  `.w/infra` remains the sole Infrastructure writer. No other writer is created.
- Prior PR238 has exact-head independent review and green hosted/post-merge CI,
  deployed-commit Render smoke and Vercel. This is historical validation, not
  acceptance of new outputs. Independent local retests used a Git-tree-verified
  snapshot shim rather than a fresh clone.
- Original packet SHA-256:
  `3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347`.
  Original ZIP remains unverified. The three retained raw official objects may
  supply additional evidence; their National Security acceptance does not transfer.

## Sequence and definition of done

1. Reconcile current admission, rendering, persistence/selection and deployment
   boundaries. Read interpretation/editorial/publication workflows and relevant
   Supabase/Postgres guidance. Establish an owned ephemeral database and a
   reproducible preview environment.
2. Add closed exact-subject bounded admission and pending receipt contracts;
   derive complete two-member accounting through `validate_review`. Bind frozen
   graph, mappings, source objects/raw evidence, preview and rendering subjects.
   Reject pending receipts at acceptance-dependent boundaries.
3. Implement the explicit bounded presentation branch and truthful non-public
   preview transport/UI. Preserve source/coverage roles and exact text. Capture
   desktop/mobile views for both members and evidence/qualification states.
4. Develop the staged migration and dormant initial-publication basis, preserving
   legacy gold behavior. Bind actual accepted subject evidence, current validation,
   source completeness, identity, immutability, least privilege and exact caps.
   Reuse V2 initial-write invariants with separate per-member write sets, fresh
   baselines, idempotency, partial-failure recovery and rollback.
5. Validate adversarial member/scope/source/boundary/hash/receipt cases; legacy
   publication regressions; ephemeral migration/activation/security/rollback;
   frontend build and rendered previews; default-live response parity; automatic
   deployment isolation. Inspect final behavior and diff.
6. Commit/push scoped work, open/attach draft PR(s), obtain exact-head hosted
   execution evidence and apply independent-review corrections. Preserve exact
   review subjects and clearly pending acceptance-dependent fields.

- [x] Reconciled base and isolated owner/worktree.
- [x] Exact bounded admission and complete per-member accounting.
- [x] Closed presentation branch and desktop/mobile preview evidence.
- [x] Staged migration and dormant initial-publication implementation.
- [x] Ephemeral DB/security/idempotency/fault/rollback validation.
- [x] Legacy/public defaults and automatic deployment isolation verified.
- [x] Final subject/preview/activation packet and local validation reconciliation.
- [ ] Scoped commits/push/draft PR and exact-head CI/review evidence.

Expected footprint: roughly 25-40 directly related files across backend contracts,
presentation/storage, staged migration, focused tests, preview UI/fixtures and
review artifacts. Generated fan-out is bounded to two members and one action.
Validation tiers: semantic and subsystem loops during work, release validation
near delivery because runtime selection and staged persistence interfaces change.

## Discoveries and decisions

Docker CLI is installed but its daemon is not running. Native PostgreSQL 17/18
binaries are available, so an owned localhost-only ephemeral cluster can provide
the required DB proof without a production service. No daemon or system service
is changed. Supabase CLI is not installed on PATH; command discovery and pinned
temporary invocation will precede migration generation as required by the skill.

Full-universe receipt constants cannot admit a partial record. The existing
database CHECK, activation trigger and repository selector require gold status;
the new basis must be explicit and narrow, with regression proof for the legacy
path. V2R excludes Health and must not be repurposed as initial publication.

## Validation, rollback and stop conditions

Results are recorded as execution proceeds. Use only explicitly identified local
ephemeral DSNs with owned paths/ports; no inherited DATABASE_URL or Supabase MCP
write. Preserve and verify rollback before exercising writes. Stop for actual
source conflict, authority ambiguity outside the approved contract envelope,
security/production effects outside scope, or an unresolved hard gate after safe
correction. Ordinary implementation/test failures remain in scope.

Rollback: remove only this milestone's unmerged changes/close its draft PR;
ephemeral DB rollback restores exact baseline and drops/stops only owned test
resources. No production rollback is executed. Migration application and public
activation remain separately authorized future operations.

Production writes performed: none. Final acceptance: pending. Final reconciliation
and actual validation/delivery evidence will be completed before handoff.

## Local implementation and evidence

The complete review packet is
`docs/editorial/review_packages/health_bounded_choice_v1/REVIEW.md`. Both semantic
subjects reproduce the frozen graph/mappings and pass the existing accounting
validator. Both content/rendering receipts and initial-publication preparations
are pending. The four actual PNG captures were visually inspected. Desktop,
tablet, mobile, keyboard receipt expansion and invalid-member checks pass.
Production route checks return 404 for both members with the preview flag set.

The owned ephemeral database is `pf_health_choice_test`, PostgreSQL 17.5,
127.0.0.1:55438, under `.tmp/pg-data`. Tests refuse any other database name or
non-loopback DSN. All numbered canonical migrations plus the CLI-generated staged
migration ran there. Fifteen PostgreSQL tests cover exact initial writes,
separate fresh member baselines, stale/replayed no-write rejection, injected
failures at three boundaries, partial member failure/retry, exact reverse data
rollback, guarded schema rollback/reapply, direct SQL pending rejection,
immutability, role/table/function privileges, invoker view/RLS, legacy gold
retention and actual default API parity without activation. Supabase CLI security
advisors leave one baseline warning on the untouched 0016 immutability function's
mutable search path. The touched activation function now sets a fixed search
path; all new functions do likewise. No new advisor finding remains. No
production DSN was used.

The V2 initial contract is reused without changes; V2R is untouched. Generated
write sets copy their caps so adversarial mutation cannot alter the process
constant. Exact replay fails closed with no duplicate writes. Row-state rollback
is exact; normal PostgreSQL sequence gaps are intentionally retained. Schema
rollback restores legacy CHECK meaning with an explicit constraint name.

Frontend: all 319 existing/new units pass; seven development browser checks and
seven production exclusion checks pass; production build passes. Lint has zero
errors and eight existing hook warnings in untouched components. A temporary
Windows permission restriction affected initial temp-file/process tests; reruns
with the appropriate process access passed. The existing JSX render harness was
extended with the actual imported bounded component, preserving its regressions.

Read-only Render inspection was directly authorized for My Workspace
(`tea-d0t0r4qli9vc73a4f2i0`). Service `srv-d84abkuq1p3s738qd1i0` tracks main,
root `backend`, auto-deploy on commit, free plan, no PR previews. Its returned
commands are `pip install -r requirements.txt` and
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`; no pre-deploy command was
returned. Repository startup has no migration/Health activation hook. Staged SQL
is outside numbered migration paths; the exact-head CI uses only its dedicated
PostgreSQL service. Vercel production cannot expose the local preview route.

The small footprint expansion beyond the initial estimate comes from separate
member accounting/receipt/preparation objects, four actual captures, and an
explicit schema rollback companion. It remains one action and two members.
No adjacent Infrastructure, Immigration, capacity, finder or persistence work
was absorbed. Independent review and hosted exact-head status remain pending
until the draft PR and review evidence are available.
