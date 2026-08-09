# M11C National Security Action Interpretation V1

Status: bounded correction to the reviewed head is implemented; final human
review is limited to the corrected S. 1071 and S. 1318 meanings and generic
structured-summary rule.

## Intent

Create a detached, source-bound candidate interpretation for each of the 81
actions that passed the accepted M11B readiness gate. Preserve
`house:119:2:278` / H.R. 8800 as an approved universe member that remains
source-blocked and uninterpreted.

## Baseline and authority

- Exact post-M11B merge base: `13f8ad58f3aee32eb90369e8b454830cfbbf130b`.
- Accepted M11A universe: 82 actions, content-bound membership authority only.
- Accepted M11B readiness: 81 ready and one `blocked_stage_mismatch`.
- Candidate judgments are non-authorizing and require human review.
- Human review of PR #135 head
  `1a5d60cea6e8712d2bc1e20019ac37505adf39ff` accepted the other 79
  meanings and all 81 exact-choice effects, while requiring bounded corrections
  to `house:119:1:320` / S. 1071 and `house:119:2:142` / S. 1318.

## Scope

In scope: exact-action meanings, exact member-position effects after meaning is
established, source/evidence bindings, explicit ambiguity and package-breadth
limits, deterministic candidate/decision separation, independent validation,
adversarial tests, CI coverage for the generic source-readiness suite, and
current-state documentation.

Out of scope: action-meaning acceptance, policy episodes, propositions,
Semantic IR, synthesis, public wording, publication, persistence, production
writes, deployment, and automatic merge.

## Implementation sequence

1. Reproduce M11A and M11B identities from the merged base.
2. Generalize the accepted Justice candidate contract only for cross-issue
   package-level bounded summaries and accepted-readiness accounting.
3. Build 81 candidates from exact accepted packets and one blocked accounting
   record without consulting party, sponsor, ideology, expected behavior, or
   downstream synthesis.
4. Generate a detached review dossier, empty human-decision template, and
   content-addressed parity manifest.
5. Independently validate source bindings, candidate/action equality, digests,
   ambiguity states, and all false downstream authorities.
6. Run adversarial, Justice, full-record, governance, schema, formatting, and
   repository-integrity regressions.
7. Commit, push, open a draft PR, verify CI, and stop for human review.

## Definition of done

- [x] Exact 82 = 81 eligible candidates + one source-blocked action.
- [x] Every eligible action has one candidate and one empty human decision unit.
- [x] Every claim binds to accepted exact-action evidence.
- [x] H.R. 8800 remains blocked and has no candidate.
- [x] Broad packages are not reduced to individual-policy positions.
- [x] Deterministic regeneration and independent validation pass.
- [x] Justice behavior and accepted publication state are unchanged.
- [x] CI durably runs `backend/tests/test_full_record_source_readiness.py`.
- [x] No downstream authority, runtime behavior, protected-file access, or
      external write occurs.

## Stop conditions

Stop if an eligible action lacks a safe bounded interpretation, exact upstream
identity changes, H.R. 8800 would need recovery, a generic evaluator requires an
issue-specific exception, Justice regresses, or scope crosses a forbidden
downstream boundary.

## Validation results

- M11A/M11B recomputation and the independent M11C validator pass at exact
  82/81/1 accounting and 211 eligible-action source bindings.
- Deterministic M11C regeneration and all three Draft-07 M11C schemas pass.
- The focused generic, authority, readiness, Justice decision, Justice Semantic
  IR, and full-record contract set passes 126 tests, including six new
  structured-summary and governed two-action regressions.
- Content-addressed preservation checks prove that the other 79 meanings, all
  81 position effects, and the eight previously accepted package meanings are
  unchanged from reviewed head `1a5d60c`.
- Justice decision implementation, Justice M5R1 Semantic IR, and the
  full-record contract validators pass without changing accepted Justice state.
- The historical Justice V4 candidate validator retains a pre-existing frozen
  V1 dossier byte-digest mismatch even in a clean tracked-only archive. That
  tracked file is unchanged by M11C; the frozen evidence and validator were not
  rewritten to conceal the baseline limitation.
- Documentation and terminology governance, deterministic JSON parsing,
  semantic schema regression, Ruff, formatting, compilation, ancestry, and
  diff checks pass.
