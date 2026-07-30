# Milestone Plan: Foushee Justice 119 Universe Discovery V1

> Historical status (2026-07-30): this June 11 non-authorizing proposal is
> preserved as the original PR #123 discovery result. The completed human
> boundary review found proof-chain, methodology, boundary, and freshness
> corrections. V1 is therefore superseded for authority and interpretation by
> the V2 refresh proposal; neither version is authoritative without a detached
> receipt.

## Intent

- Discover, content-address, and reconcile Valerie Foushee's recorded
  119th-Congress Justice & Public Safety candidate action universe through a
  precise production snapshot cutoff.
- Preserve the accepted seven-action publication as a valid benchmark-sample
  finding while supplying a non-authorizing universe proposal for human review.

## Discovery Boundary

- In scope: read-only production, public API, repository acquisition/archive,
  classification, source-contract, and official-source evidence for F000477,
  `JUSTICE_PUBLIC_SAFETY`, House, Congress 119.
- Completeness is bounded to the cutoff represented by the content-addressed
  snapshot, not the future end of the 119th Congress.
- Out of scope: new action interpretations, episode construction, behavioral or
  synthesis propositions, full-record conclusions, authority receipts,
  publication changes, production writes, migrations, deployment, and merge.
- Expected change size: generic discovery tooling and tests, two closed schemas,
  a proposed manifest, one reconciliation artifact, this plan, a review packet,
  and directly affected navigation. Validation is domain-level plus the required
  disposable-PostgreSQL and governance checks.

## Production-Read Safety Gates

- Repository HEAD, local/remote `main`, deployed Render commit, cleanliness, and
  benchmark state must match the authorized baseline before database access.
- The configured URL must be inspected without disclosure and identify the
  intended production Supabase database.
- Raw evidence must remain in a secure directory outside the worktree.
- The client must be autocommit-safe so its first SQL command is the explicit
  `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY`. The immediate fixed proof
  must establish active read-only and repeatable-read state before
  transaction-local statement/lock/idle timeouts and application name are set.
- `default_transaction_read_only` is recorded as informational and may be
  either `on` or `off`; no session-level setting may be changed.
- Server-side read-only state, PostgreSQL/database/schema identity, and a
  sanitized digest-only query audit must be recorded before inventory queries.
- Only allowlisted, non-locking, non-side-effecting catalog and `SELECT` queries
  may execute. Failure to prove enforcement stops the milestone.
- A new read-only transaction must reproduce the member-action and
  Justice-classified digests before delivery; snapshot drift requires refresh or
  a reported blocker.

## Inventory Lanes

1. Production: every recorded Congress-119 member action, regardless of domain,
   then existing Justice classification, interpretation, source, precompute, and
   editorial state.
2. Governed benchmark: seven accepted action identities, exact-action source
   contracts, accepted Semantic IR corpora, approval, and successful-publication
   receipts.
3. Repository acquisition: raw archives, caches, manifests, parsers, and
   classification/interpretation records.
4. Broad recall: structured legislative metadata and taxonomy signals;
   keywords may increase recall but never decide membership.
5. Official reconciliation: Clerk roll calls, Congress.gov measure/amendment
   records, and GovInfo/official supporting material where exact-action meaning
   requires it.
6. Public API: scoped positions, Justice evidence, and editorial presentation
   responses for `119`, `all`, and `118`.

## Reconciliation Sequence

1. Map production lineage, canonical keys, source fields, and API consumers.
2. Capture and digest the complete member-action snapshot.
3. Union recall-lane candidates and preserve lane provenance.
4. Reconcile canonical identities, vote states, measure identities,
   classifications, sources, precomputes, acquisitions, and API projections.
5. Assign exactly one discovery disposition per recall candidate.
6. Separate the complete snapshot, recall set, proposed universe, and unresolved
   boundary set; compute order-independent digests.
7. Generate the non-authorizing proposal and reconciliation evidence, then
   validate and repeat the production freshness probe.

## Candidate-Universe Decision Rules

- Favor recall; include a candidate when any governed lane supplies a plausible
  Justice relationship.
- Proposed membership requires exact-action evidence supporting the established
  Justice boundary. Parent-measure context alone is insufficient.
- Party, vote direction, political salience, benchmark similarity, and fit with
  the current finding never influence inclusion or disposition.
- `Present` and `Not Voting` can be proposed in scope only as non-directional.
  Procedural/context actions remain visible and non-counting.
- Missing, unresolved, or conflicting evidence remains explicit. No unresolved
  candidate may silently become excluded.
- Discovery dispositions are non-authorizing inventory judgments and must not
  add support/opposition conclusions for newly discovered actions.

## Evidence Outputs

- Secure local raw production/API/official evidence and sanitized query audit.
- Sanitized proposed `full_issue_universe_manifest_v1` under the proposals path.
- Closed `full_issue_universe_discovery_v1` reconciliation artifact and schema.
- Generic read-only discovery tool, validator, and focused tests.
- Review packet documenting lineage, cutoffs, counts, digests, mismatches, gaps,
  blockers, and exact human decisions.

## Definition Of Done

- [x] All preflight and server-enforced read-only gates pass.
- [x] Complete Foushee Congress-119 member-action snapshot is captured and
  content-addressed through a precise cutoff.
- [x] Every recall candidate is accounted for exactly once, with proposed and
  unresolved sets explicit and all seven benchmark actions reconciled.
- [x] Production, repository, official-source, and public-API mismatches are
  classified without modifying production.
