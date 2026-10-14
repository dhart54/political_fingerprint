# Isolated Health-provider validation prototype

## Intent and envelope

Implement and measure only repeated Health-provider validation inside the
Immigration adapter, on frozen `eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea`.
Separate worktree `.w/cvo`, branch `codex/health-provider-validation-prototype`.
Diagnostic PR227 remains at `d9809414605a099abe3da31cf81f810d90f2b504`.
Root, `.w/ib`, PR198, PR193, candidate/source artifacts and all historical proofs
are protected. No generic helper/schema/full-source/CI-gate changes. No
acceptance, publication, deployment, production write or candidate integration.

## Design decision

One successful Health-provider validation record lives inside one `prepare()`
invocation. Each occurrence still reads/parses its provider and observes its
schema once, in the original order. Reuse requires matching observed provider
text, complete type-strict parsed payload, schema text, root identity/path,
resolved provider path and validator identity. On a miss, the existing generic
validator consumes the already observed schema through a narrow path facade;
there is no second schema read. All other validation and per-action guards stay
in place. Store a private deep copy only after success. No failure caching,
cross-invocation state, or path/mtime-only binding.

## Validation method and proof boundary

- Benchmark baseline/prototype serially on the same frozen inputs and hardware.
- Compare all generated semantic JSON values and packet text; only the adapter
  rule-file hash is expected to differ in the reproducibility proof.
- Run every existing assertion unchanged. First run raw, preserving the expected
  old adapter-binding failure. Then use an explicit test-only in-memory expected
  proof adjustment: verify the exact frozen proof and old binding, substitute
  only the adapter hash on that proof read, and delegate every other read
  unchanged. No disk proof write and no claim of historical proof validity.
- Target provider/schema/root/typed payload/input changes, failures/order/message,
  no cross-invocation reuse, and continued full-source checks.
- Preserve exact before/after inputs, rule/source/test hashes and failure evidence.

## Sequence and resume

1. Reconcile instructions/frozen state and design. Complete.
2. Adapter-only prototype and focused mutation controls implemented; final tests
   add type-strict boolean/number/signed-zero comparison and failure-order control.
3. Preliminary serial timing complete. Baseline11.096s first/11.820s warm;
   prototype5.973s first/8.099s warm. All six generated semantic outputs and both
   current-renderer/historical-packet digests match. Profile core validations
   46->36, schema traversals100->90, full-source passes17->17. The prototype
   measurement predates the signed-zero hardening; remeasure final code.
   Raw364-case suite running in exec session43652, one failure visible so far.
   Wait for final report and confirm it is solely the historical adapter binding.
   Then run the labelled hash-normalized suite plus all15 new controls.
4. Adapter/control patches and review report generated. Final review tightened
   root identity lifetime: retain the root object and test forced object-ID reuse.
   Rerun final validation/timings and regenerate exact patch/evidence, then scoped
   commit and independent review; no candidate integration.

The sole Immigration owner decides how to apply a reviewed current-head-aware
patch at a future coherent checkpoint and regenerates the newly bound proof.
Expected proof delta is inventoried, never applied to canonical evidence here.

## Current results and limits

Adapter prototype and15 mutation controls implemented;15 pass in20.28s. Two
pytest cache-write access denials under `.w/cvo/.local/pytest-cache-files-*`
remain warnings; use reviewed execution for complete suites per the runbook.
Initial redirect failed because `.local` did not exist; created that ignored
directory and ran the tests. No false pass claimed for the failed launch.

The first baseline measurement stopped on a new harness assertion: the frozen
Markdown packet retains an earlier44-input generation while generated JSON and
the renderer have65. Classify as historical/follow-up, preserve all bytes and
do not reconcile in this lane. Compare both the immutable historical packet and
the current baseline/prototype rendered text exactly; semantic JSON comparisons
continue to require equality to all six frozen generated outputs.

Original baseline evidence remains in PR227 and
`.w/cvp/.local/`; frozen baseline checkout `.w/cvb` remains clean. Cache warnings
are recorded above; no production effect. Benchmarks run one process
at a time. CI savings do not establish the under-10-minute research/review goal.

## Validation before final root-identity lifetime hardening

- Current adapter tested: text binding
  `dbaf91592a4c71eaeb9bcf81cb60f7c8dc13ccf0b3aedab1475fdc9791c54bf9`.
- Raw364:363 pass, sole old adapter binding mismatch/366.51s. No proof adjustment.
- Labelled379:all364 original cases plus15 new controls pass/380.22s,
  zero skips/warnings. Exactly one expected proof read is adjusted in memory;
  historical proof/input/rule/test bytes remain unchanged.
- Final same-runner paired prepare:10.1691/10.4831s baseline versus
  5.6661/5.8349s prototype first/warm;44.28%/44.34% observed reduction.
- Actual six disposable serialized JSON files are byte-identical; all frozen
  semantic JSON values, rendered text and historical packet digests match.
- Full-source validation17->17; core validation46->36; schema traversal100->90.
- Only protected-file hash difference is the adapter; other evidence manifests
  are identical. Original364 test identities are unchanged.
- Patches, normalized measurement receipt, explicit proof-delta inventory and
  review report are under `docs/review_packets/health_provider_validation_prototype/`.
- No canonical proof regeneration, CI modification, source/candidate edit,
  production/publication/deployment or editorial approval. Next: independent
  review; sole owner decides current-head-aware integration at a future checkpoint.

## Current resume point

Final code now retains the root object so numeric IDs cannot be reused after
collection. One existing root-control case adds a forced-ID-collision check;
the control case count remains15. Previous366.51s raw/380.22s labelled results
and44.3% paired sample are retained as before-hardening evidence, not the final
hash. Next: final15 controls, raw364 and labelled379 with the exact new code,
serial same-runner remeasurement, exact patches/manifest/report update and commit.

Final hardening validated:15 controls pass/21.71s; raw364 gives363 pass and only
the historical adapter binding mismatch/315.46s; labelled379 pass/368.26s with
zero skips/warnings and one in-memory expectation read. Final binding is
`cf084f210afa6a416263fb08d2db8d34d67efd429760b44d77363a220c038d73`.
Final paired calls13.0277/14.6049s baseline versus6.1954/8.5580s prototype,
52.44%/41.40% observed reduction. Actual six serialization files and current
rendered output are equal; all286 common protected manifest entries match, with
the adapter the sole differing dependency. Patches/receipt updated to exact final source. No further implementation
or test changes remain; next is scoped review/commit and independent handoff.

Live owner work advanced independently to
`e50514114857e1fde3fd3f2d5d9863cd95179c0c` while final validation runs. Frozen
benchmark remains eb9d70ab; this lane did not edit or integrate that worktree.
Read-only diff shows no adapter/generic/shared-corpus/CI file change between
those heads. Owner still must assess its current head before later application.

Final root-lifetime code validation now complete: raw364 has363 pass and only
the expected old proof binding failure/315.46s; labelled379 pass/368.26s,
zero skips/warnings. Actual final paired measurements are13.0277/14.6049s
baseline and6.1954/8.5580s prototype,52.44%/41.40% reductions. They supersede the
earlier paired numbers above for delivered code. Exact current binding:
`cf084f210afa6a416263fb08d2db8d34d67efd429760b44d77363a220c038d73`.
All six actual serialization files remain byte-identical; all original364 case
identities and the286 common dependency hashes match. Exact patches regenerated
and checked read-only against the frozen baseline. Handoff is independent review;
no code/CI/proof/owner-branch integration remains authorized in this lane.
