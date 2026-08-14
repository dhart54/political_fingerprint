# M11K National Security Public-Wording Candidates V1

Status: implementation and local validation complete; draft PR required.

## Intent

Create a detached, deterministic, non-authorizing public-wording review package
from the exact accepted M11H Behavioral Semantic IR and M11J canonical internal
synthesis. Stop for human substantive wording review.

## Exact Base

- Accepted M11J PR #142 head: `ed0d3b65f287b3bc1b8985a7ef85a72a9e574043`.
- Post-M11J main: `03b14aa030ea302c1c109b0efd6a2ad7cef23f1b`.
- Branch: `codex/m11k-national-security-public-wording-candidates`.

## Scope

- Generic detached wording-candidate compilation and validation.
- One overview, two synthesis items, eight repeated patterns, one trajectory,
  and six notable choices.
- Exact accepted semantic bindings, complete limitation treatment, empty human
  decision template, parity, dossier, schemas, tests, and current state.

## Non-Scope

- Human acceptance, canonical public copy, publication, persistence, database
  or production writes, deployment, frontend/API/runtime changes, or selector
  activation.
- Changes to accepted M11A-M11J or Justice artifacts, or either protected ZIP.

## Definition Of Done

- [x] Exact post-M11J base and accepted source identities are bound.
- [x] All 15 behavioral and two synthesis records have complete wording
  accounting without changing semantic roles.
- [x] Ukraine wording states accepted behavior without a misleading single
  mixed policy label.
- [x] H.R. 8800 remains outside wording evidence.
- [x] Every source limitation is retained or explicitly compressed.
- [x] Requested local validation passes; hosted CI remains a PR gate.
- [ ] Draft PR is open and stopped for human substantive wording review.

## Decisions

- Keep wording as a detached candidate layer; do not invoke the production
  presentation compiler or alter runtime code.
- Permit no single direction display where explicit accepted behavior is more
  accurate than a mechanical mixed label.
- Validate objective semantic and authority constraints while leaving clarity
  and prose quality to human review.

## Production Writes

- Performed: no.
- Authorized: none.

## Blockers

- None.

## Validation Results

- Deterministic generation, exact M11K validation, and all M11A-M11K
  validators: pass.
- Generic Behavioral Semantic IR, synthesis, wording-candidate, and public
  presentation regressions: 101 passed, including 11 M11K adversarial tests.
- Selected Issue Experience: 11 unit tests and 13 production-shaped Playwright
  tests passed.
- Justice Semantic IR, launch, ratification, benchmark, routing, and catalog
  regressions: pass.
- Governance, terminology, schemas, JSON/YAML parsing, Ruff, formatting,
  compilation, and diff checks: pass.
- The broad local hosted-equivalent suite reached 315 passes; remaining local
  failures are pre-existing Windows temp-permission and checkout byte/line-ending
  constraints. Linux hosted CI is the authoritative full integration gate.
- GitHub CI: pending draft PR.
