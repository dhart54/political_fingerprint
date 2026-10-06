# Render backend smoke contract maintenance

## Intent, outcome and decision envelope

Restore reliable smoke checks of the existing governed public API on an isolated
`codex/render-smoke-contract` branch. Routine code, tests, feature push and draft
PR are authorized. Merge, deploy, hooks, publication, production writes, service
configuration and editorial decisions are outside this milestone. Immigration
PR198 and `.w/ib` have an active owner and are untouched.

Expected diff: one workflow, one standard-library runner, focused unit tests,
this plan and a compact live validation receipt. No product/runtime code changes.
The operational result is a maintained, reusable smoke contract, with a PR-only
GET path that cannot enter the deployment job.

## Baseline and guidance

- GitHub main verified October 6, 2026: `862b290cceea8af7d6c1c800d1ecdfa52386a490`.
  Worktree `.w/render-smoke` starts clean from that exact main, preserving unrelated
  root work. PR199 `d9f0174cebfb27c1390e3dec21bdb4b4c250ae78` is guidance only.
- Read root AGENTS, PR199 root AGENTS/DOT_OPERATING_BRIEF/CURRENT_STATE,
  interpretation principles, operating/PR workflows and relevant public selectors.
  No `.agents` skill files exist in either named Git tree or the applicable local
  ancestors. The sole scoped AGENTS is under `docs/semantic_ir`, outside this diff.
- Inspected both hosted workflows before execution. Existing main push paths,
  hook condition and 90-second wait remain. No workflow was manually dispatched.
- Render job112063800306, run37399669875 at main, successfully invoked the hook
  then failed curl404 before Python assertions. The fixture `leg_alex_morgan` is
  nonexistent publicly and must not represent cross-member isolation.

## Authority reconciliation and discoveries

The committed authorized Green activation execution after-state is
`docs/editorial/publication_replacements/m15b_green_activation_execution/after-justice-direct.json.gz`,
file SHA256 `a06fe2853a0fd1bdf9db04878ce8c73c6921229ef464b6627272b5e68b686530`.
Its direct/live files are identical and sealed by the existing file manifest;
the README, execution record, applied receipts and registry audit explain the
activation. It supplies expectations independently of today's response.

Public GETs reconcile all eight issue tiers, identity, scope and published
provenance against that record. Foushee119/all has Education, Environment,
National Security and Justice published; Economy, Health, Immigration and
Infrastructure remain receipts-only. Foushee118 and Thomas Massie119 remain
receipts-only for every issue. Massie's repository-backed identity is M001184.

Justice's embedded API artifact remains
`public-issue-presentation-candidate:f000477:justice_public_safety:119:v1`, version1,
review receipt `approval-receipt:f000477-full-record-justice-119-m10r1`, wording SHA
`58722f5f61ea0b2eb3b41b3cbf58009971c6fcfd184e189117715e2955627fc7` and compiled IR
SHA `becb730af6c9ca6a08ecf6afb885503df99131530b4dc852a8e3e5817aab8fb3`.
Green root251 wraps this historical presentation provenance; wrapper identity is
not the embedded API identity. Justice has37 accounted actions,35 directional
receipts,2 noncounting controls,16 synthesis-support actions,14 support episodes,
4 primary patterns and1 trajectory. Legacy interpreted position counts are a
separate contract and are not equated with full-review receipt counts.

Later renderers change prose and receipt caveat presentation. Smoke checks bind
unchanged provenance, action identities, findings, direction, lineage and coverage
instead of freezing complete historical response bytes. Three site presentations
use an overview with null conclusion; Justice uses a conclusion. Site scope=all
and Justice scope=all have different established boundary sentences. Both are
enforced from their respective authority responses.

## Implementation and validation

- [x] Discovery and independent repository/live reconciliation.
- [x] Extract bounded standard-library GET-only runner (eight requests including
  health before/after, 30-second per-request timeout and 8 MiB response cap).
- [x] Enforce nonempty positions/findings/receipts, exact published provenance,
  complete issue coverage and fallback isolation. Justice receipts bind to member,
  interpretation, full chamber/Congress/session/roll identity, vote and Clerk URL.
- [x] HTTP errors, timeouts, invalid JSON and semantic mismatches fail closed, write
  a failure report and exit nonzero. No retry, fallback or transient-success mask.
- [x] Add PR-only exact-head tests and public GET smoke. Deploy job is push-only
  and PR job has no deploy-hook secret. Main hook runs require the requested Git
  SHA in health; no-hook runs identify the currently served SHA without deploying.
- [x] 21 offline tests pass (including many parameterized mutations). Test CLI503
  through the actual transport error path; ensure one request and exit1.
- [x] Fresh GET smoke PASS at `862b290c...`, 2026-10-06 16:28:32–16:28:38 UTC.
  See [validation receipt](../review_packets/render_backend_smoke_20261006.json).
  Raw responses are in the task's temporary `pf-render-smoke-verified` directory;
  the committed receipt records their file digests and exact authority digest.
- [x] YAML parses, targeted tests and final diff/whitespace inspected.
- [ ] Feature commit/push, draft PR and exact-head hosted CI reconciliation.

Validation corrections were in the smoke implementation: use the established
overview/conclusion and scope-boundary variants. Windows sandbox temporary-directory
ACLs blocked a local CLI report test; the same focused offline suite passed outside
the sandbox. No product, approval or production gate was changed.

## Operation and maintenance

```powershell
python -m unittest scripts.tests.test_render_backend_smoke -v
python scripts/render_backend_smoke.py --output-dir <fresh-output-directory>
```

Add `--expected-commit <full-sha>` when validating a specified deployment. Check
`report.json` for pass/failure, endpoints, timestamps and the deployed commit.
Future expectation updates require independent reconciliation with authorized
publication evidence; a new live response alone cannot become the expected state.
The historical baseline is a smoke authority source, not a legacy generator,
frontend adapter or reconstructed approval. Update only affected serving invariants
when an separately authorized publication changes them.

## Production writes, rollback and limits

Production writes/deployments/hooks performed: none. Rollback for this maintenance
is an ordinary revert of its feature commit after separate merge authority.
Existing main merge paths include an automatic deploy hook; a future merge must
have an envelope permitting that effect. This task stops at draft PR.

Render MCP `list_services` reported no selected workspace, so no current Render
deploy record was inspected. `/health` identifies the deployment, corroborated
by GitHub's main and the historical failed run at that SHA; this is not fresh
Render service-record or direct database verification. No workspace selection,
database, secrets or configuration were changed. The live check validates serving
contracts, not editorial quality, frontend comprehension or new approval state.

Follow-up: transient public availability must remain visible as a failed run.
No unrelated repository cleanup or expensive manual suite reruns are required.
Recommendation: review the bounded draft diff and exact-head checks; obtain
separate merge/deployment authority before integration.
