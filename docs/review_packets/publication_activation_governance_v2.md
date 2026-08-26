# Publication Activation Governance V2 Review Packet

## Decision Requested

Does Publication Activation Governance V2 preserve the existing fail-closed
safety bar while ensuring that equivalent fresh execution evidence can be
recaptured without changing stable human authority or requiring human
re-ratification?

## Scope

- Additive future-only V2 authority, write-set, and execution-validation code.
- No reinterpretation or regeneration of accepted V1 authorities.
- No publication artifact, selector, registry metadata, schema, frontend, or
  production mutation.
- No M14 or future-domain candidate/evidence.

## Model

The stable authority binds the exact candidate, semantic lineage, preparation
authority, reviewed runtime manifest/source commit, production target, complete
governed baseline, exact write-set subject, registry target, rollback,
postconditions, and positive authorization scope. Its exact fields are listed in
`docs/workflows/publication-activation-governance-v2.md`.

Runtime health and transaction-read-only preflight objects are execution-only.
Their timestamps, file hashes, and subject hashes are excluded from authority and
write-set subjects. The execution result records the exact fresh evidence subject
hashes used.

## Exact Non-Cascading Identity Proof

Two runtime proofs for the same stable runtime:

- proof A: `3fd30be0e6936cd06e98468764cdc471d43c10537da1b37ad5f608c1b4e29a16`
- proof B: `6892e6b45c18657635c6743a59b14aa8745a293081c8663d69f7144501bb7c75`

Two transaction-read-only preflights for the same stable state:

- preflight A: `189225fc8b1961c93910115325a2f1b7995adc983090a504dbc3c29bb686ba44`
- preflight B: `d73e27b27320be0d119043729118d5188f3bae35b5f79fae67f544861d3ee961`

Both pairs produce `VALID_FOR_EXECUTION` under the same stable subjects:

- authority: `b118aed65b2f536fd1792d5a276fb3a8502db5b2e0d07dbf8533078a5b36f8aa`
- write set: `7b55206b70b8d4a84cdf1799008d7e61a51f9e2be89b632bb52926c1aa365241`

The expired-evidence regression first fails closed, then replaces both objects
mechanically and reaches `VALID_FOR_EXECUTION` without changing either stable
subject.

## Adversarial Results

Focused V2 tests fail closed for:

- deployed/health commit drift;
- current runtime-manifest drift;
- production state-fingerprint drift;
- existing registry content drift;
- existing registry publication-metadata drift;
- target registry-row presence;
- governed count drift;
- current write-precondition drift;
- write-graph drift under existing authority;
- internally invalid or stale evidence;
- activation decision chronology preceding preparation authority.

The hosted PostgreSQL test establishes a real transaction-read-only baseline,
proves an attempted insert is rejected by PostgreSQL, validates the normalized
fresh observation under the existing authority, and confirms counts, fingerprint,
and registry rows are unchanged. It is wired into the existing
`publication-activation-postgres` job.

## Historical Compatibility

Local replay and focused compatibility results:

- V2/M11N/M12N V3/M13N-R/M13N authority and closeout suite: `76 passed`.
- M11N ratification-candidate validator: passed with historical subjects intact.
- M12N ratification validator and frozen V3 historical replay: passed with
  historical subjects intact.
- Full-record benchmark/activation suite: `46 passed`.
- Governed release pipeline: passed all 7 checks.
- Public review-state catalog: deterministic and current.
- Historical activation directories, current-state indexes, and protected ZIPs:
  zero changed paths.

## Production Isolation

A bounded live transaction-read-only verification reported:

- `7` batches;
- `155` artifacts;
- `165` relationships;
- `4` publication-registry rows;
- state fingerprint
  `090477315f73df6cadda662f2aa24ef4a30ed0b2e74669bb3e7d5cf73680e01e`.

The four active rows remain Justice & Public Safety, National Security & Foreign
Policy, Environment & Energy, and Education & Workforce. Those four resolve to
`reviewed_conclusion` for `119` and `all`; every domain remains `receipts_only`
for `118`. No fifth row exists and no production write was performed.

## Validation Notes

- Focused Ruff and Ruff format checks pass for all changed Python files.
- Python compile, documentation/schema/catalog, Git diff checks, and workflow
  validation pass locally.
- Repository-wide Ruff/format is not a clean baseline: 539 pre-existing lint
  findings and 187 pre-existing formatting differences occur outside this
  milestone. They were not modified or absorbed.
- Local Docker/PostgreSQL is unavailable; the exact real-database V2 proof is a
  mandatory hosted step in the draft PR.
- Hosted implementation-head run `32924329185` at
  `c9f3612b7699c76ced3e0a953a825429d4358684` passed all four backend jobs. The
  publication-activation job completed the V2 transaction-read-only proof, the
  unchanged historical activation chain, backup/real-Uvicorn evidence, and
  owned-resource cleanup; the full-record benchmark also passed.

## Stop Boundary

Stop after exact-head hosted CI and independent governance review. Do not merge,
deploy, begin M14, or capture future-domain production runtime evidence.