- [x] Proposed manifest and closed discovery artifact validate with recomputed,
  order-independent identities and no authority or synthesis claims.
- [x] Required safety, schema, digest, reconciliation, methodology, semantic,
  parsing, governance, credential, compilation, and diff validations pass.
- [x] Final production freshness check matches the captured snapshot.
- [ ] Sanitized diff is reviewed, one cohesive commit is pushed, and one draft PR
  is opened for human universe-boundary review.

## Baseline

- Branch/base commit:
  `codex/foushee-justice-119-universe-discovery` from
  `9d053e1bdabb2a2caf9e3f392d72d119a9c25983`.
- Repository preflight: clean; HEAD, local `main`, refreshed `origin/main`, and
  remote `origin/main` match the expected commit.
- Deployed backend: HTTP 200; `/health` reports the exact expected commit.
- Benchmark: `reviewed_conclusion`, `benchmark_sample`,
  `reviewed_sample_finding`; external full-record authority absent and full
  synthesis ineligible.

## Progress Checklist

- [x] Repository and deployed-backend identity preflight
- [x] Governing-contract and preliminary data-lineage discovery
- [x] Production read-only proof and inventory
- [x] Repository/API/official reconciliation
- [x] Artifact and tooling implementation
- [x] Final broad validation
- [x] Documentation and artifact reconciliation
- [ ] Commit and draft PR

## Discoveries

- The live health endpoint exposes a content commit identity and matched the
  authorized base at preflight.
- The current full-record review state expressly retains the seven actions as a
  complete benchmark sample while leaving every external full-record authority
  reference null.
- The ignored backend environment file identifies a PostgreSQL Supabase target
  without exposing its connection details.
- The corrected transaction contract passed with active
  `transaction_read_only=on`, `transaction_isolation=repeatable read`, and
  informational `default_transaction_read_only=off` over a Supavisor
  session-mode connection.
- The single proven transaction returned 555 direct production member actions,
  24 current primary Justice actions, member service/precompute/editorial
  state, and the public schema catalog; it ended with `ROLLBACK`.
- The repository Clerk cache contains 577 member actions through June 11, 2026.
  Twenty-two are absent from the production member-action join, with no
  production-only action in the same boundary.
- Official acquisition found 61 later Foushee actions, rolls 223–283 through
  July 23. They remain outside the declared June 11 snapshot and require a
  later refresh.
- The high-recall set contains 111 candidates. Source-led dispositions propose
  27 actions, retain 13 cross-domain boundary cases, classify 55 procedural
  controls, and reject 16 unsupported recall false positives.
- The live API returns 24/76/52 Justice evidence rows for `119`/`all`/`118`;
  the 119 set matches direct production and the seven governed benchmark
  projections remain intact.
- The final read-only snapshot began at `2026-07-30T17:46:57.928657Z`.
  Every fixed-query result digest, the 555-action production inventory, the
  24-action primary Justice set, benchmark presence, and latest vote date
  matched the baseline; the transaction rolled back and the connection closed.

## Decisions And Rationale

- The merged `full_issue_universe_manifest_v1` schema will be used unchanged for
  the proposal. Pending authority will be represented only in the surrounding
  discovery artifact and review packet.
- Raw database identifiers and connection details will remain outside the
  repository; repository artifacts will use canonical public identities and
  digests.

## Deviations Or Corrections

- The original startup-default gate was superseded by the user's corrected
  contract. The implementation now treats the default as informational while
  proving the active transaction before every production data query.
- The declared completeness boundary remains June 11 even though official
  acquisition observed later actions. This keeps the proposal honest about
  production/repository lag and makes the later refresh requirement explicit.

## Validation Results

- `python -m unittest backend.tests.test_readonly_discovery`: passed (11
  safety tests).
- `python -m unittest backend.tests.test_full_issue_universe_discovery
  backend.tests.test_readonly_discovery
  backend.tests.test_readonly_discovery_postgres`: passed (21 tests plus one
  expected disposable-PostgreSQL skip in the ordinary environment).
- Disposable PostgreSQL 17 adversarial integration: passed; database-enforced
  write rejection, deterministic ordering, missing/duplicate/conflicting/
  unresolved/changed snapshot cases exercised; container removed.
- `python scripts/validate_full_issue_universe_discovery.py`: passed.
- Full-record methodology validator and 18 tests: passed.
- Semantic IR validator, 26 tests, and the seven-check semantic pipeline:
  passed.
- Source-manifest parsing tests: passed (10 tests).
- Documentation and terminology governance, JSON parsing, credential scan,
  Python compilation, and `git diff --check`: passed.

## Production Writes

- Performed: no.
- Authorized: none.
- Expected effects: none.
- Actual effects: no production writes; the discovery transaction rolled back
  and the connection closed.

## Rollback Paths

- No production rollback is applicable because production writes are forbidden.
- Repository changes remain isolated to this branch and can be reviewed before
  merge; the active benchmark publication and registries are not touched.

## Blockers

- None. The 13 boundary cases, 22 through-cutoff ingestion gaps, 61 post-cutoff
  actions, and seven lossy Senate-resolution bill links are explicit human
  review inputs, not silent blockers to the bounded proposal.

## Final Reconciliation

- Definition of done satisfied except for Git delivery. The bounded discovery
  artifacts, documentation, final production freshness check, broad validation,
  credential review, and staged-diff review are complete; commit, push, and the
  draft PR remain.
- Recommended next step after those gates: human review of the proposed
  boundary. A detached authority receipt requires a separate explicit
  authorization.
