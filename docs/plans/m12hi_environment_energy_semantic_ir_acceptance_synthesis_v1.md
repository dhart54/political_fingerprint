# M12H/I Environment & Energy Semantic IR Acceptance and Synthesis Candidates V1

## Intent

Mechanically implement the independently accepted M12G Behavioral Semantic IR
without changing any reviewed content, validate that acceptance completely, and
only then compile detached M12I synthesis candidates from the accepted
proposition records.

## Exact boundary

- Accepted PR #153 head: `ab35caf3fb8ff80961da990b742bd42f7c4e56ba`.
- Reviewed base: `450a759c5a2d0eaf767e68bc999c7d3ec8e9ca1e`.
- Exact post-M12G merge main:
  `d3bc0fddad701e0621c87857ed80288c23a867aa`.
- M12G candidate file/subject SHA-256:
  `f97b123e97b3a11d5320806857a02ea1e3c7604f36bc2c6b7373185feacba3ca` /
  `4cc502b76e1f603eef8276bf8632daa25153b0e5d07cf2e99e1c27514c36d023`.
- In scope: generic contract corrections, exact M12H acceptance, independent
  M12H validation, detached M12I candidates, complete accounting, regressions,
  one branch, and one draft PR.
- Out of scope: M12J, synthesis acceptance, public wording, site integration,
  publication, persistence, database/production writes, deployment, and the two
  protected user-owned ZIPs.

## Internal gates

1. Guarded-merge exact PR #153 and branch from exact resulting main.
2. Generalize Behavioral Semantic IR authority and implementation bindings while
   retaining the historical M11H vocabulary and byte-identical artifacts.
3. Accept all three M12G propositions as written, preserve the complete
   63-episode disposition ledger, and independently validate M12H.
4. Only after M12H passes, generalize synthesis bindings and the zero-candidate
   fail-closed outcome while preserving byte-identical M11I output.
5. Compile, validate, document, and publish detached M12I candidates, then stop
   for independent substantive review.

## Completed M12H gate

- [x] Three exact `accept_candidate_as_written` decisions; no revisions or
  rejections.
- [x] Three repeated patterns, zero trajectories, zero notable choices, 13
  primary episodes, and zero primary overlap.
- [x] Complete 63-episode ledger: 13 primary, 25 contrast-only, 24 no-safe, and
  one `unused_non_directional_evidence` episode.
- [x] H.R. 6387 remains non-directional and ownerless; H.R. 471 and H.R. 3898
  remain whole-package singletons with no component-level promotion.
- [x] All evidence lineage resolves through accepted M12F episodes and accepted
  M12D action interpretations.
- [x] Historical M11H artifacts remain byte-identical.
- [x] M12H was independently validated before M12I generation.

## M12I review frontier

- [x] One bounded `uniform_direction` candidate uses all three accepted M12H
  proposition records as `primary_support` inputs.
- [x] Thirteen unique episodes and 13 unique actions are deduplicated lineage,
  not independent semantic inputs.
- [x] All three accepted propositions are explicitly accounted; none is
  intentionally standalone.
- [x] No raw action, raw vote, contrast-only, no-safe, non-directional, or
  whole-package component material enters synthesis directly.
- [x] A separate interpretive-boundary candidate was rejected as duplicative;
  no mechanism divide or no-common-throughline candidate is supported.
- [x] Zero-candidate output is valid when all accepted propositions are
  explicitly standalone; every nonzero candidate still requires at least two
  accepted inputs.
- [x] The human decision template is empty and every downstream authority is
  false.
- [x] Draft PR #154 hosted checks passed on exact accepted head
  `95a7c59cd1876c7934fea9547008e2b8e86e8be0`; independent substantive review
  accepted the sole candidate exactly as written.

## Validation approach

Run M12A-I validators, historical M11A-N and Justice regressions, the Behavioral
Semantic IR and synthesis suites, publication/API checks, schema/JSON/docs and
terminology checks, Ruff, formatting, compilation, ancestry/scoped-diff checks,
and `git diff --check`. Established unchanged-file Windows byte failures are
reported separately; hosted Linux CI is the authoritative broad gate for that
baseline condition.

## Stop condition

This stop condition was satisfied at PR #154. M12I is now an immutable accepted
checkpoint and M12J/K proceeds under its separate plan and authority layers.

## Local validation results

M12A-I validators pass, as do M11A-K and M11N validators, deterministic M11H,
M12H, M11I, and M12I rebuild checks, the 38-test focused Behavioral Semantic IR
and synthesis suite, Semantic IR validation (12 development and four held-out
references), documentation, terminology, JSON/schema, Ruff, formatting,
compilation, ancestry, scoped-diff, historical M11H/M11I byte-compatibility, and
`git diff --check`. The integrated governed regression set reports 534 passes and
one unchanged Windows checkout byte-line-ending failure in the historical policy
episode acceptance fixture. M11L's historical parity validator reports the same
established Windows exact-byte class. No frozen historical file was rewritten;
hosted Linux CI remains the authoritative broad gate.
