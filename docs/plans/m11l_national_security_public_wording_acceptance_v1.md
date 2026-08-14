# M11L National Security Public-Wording Acceptance V1

Status: implementation and local validation complete; mechanical review pending.

## Intent

Bind the accepted M11K package and its 18 human wording decisions into an
immutable authority record and deterministic canonical reviewed-wording
implementation for internal use only.

## Exact Base

- Accepted M11K PR #143 head: `57f29bd156c0f6c747fd21084491558d3277bd22`.
- Post-M11K main: `649bb508e2cdb92ab8cb0afe82dd266c2f503944`.
- Branch: `codex/m11l-national-security-public-wording-acceptance`.

## Scope

- A generic fail-closed bounded public-wording decision contract.
- Four exact accept-as-written decisions and fourteen exact bounded revisions.
- Immutable original candidate embedding, source and limitation preservation,
  parity, schemas, adversarial tests, and current-state closeout.

## Non-Scope

- Publication, production selection, persistence, database or production
  writes, deployment, frontend/API/runtime behavior, or selector activation.
- Changes to accepted M11A-M11K, Justice artifacts, or protected ZIP files.

## Definition Of Done

- [x] Exact M11K head, merge base, package, template, and parity are bound.
- [x] All M11H/M11J semantic sources and limitation identities are preserved.
- [x] Four items remain exact and fourteen revisions are implemented exactly.
- [x] Semantic/source/evidence/direction/authority tampering fails closed.
- [x] Canonical state marks M11K complete and M11L pending mechanical review.
- [x] Requested local validation passes.
- [ ] Draft PR is open and hosted CI is green.

## Production Writes

- Performed: no.
- Authorized: none.
