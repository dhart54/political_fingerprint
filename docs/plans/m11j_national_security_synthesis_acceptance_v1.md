# M11J National Security Synthesis Acceptance V1

Status: implementation and local validation complete; draft PR preparation.

## Intent

Create detached human synthesis authority and deterministic canonical-internal
implementation for the two exact M11I candidates and the bounded assistance
revision. Stop before public wording.

## Exact Base

- Accepted M11I head: `8535163aee1d2a548ec7d0c23935b1322a05b863`.
- Post-M11I main: `e9e771b23eb65629e0a3ed7ecb6c32748d7ebf59`.
- Branch: `codex/m11j-national-security-synthesis-acceptance`.

## Scope

- Generic synthesis decision authority and implementation validation.
- Two governed decisions: one accepted as written and one bounded revision.
- Exact proposition, relationship, episode, and action lineage.
- Schemas, deterministic artifacts, adversarial tests, state, and review packet.

## Non-Scope

- Public wording, publication, persistence, database or production writes,
  production effects, deployment, frontend/API/runtime changes.
- Changes to M11A-M11I, Justice, or either protected user-owned ZIP.

## Definition Of Done

- [x] Original M11I candidate content remains immutable.
- [x] Exact human revision is separately bound and deterministically applied.
- [x] Source direction remains structural proposition-relative metadata only.
- [x] All 15 proposition roles and non-inflated lineage remain exact.
- [x] Generic/adversarial, milestone, Justice, and governance checks pass.
- [ ] Draft PR opened for human mechanical review.

## Decisions

- Use sealed per-candidate decisions and explicit path/value replacements so a
  bounded revision cannot authorize unrelated drift.
- Preserve full original candidate content inside every implementation record.
- Require accepted proposition semantic content—not direction metadata—as the
  declared basis for synthesis explanation.

## Production Writes

- Performed: no.
- Authorized: none.

## Blockers

- None.

## Validation Results

- Deterministic M11J regeneration and independent exact-identity validation:
  pass.
- M11A-M11J validators: pass.
- Generic Behavioral Semantic IR and synthesis candidate/decision suites: 50
  tests passed, including 11 M11J synthesis-decision adversarial tests.
- Justice authority, action interpretation, episode implementation, Semantic
  IR, launch, ratification, benchmark, routing, and catalog regressions: pass.
- Documentation and terminology governance, Draft-07 schemas, JSON/YAML
  parsing, Ruff, formatting, compilation, ancestry, immutable-artifact, and
  diff checks: pass.
- GitHub CI: pending draft PR.
