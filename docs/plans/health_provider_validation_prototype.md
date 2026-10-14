# Isolated Health-provider validation prototype

## Envelope

Only repeated Health-provider qualification in the Immigration adapter, on frozen
`eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea`. Worktree `.w/cvo`, branch
`codex/health-provider-validation-prototype`. No generic helper, schema, existing
test, source/candidate/proof, CI gate, acceptance or publication change. Root,
`.w/ib`, PR198 and PR193 are protected. Diagnostic PR227 remains separate at
`d9809414605a099abe3da31cf81f810d90f2b504`. No integration, merge or deployment.

## Implementation and review corrections

One private successful validation observation per prepare invocation. Read and
parse every provider occurrence; observe the schema once at every qualification
boundary. Reuse requires complete type-strict payload, provider/schema text,
root identity/path, provider path, known helper identities, member-field policy, type-checker/ID/applicable-keyword configuration
and snapshots of the keyword-validator and format-checker registries. Store a
deep copy only after success. Preserve every full-source pass and action guard.

Independent review of `c30f790c6d053acd93dc9add9c4a07a66aec4e88` found:

1. In-place registry changes borrowed the earlier success. Real-provider
   differential regressions reproduced two invalid acceptances. Snapshot both
   registries; changed or unobservable configuration disables reuse for that
   invocation and dispatches the original validator with the actual root.
2. A changed validator and denied schema read surfaced the wrong first error.
   The combined regression reproduced PermissionError instead of ValueError.
   Cold validation now observes the schema lazily inside original dispatch;
   changed dependencies dispatch before any eager schema read.
3. Prior code-file SHA256 described materialized worktree bytes; the adapter
   contained mixed line endings and differed from its Git blob. Preserve that
   historical receipt, distinguish both identities, and rerun corrected code
   materialized as exact Git-blob LF bytes. Do not change Git configuration.

A real-provider TYPE_CHECKER replacement probe also reproduced a warm invalid
acceptance after the first corrections. Snapshot that configuration, ID_OF and
applicable-keyword dispatch; the 19th control verifies direct/fresh/warm rejection
parity. Health-provider bytes are explicitly protected in the final manifest.

Final tested source commit: `b606500f4e61848b2b15e3e510ff1641742f661d`.
19 focused controls pass in 24.65s. No review finding changes candidate meaning.

## Verification sequence and current resume

1. Reproduce review findings; correct adapter and add three regressions. Complete.
2. Commit source and materialize the three tested source/driver files as exact
   Git-blob bytes. Harness checks their committed filtered identities and records
   worktree raw SHA256, Git blob SHA256, object IDs and newline counts. Complete.
3. Serial paired prepare measurement on unchanged frozen inputs. Complete:
   baseline 11.1198/11.1703s versus corrected 6.7039/6.3506s, first/warm calls.
   OS cache not cleared, desktop load uncontrolled, one process at a time.
   All six actual serialized JSON files are byte-equal; all 17 full-source passes
   remain (shared-core validations 46 to 36, schema traversals 100 to 90).
4. Raw 364 existing tests; retain the expected historical adapter-hash failure.
   Then labelled 383 tests (364 originals plus 19 controls) with exactly one
   in-memory expected proof hash substituted. All other proof fields and
   assertions stay intact. No canonical proof write. Complete: raw363 pass/sole old binding failure in
   295.77s; labelled383 pass/293.20s, no errors/skips/pytest warnings, exactly
   one adjusted expected proof read. All original364 case identities preserved.
5. Rebuild patches, measurements and report; check patches read-only against
   frozen baseline, commit/push evidence, stop for independent review. Packet/patch verification
   complete; commit/push is the final checkpoint operation.

Final tests must bind the same adapter, controls and driver bytes as the paired
measurement. Final documentation commit may add evidence but cannot change those
tested sources. Prior c30f790 results remain historical, superseded by this run.

## Proof and integration boundary

Historical adapter text binding:
`d40f86e686467a23459a2818de7eb3cb044d3600107b65dea4354f88362402e6`.
Corrected adapter text binding:
`8809b7be8503290a992a1a292576ab34c597c6b5cb2c130b885112e3c31b71a1`.
Only the Immigration reproducibility proof has this old rule-file binding.
Local normalization establishes conditional equivalence; it does not make the
historical proof valid for changed code or replace exact-head CI.

The sole Immigration owner applies a reviewed, current-head-aware patch at an
authorized future coherent checkpoint and generates a newly bound proof. Last
read-only owner head: `e50514114857e1fde3fd3f2d5d9863cd95179c0c`.
No adapter/generic/shared-corpus/CI change from the frozen head was observed then.
No current-head integration is authorized in this lane.

## Preserved findings and limits

Frozen Markdown packet retains an older 44-input generation; frozen JSON/current
renderer has 65. Preserve it as historical/follow-up. Compare current baseline
and prototype renderer exactly; do not repair editorial artifacts here.

Prior Windows cache-write denials are preserved in the earlier report. Full
suites use reviewed execution under the documented Windows temporary-directory
rule. No approval rejection or access bypass. Benchmark improvements alone do
not establish CI savings or an under-10-minute research/review goal.

## Shutdown stop and explicit resume

User shutdown deadline2026-10-14 02:00UTC; preferred writer stop01:55UTC.
Final existing suites finished before that boundary. No new research or long
validation started after the instruction. Save/push this coherent evidence
increment and stop. Do not resume automatically. On explicit user resume:
independent review of exact packet/source, then sole owner current-head
reconciliation and separately authorized integration/new proof. No merge,
deployment, publication or canonical proof write is authorized here.
