# Milestone Plan: M13B Roll-19 Source-Readiness Correction V2

## Intent

Correct the concrete post-review roll-19 operational-source defect without
rewriting historical M13B v1, changing the accepted M13A universe, or beginning
M13C action interpretation.

## Base and authority

- Exact post-M13B v1 main: `e49d416b3549d87763e375079f742f7013c1c988`.
- Branch: `codex/m13b-roll19-source-readiness-correction`.
- M13A action set: 17 actions / `83b7b129eaa32d114c72782c70cb06dac55f7cd01c8681c8dc2ae2dca986cf5b`.
- Historical M13B v1 remains byte-identical and is superseded only for current
  interpretation readiness.

## Scope

- Preserve the accepted M13C fail-closed stop reason.
- Acquire the complete official January 13, 2026 GovInfo House section.
- Prove raw PDF page/content anchors for H677-H678 and H692-H693.
- Create M13B v2 by replacing only roll 19's operative source binding.
- Bind unchanged source-packet parity for the other 16 actions.
- Create a non-authorizing correction/supersession receipt.

## Non-scope

No action interpretation, episode construction, Semantic IR, synthesis, public
wording, site integration, publication, deployment, production write, or change
to Justice, National Security, Environment, or protected user-owned ZIPs.

## Definition of done

- [x] Historical M13B v1 ID, file SHA, subject SHA, and old PDF remain unchanged.
- [x] The old two-page PDF and size/header-only fixture fail the strengthened
  `operative_floor_text` contract.
- [x] The complete official House section proves exact-stage adoption, complete
  section 2 text through H678, and roll-19 linkage on H692-H693.
- [x] M13B v2 derives 17 ready / 0 blocked with exact 16-action packet parity.
- [x] Local validation and exact diff inspection pass.
- [ ] Draft PR and exact-head hosted CI pass before the independent correction
  review stop.

## Stop boundary

Stop at a draft correction PR. Do not begin or revive M13C until M13B v2 is
independently reviewed.
