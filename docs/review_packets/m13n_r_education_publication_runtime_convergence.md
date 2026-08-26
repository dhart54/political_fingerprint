# M13N-R Education Publication Runtime Convergence

## Boundary

This code-only milestone makes the already accepted M13M artifact recognizable by
the publication runtime after a future exact preparation authority, sealed
activation authority, and active registry row exist. It also includes the final
production-sensitive Education preparation/execution code that M13N will use.
It creates none of those governed objects and performs no production read, write,
preflight, activation, or runtime-proof capture.

Accepted content remains:

- artifact `site-integration-candidate:f000477:education_workforce:119:v1`;
- file SHA-256 `34f470355e82010a4b5f8180143ba99566e50320643141a2c35b35af89658f31`;
- subject SHA-256 `edfac59e705245e4a4a5ae7e2a7d009a6ad184036b6b872ca031b22ef48dca2d`.

## Runtime contract

Publication dispatch is explicit for National Security, Environment, and
Education. Unknown identities fail closed. Education requires the exact accepted
candidate; a non-synthetic accepted preparation authority with every mutation,
activation, persistence, and deployment permission false; a distinct sealed
positive authority using the hardened stable-runtime and historical-ratification
evidence contracts; exact registry gates; and exact metadata/content bindings.

Runtime capability does not activate Education. Without the exact row, all scopes
remain `receipts_only`. A test-only exact future row proves `reviewed_conclusion`
at `119` and `all`, with the existing 119th-Congress analytical boundary at
`all`, while `118` stays `receipts_only`.

## Complete future M13N runtime source manifest

The future ratification must hash the smallest complete production-sensitive set:

1. `backend/app/api/positions.py` — active-candidate positions/evidence projection.
2. `backend/app/api/editorial_presentations.py` — public presentation route.
3. `backend/app/editorial_presentations/selector.py` — multi-domain public selector.
4. `backend/app/editorial_presentations/site_publication.py` — authority, eligibility, and fail-closed dispatch.
5. `backend/app/editorial_presentations/education_workforce_integration_candidate.py` — accepted Education validation and projection.
6. `backend/scripts/foushee_education_workforce_publication_preparation.py` — bounded preparation, exact lifecycle, rollback, and fail-closed production execution entry point.

All six paths exist in this PR. `reviewed_runtime_manifest()` hashes their exact
bytes, and a regression asserts both existence and exact set membership. After
the exact M13N-R merge commit is deployed, M13N can capture runtime health and a
transaction-read-only production preflight without changing any file above.

If M13N discovers that any production-sensitive path must change, it must stop as
`production_runtime_not_converged`, merge and deploy the corrected runtime, and
capture fresh evidence against that new exact commit. Governed evidence JSON/MD,
authority forms, tests that do not alter runtime behavior, and later governance
tooling outside this set do not change the ratified runtime manifest.

Historical M12N manifests remain frozen and are not compared with current
runtime during historical replay. Fresh production execution still requires the
current exact manifest.

## Preparation and execution boundary

The Education runtime can construct and validate the exact M13M three-artifact,
two-relationship, one-registry-row graph; capture a read-only baseline; construct
the non-activating preparation authority and empty human decision template; bind
rollback; apply idempotently to disposable PostgreSQL; refuse state/runtime/target
drift; and restore the exact baseline.

Production execution remains impossible without all of the following:

- exact non-synthetic Education preparation authority;
- sealed accepted positive Education activation authority;
- exact activation write-set binding;
- exact approved production target identity;
- fresh preflight and unchanged state fingerprint;
- stable ratified runtime manifest and commit identity;
- separate fresh execution-runtime proof matching that stable runtime; and
- explicit apply or rollback confirmation.

No Education production-preflight, runtime-proof, authority, write-set, rollback,
receipt, or current-state artifact exists in this PR.

## Review frontier

Is PR #171 now a complete production-sensitive runtime such that, once its exact
merge commit is deployed, M13N can capture truthful production/runtime evidence
without changing ratified runtime code?
