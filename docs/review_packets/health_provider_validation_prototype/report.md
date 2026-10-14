# Isolated repeated Health-provider validation prototype

This is an engineering prototype for independent review, based on frozen
`eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea`. The adapter-only patch reduces direct
prepare latency by 41.4–52.4% in the final paired sample, while preserving all
six semantic output files byte for byte. It is not integrated into PR198 or main.
The sole Immigration owner must apply a reviewed, current-head-aware patch at a
future coherent checkpoint and generate the newly bound proof.

## Deliverables and boundaries

- [Adapter-only patch](adapter.patch): only repeated Health-provider validation
  in `scripts/prepare_immigration_shared_candidate.py`.
- [Mutation-control patch](controls.patch):15 new controls; no existing test edit.
- [Reproduction harness](run_prototype.py), [measurements](measurements.json)
  and the living plan under `docs/plans/health_provider_validation_prototype.md`.

Worktree `.w/cvo`, branch `codex/health-provider-validation-prototype`, separate
from diagnostic PR227 and protected `.w/ib`. Canonical source/candidate/proof
artifacts, generic helpers, schemas, full-source checks and CI gates have zero
diff. No editorial acceptance, publication, production or deployment effect.

## Design and observations

Each `prepare()` creates one private successful validation record. Only the
existing Health-provider qualification path can use it. Every occurrence still
reads and parses the provider and freshly observes its schema at the original
validation boundary. Reuse requires equal provider text, complete type-strict
parsed payload, observed schema text, root identity/path, resolved provider path,
known validator/helper identities and member-field policy. Boolean/number and
signed-zero differences cannot borrow validation; NaN is never reused.

The cached payload is a private deep copy made only after successful validation.
The record retains the root object and compares identity, so numeric object-ID
reuse after collection cannot borrow an earlier validation.
There is no failure memoization, cross-invocation state, cached compilation,
source-validation reuse, path/mtime-only key, or altered per-action guard.
Changed authoring/capture continue through their original validation paths.

On a miss, the existing generic validator receives a narrow path facade that
returns the already freshly observed schema, without reading it a second time.
All other path access delegates to the real root/path. Review must preserve the
current generic contract: its schema read is UTF-8 at the named path. This is a
private prototype mechanism, not standing authority to bypass generic checks
or to assume future helper dependencies are unchanged.

## Final matched benchmark

Windows desktop, AMD64 Family 25 Model 97 Stepping 2 / AuthenticAMD, 16 logical CPUs;
Python 3.13.3, jsonschema 4.26.0, pytest 8.3.5. One benchmark process at a time,
identical frozen inputs and unchanged generic rules. First means fresh Python
process; OS cache was not cleared. Warm means second call in that process, with
a fresh invocation-local record. Desktop load was uncontrolled.

| Condition | Baseline seconds | Prototype seconds | Observed reduction |
| --- | ---: | ---: | ---: |
| First call | 13.0277 | 6.1954 | 52.45% |
| Warm call | 14.6049 | 8.5580 | 41.40% |

These are two paired calls, not a population/CI estimate. Earlier paired samples
were11.096/11.820s versus5.973/8.099s before signed-zero hardening, and
10.169/10.483s versus5.666/5.835s before final root-lifetime hardening. They are
retained as preliminary evidence, not the final code result. Profiling adds overhead and
is not used to estimate the speedup.

| Validation work per complete prepare | Baseline | Prototype |
| --- | ---: | ---: |
| Shared-core validations | 46 | 36 |
| Schema traversals | 100 | 90 |
| Full-source validations | 17 | 17 |
| Health-provider actual reads per invocation | 13 | 13 |
| Health qualification-provider validations | 11 | 1 |

All17 full2,587-source capture validations remain. Fresh schema observations
remain at every original boundary, including reuse hits. Integration controls
verify26 real Health-provider reads,34 full-source passes and two full Health
qualification validations across two distinct prepare calls.

Six actual disposable serialization outputs—core, mapping, projections, compiler
input, compiled IR and readable candidates—are byte-identical before/after.
All six semantic values equal the frozen checked-in JSON. Current generated
packet text and the unchanged historical packet digest also match before/after.
Repeated and profiled calls produce identical results and do not mutate inputs.

## Existing assertions and proof accommodation

The raw prototype run executes all 364 original cases unchanged:
**363 pass; one expected historical adapter-binding failure; 315.46s**. It is
`test_all_checked_in_generated_outputs_match_an_independent_replay`, with the
old/new adapter hash mismatch. No expected value is adjusted in this run.

