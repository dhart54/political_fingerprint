# Milestone Plan: Foushee Justice 119 Universe Authority Receipt V1

## Intent and outcome

- Mechanically record the already-issued human approval of the exact V2
  Foushee Justice/Public Safety 119th-Congress universe.
- Produce one detached, content-bound
  `full_issue_universe_authority_receipt_v1` and an independent repository
  verifier without interpreting actions or authorizing later semantic stages.

## Scope and boundaries

- In scope: reproduce frozen V2 identities and accounting, write the one-time
  human authority timestamp, verify the receipt independently, share canonical
  manifest/receipt verification with the full-record validator, add tamper
  tests, and reconcile current-state indexes.
- Out of scope: action interpretation, samples, episodes, propositions,
  Semantic IR, synthesis, production repair or access, persistence,
  publication, deployment, and merge.

## Decision envelope

- Human reviewer and decision are externally supplied as `dhart54`,
  `full_issue_universe_review_authority_v1`, and
  `approved_complete_issue_universe`.
- Codex may assemble and verify the receipt but does not make or reconsider the
  universe-boundary decision.
- Stop before receipt creation if any approved digest, count, boundary, source
  identity, or closed-schema requirement cannot be reproduced.

## Definition of done

- [x] Exact baseline `d728e96a2786ab571ca08561f020a4b4947954e1`
  verified and focused branch created.
- [x] Manifest, action-set, universe-subject, boundary, source, accounting,
  FISA, expressive-action, cutoff, and latest-roll identities independently
  reproduced before receipt creation.
- [x] Detached receipt passes the closed schema and independent verifier.
- [x] Full-record validator shares the same canonical verification core and
  retains fail-closed/test-authority restrictions.
- [x] Tamper, current-state, governance, semantic, compilation, broad tests,
  and final diff checks were run and reconciled without an M1 blocker.
- [x] Final state preserves the seven-action benchmark and keeps all later
  semantic, production, and publication gates closed.

## Baseline and implementation sequence

- Baseline: PR #123 merged; V2 discovery is frozen through House roll 283 and
  July 23, 2026; the active seven-action benchmark remains publication-active.
- Implement canonical manifest/receipt verification, the detached receipt,
  independent V2 accounting verification, validator reuse, tamper tests, and
  narrow state/index reconciliation in that order.

## Discoveries and decisions

- Windows materializes governed JSON with CRLF, while approved artifact hashes
  use canonical Git/LF bytes. The existing full-record validator already
  permits exactly this canonical repository-byte equivalent; the shared helper
  preserves that rule.
- No accepted full-universe receipt exists yet. The receipt is placed directly
  under `docs/editorial/full_record_reviews/`, beside the current review state
  and outside `proposals`, matching detached canonical-receipt practice.
- The manifest `end_date` remains July 23 while `as_of_date` remains July 30;
  neither is normalized into the other.

## Validation results

- Pre-write V2 discovery validation: passed.
- Pre-write identities: manifest `17cc2d30...`, action set `51fff89a...`,
  universe subject `d778bff4...`; accounting `638 / 172 / 37 / 7 / 69 /
  59 / 0`; latest roll `283`; cutoff `2026-07-23`.
- Independent authority verifier: passed with all approved identities,
  accounting, boundary, FISA, source, and state constraints reproduced.
- Focused authority and full-record tests: 30 passed. Public catalog regression
  tests: 11 passed. Catalog discovery is schema-semantic and fail-closed; its
  canonical-byte assertion accepts only exact LF repository bytes or their
  exact Windows CRLF materialization.
- Semantic pipeline: seven checks passed. Documentation governance, terminology
  governance, Ruff lint, Ruff formatting for new files, Python compilation,
  JSON parsing, and `git diff --check`: passed.
- Final broad backend suite: exit 1; 1,040 passed, three failed, 33 skipped, and
  zero xfailed. The exact failures are the two editorial-presentation API tests
  under the documented invalid database URL and the ZIP source-manifest
  exact-byte test under Windows CRLF materialization.
- The identical command at clean baseline `d728e96a...` returned exit 1 with
  1,009 passed, 20 failed, 33 skipped, and zero xfailed. All three final-branch
  failure node IDs and failure modes were identical there. The additional 17
  baseline-worktree failures came from deliberately absent ignored local data
  caches and `frontend/node_modules`; they are not branch-caused.

## Production, rollback, blockers, and final reconciliation

- Production writes performed: none. Production access: none.
- Rollback: ordinary branch/file reversion only; no external state is changed.
- Blockers: none.
- Final reconciliation: the detached receipt establishes only the exact issue
  universe. The seven-action benchmark is unchanged, and interpretation,
  episodes, Semantic IR, synthesis, persistence, publication, production, and
  deployment remain outside this milestone.

## Successor boundary

- M2 mechanically establishes interpretation-source readiness for every action
  in the immutable 37-action universe. It does not generate action
  interpretations, establish policy episodes, construct propositions, compile
  Semantic IR, or perform synthesis.
- Action interpretation begins only in a later, separately authorized M3. M2
  has not begun on this branch.
