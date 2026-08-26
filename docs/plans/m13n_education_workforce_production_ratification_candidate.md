# Milestone Plan: M13N Education & Workforce Ratification Candidate

## Intent

- Merge and deploy the independently accepted M13N-R runtime exactly.
- Capture truthful, fresh runtime and transaction-read-only production evidence.
- Build a non-activating Education preparation package and detached activation-ratification candidate.
- Stop at a draft PR for independent activation review.

## Exact Boundary

- Post-M13N-R main: `1a01725dbd3311bfa8dcdea31009466f2c51c6a1`.
- The six reviewed runtime-source files are frozen and may not change in M13N.
- Production database writes, registry mutation, Education activation, positive-authority sealing, deployment changes, and candidate-PR merge are forbidden.
- Protected user-owned ZIPs remain outside scope.

## Definition Of Done

- [x] PR #171 merged with accepted-head protection and main recorded.
- [x] Live `/health` equals exact post-M13N-R main.
- [x] Public inactive state remains unchanged.
- [x] Fresh exact runtime proof and read-only production preflight pass all gates.
- [x] Preparation authority, write set, rollback, empty template, and detached candidate are deterministic and non-authorizing.
- [ ] Disposable PostgreSQL proves exact apply, public projections, idempotency, drift refusal, and rollback in hosted CI.
- [x] Six runtime files remain byte-identical to the reviewed manifest.
- [ ] Draft M13N PR has exact-head hosted CI and remains unmerged.

## Production Safety

- Production operations in this milestone are read-only.
- The captured preflight must remain `6 / 152 / 163 / 3`, with zero Education rows and the exact production target/runtime binding.
- Any runtime, state, target, or baseline mismatch is a hard stop.
- The empty activation template and detached ratification candidate confer no authority.

## Validation

- Focused deterministic builders and validators.
- Exact governed disposable PostgreSQL lifecycle.
- M13N-R, M11N, M12N V3, and M13M compatibility.
- Semantic/release pipeline, Ruff, formatting, compile, catalog/schema, and diff checks.
- Exact-head hosted CI and Vercel preview.

## Captured Gates

- M13N-R accepted head: `ea32802a12a212f57ed8f80d01dbe71b2980c2e3`.
- Merge/post-convergence main: `1a01725dbd3311bfa8dcdea31009466f2c51c6a1`.
- Runtime manifest: `ad95d769f3d860431cfc7418b2bd4fd076f6ba991eff00c65031bf1fffe0e904`.
- Runtime-health proof: `4bde3cc7ea19ae29a142148c14f926ab76fb8406edac21930e6a745fe82c2690`.
- Production preflight: `ffd285eb447ce4abb2f48a2b7fdc0c80a7320aee912a7fc883779aa8e9c7c085`.
- Production fingerprint: `7fd41a05d8fcc033b8b1522e54a5ecda12ce9782c040e723d04613f30d30a860`.
- Preparation decision timestamp: `2026-08-26T00:47:09.030374Z`; reviewer: `dhart54`.

## Preparation Identities

- Preparation authority file/subject: `9d6c9051c30746d9fcfd54dd94c9c04d33b25007ebfd1a5c80b35b07b338355f` / `39ec1c2760123330a532a97ef5db2e80e1ec20830c7b7437b753bf6c3f77382e`.
- Write set file/subject: `7e5585c5b345d43579253c5e0e746669cfbd14d037730755668339494b0f671a` / `4486e75153b6f47c2a49b426082fb58f21f5e85506f3fa7b80d8ec9cbd88e5d2`.
- Rollback file/subject: `5e06f3f3306ace0d4dc9c6ad479171558cb706656ecc1ffac38185b363207e57` / `9667a7d2f960ea456ed4a91b203a60f0d5b44a210ef87a5678d5cc85afa49236`.
- Empty template file/subject: `95574a81f9fcfbf6130c6706dcee733321168cc8b3180d3ec7f3da6162dc8c9e` / `c29c1eb04795c5eb7e6199c914cf4122601176e01a5bc13f7661cbd767cd338c`.
- Candidate file/prospective subject: `70e411549cbb335ac771e4b93a2edfb4dcba62d611085396f7bd46ee9eb76f5f` / `eb44a2634d54639317b8997afad2253310e90288365c5e844ca6ac355923b88e`.

## Validation Results

- Focused M13N plus M13N-R/M11N/M12N/M13M compatibility: `100 passed`; three disposable PostgreSQL tests skipped locally because neither PostgreSQL nor the Docker daemon is available.
- M12N V3 frozen candidate, authority materialization, and successful-activation replay identities remain exact.
- M13M deterministic validation, public review-state catalog, and Semantic IR validation passed.
- Governed editorial release pipeline passed all 7 checks.
- Ruff, formatting, compile, workflow-YAML, diff, and six-file runtime-freeze checks passed.
- The normal Render workflow deployed exact main. Its separate known Justice provenance assertion failed after deployment; direct `/health` and the required inactive-domain probes passed exactly.
- Production database writes performed: none.

## Stop Point

After the draft M13N PR and exact-head CI, stop for independent ChatGPT activation review. Do not materialize or seal a positive activation authority.