The separately labelled run executes the same 364 cases plus all 15 new controls:
**379 pass in 368.26s, zero skips/warnings**. It changes only one in-memory read
of the exact historical Immigration proof's expected adapter hash. The harness
first verifies the proof's frozen text and old binding, substitutes exactly that
field and delegates every other read unchanged. Exactly one read is adjusted.
The original assertions remain intact. All other proof fields compare exactly.

This establishes conditional structural equivalence, **not validity of the
historical proof for the changed adapter**. No proof file is overwritten,
normalized on disk, or regenerated for candidate integration. Whole-suite
timings include different failure/normalization/control work and are not used
as a speedup claim. Diagnostic-stage baseline:364 pass/374.24s on this desktop.
No under-10-minute per-review research or CI savings claim follows.

The controls cover repeated fresh schema observation, provider text/parsed
mutation, private-copy isolation, booleans/numbers/signed zero/NaN, changed and
malformed schemas, permission errors with failure-order/message parity, changing
root/path/validator/member policy (including forced object-ID collision), non-caching of failures, separate sessions,
real prepare invocations, provider changes after a hit and full-source rejection
of changed unused capture rows after a hit.

## Sole expected proof delta

The exact old binding appears in only this current frozen JSON proof:

`docs/editorial/shared_candidates/house_119_immigration_20260916/generated/reproducibility_proof.json`

Expected future change:

```text
rule_files_sha256["scripts/prepare_immigration_shared_candidate.py"]
old: d40f86e686467a23459a2818de7eb3cb044d3600107b65dea4354f88362402e6
prototype: cf084f210afa6a416263fb08d2db8d34d67efd429760b44d77363a220c038d73
```

These are canonical text digests, not raw-file SHA256. All other rule, input,
core, mapping/projection/compiler/compiled/readable and controlled-proof values
remain equal. Health's generic-rule proof binding is unchanged. Preserve every
historical checkpoint proof. The owner must inventory the then-current head,
review any intervening adapter changes and generate a separately identified
newly bound proof; this prototype binding cannot be copied blindly into a later
checkpoint or used as approval.

## Reproduction

From `.w/cvo`, choose fresh output paths. Initial working prototype measurements
were frozen-head plus the recorded adapter diff; delivered head and script
hashes are preserved in the final resume receipt. After checkout, use its exact
head in `--expected-head`; frozen baseline remains the exact eb9d70ab snapshot.

```powershell
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root ../cvb --expected-head eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea --variant baseline --repeats 2 --profile --output .local/baseline-new.json
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root . --expected-head <delivered-head> --variant prototype --repeats 2 --profile --output .local/prototype-new.json
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root . --expected-head <delivered-head> --variant prototype --mode suite-raw --output .local/raw-new.json
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root . --expected-head <delivered-head> --variant prototype --mode suite-normalized --include-controls --output .local/normalized-new.json
```

The harness refuses unexpected head/scope/variant/proof changes and protected or
existing output destinations. It verifies input/rule/test/proof bytes before and
after execution and retains raw test XML/logs. Normalize only the explicitly
described expected adapter hash; never alter production or canonical evidence.

## Preserved adjacent findings and access

The frozen Markdown packet contains an older 44-input generation; frozen JSON
and the renderer contain 65. This stopped an initial new harness assertion on
the unchanged baseline. Preserve the old bytes as historical/follow-up; do not
repair the packet in this optimization lane. Actual baseline/prototype current
renderers are equal and all six frozen JSON outputs match.

The initial15-control run passed in20.28s but emitted two Windows cache-write
access denials under `.w/cvo/.local/pytest-cache-files-*`. Full suites used reviewed
execution as instructed by the Windows runbook and emitted no warnings. No
automatic approval rejection occurred. An initial redirect failed before tests
because `.local` was absent; corrected by creating the ignored diagnostic folder.

## Review and integration stop

Stop here for independent review. No candidate integration PR, CI-gate change or
current-head application is performed. Raw canonical-proof CI would still reject
the old adapter binding; the normalized local run must not replace that gate.
The sole Immigration owner applies a reviewed, current-head-aware patch and
regenerates a new proof at an authorized future checkpoint. Diagnostic PR227,
PR198, PR193, root checkout and `.w/ib` remain separate and unchanged.
