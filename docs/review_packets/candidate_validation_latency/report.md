# Candidate validation latency: coordination proposal

The measured opportunity is repeated validation of large, unchanged inputs in
the Immigration-owned reuse adapter. This lane makes **no runtime or test
optimization**: the measured owning helpers are outside the refined write scope.
The profiling harness executes the existing checks without patching validators,
sources, schemas or preparation. No candidate output or conclusion is changed.

## Exact baselines and ownership

Live GitHub main was `9337ed516621875709f6bb33ca4f9fb20c4ef2b7` on discovery.
The main-based feature worktree is `.w/cvp`; the detached benchmark snapshot is
`.w/cvb` at PR198 checkpoint225 `eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea`.
The active `.w/ib` remains untouched. Reserved PR193 remains
`a1ea3035606d6b47987dea5606513a2d5e6ad71e`.

PR198 and PR193 change lists contain none of the generic preparation/shared
corpus/research test targets. The generic helper and both shared-domain/corpus
tests are also identical between current main and PR198. Compare PR193 against
its own base `2049eaf25e2ab9f197dafe6ad97d9f8e0cc3c257` for ownership: a direct
old-feature/current-main diff includes unrelated intervening main changes.
Other open PRs on discovery: 223, 209, 199, 187 and 100; no latency owner found.
The operating brief remains unmerged PR199 guidance, not live-state authority.

## Reproduction and conditions

Run from `.w/cvp` with only one benchmark process active:
Choose a fresh output path on repeat runs; existing measurements are preserved.

```powershell
python docs/review_packets/candidate_validation_latency/profile_candidate.py --root ../cvb --expected-head eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea --domain immigration --repeats 2 --profile --output .local/immigration-prepare.json
```

The first call is fresh-process; the next is warm in the same process. OS disk
cache was not cleared. The snapshot had just been checked out/read. This is not
a claim of hardware cold-cache latency. Windows AMD64 processor signature
`AMD64 Family25 Model97 Stepping2, AuthenticAMD`; Python3.13.3, pytest8.3.5,
jsonschema4.26.0, 16 logical CPUs. Other desktop/research processes may run;
measurements are single-threaded and have no exclusive-machine guarantee.
No parallel benchmark workers, dependency/config changes or database access.
Hosted evidence uses Ubuntu/Python3.11.17 and is a separate measurement.

The fixed Immigration fixture has 65 authored actions and 2,587 captured sources;
`sources.json` is 34,111,656 bytes. Its reused Health core has 115 actions and is
19,338,181 bytes. Import and initial input load are measured separately.

| Unchanged checkpoint225 prepare | Wall seconds | CPU seconds |
| --- | ---: | ---: |
| Fresh-process first call, initial run | 10.5490 | 10.4375 |
| Same-process warm call, initial run | 10.1195 | 10.1094 |
| Profiled call, initial run | 15.5461 | 15.5469 |
| Fresh-process first call, hardened harness rerun | 10.9898 | 10.8906 |
| Same-process warm call, hardened harness rerun | 11.7297 | 11.3594 |

The final Immigration profile is21.1195s and retains the same16 reuse/17 full
capture/46 core/100 schema call counts. The main Health control is0.8066s first,
0.7962s warm; its profile is1.2097s. These are different fixtures, not a speedup
comparison. Warm calls are not consistently faster, and profiler overhead varies.
Thirteen referenced provider files, loaded inputs, tracked cleanliness, rule/input
bytes and exact head remain unchanged in the hardened Immigration run.

[Normalized measurements](measurements.json) retain all timing values, product
digests, fixture/rule/provider/test hashes, class counts and the slowest30 cases.
Profile rows retain the top20 cumulative functions plus watched functions;
absolute checkout/library roots are replaced by explicit labels. Raw receipt
hashes are retained; full raw JSON/XML/logs remain under `.w/cvp/.local/`.

The profiler adds overhead; its cumulative times identify ownership, not a
predicted wall-time saving. Every call produces equal digests for core, mapping,
projections, compiler input and compiled IR. No optimized timing exists because
no implementation is authorized in the measured owning path.

## Diagnosis

Initial cProfile observations for one complete unchanged prepare:

| Function | Calls | Cumulative seconds |
| --- | ---: | ---: |
| Immigration `prepare` | 1 | 15.5440 |
| `_prepare_reused_action` | 16 | 13.6664 |
| `_prepare_candidate_core_augmentation` | 11 | 11.4503 |
| `validate_shared_action_core` | 46 | 11.2581 |
| `_validate_schema` | 100 | 8.6049 |
| Common `prepare` | 17 | 3.1734 |
| `validate_sources` | 17 | 2.0364 |
| `digest` | 49,642 | 4.8204 |
| All `Path.read_text` | 130 | 0.5744 |
| All `json.loads` | 130 | 0.4323 |

Cumulative rows overlap and must not be added. The profiled validator constructor
row, including recursively evolved internal validators, is about0.479s across
542,731 calls; this is not100 top-level constructions. Reading/parsing a cached
schema alone does not address the dominant actual validation traversal.

The adapter calls common preparation once for ordinary actions and once per
16 reused actions, each with the full source capture. Eleven augmentation rows
separately load and validate the same full Health provider. The diagnosis is
grounded in call counts plus the current call sites, not inferred from CI alone.

The large suites already prepare their baseline once per class. The initial
full-lane timing attributes346.96s to209 Immigration cases and32.28s to133
Health cases;15 shared-corpus cases take0.274s and seven research cases0.001s
(JUnit per-case sums include setup/teardown and exclude runner overhead).
Moving the invalid-input calls to an
earlier private helper or narrowing their capture would weaken the integration
contract. There is no measured worthwhile independent test-only improvement.

## Coordinated implementation envelope

Recommendation: let the Immigration implementation owner run a separately
authorized, bounded engineering increment. Start with per-invocation handling
of repeated preserved-provider inputs and full source capture; keep action
construction, exact wrappers, compiler checks and final aggregate validation.
Do not alter source semantics, schema requirements or publication state.

Requirements before accepting any design:

1. Retain source seal checks on every supplied source, including unused rows.
   Preserve all exact-action, provider, wrapper, member and whole-output checks.
2. Any reuse must be scoped to one invocation and bound to exact observed bytes
   and every validation dependency. Path/head/mtime-only caches are unsafe.
   Changed capture, provider, schema, root or monkeypatched reads must receive
   fresh validation. Mutable caller objects cannot borrow old validation.
3. Preserve lazy failure order and exception class/message/path. Same-owner
   positive output equality alone cannot establish invalid-input equivalence.
4. Compare every core/mapping/projection/compiler/compiled/readable result and
   full generated packet bytes on the exact frozen fixture. Retain all current
   assertions and negative cases, and add same-process changed-input/provider
   and dependency-mutation regressions for the proposed reuse mechanism.
5. Benchmark baseline/optimized fresh-process and warm calls on the same
   fixture/hardware; repeat the complete364-test lane unchanged. Profile overhead
   and CI variability cannot be presented as measured speedup.

The simplest first coordination target is candidate-owned repeated Health
provider validation. Moving common full-source validation requires changing
the hash-bound generic helper and therefore expands proof consequences. The
owner should decide the exact API after failure-order/equivalence analysis;
this report does not authorize a cache or private bypass API.

## Exact proof consequences and safe integration

In the frozen checkpoint225 tree, these current proof artifacts bind changed
helper identities:

- `docs/editorial/shared_candidates/house_119_immigration_20260916/generated/reproducibility_proof.json`
  binds `scripts/prepare_immigration_shared_candidate.py`.
- Both Immigration and Health
  `docs/editorial/shared_candidates/house_119_health_20260916/generated/reproducibility_proof.json`
  bind `scripts/prepare_shared_domain_candidate.py` and
  `backend/app/semantic_ir/shared_corpus.py`.

Proof values are text-canonical `digest(read_text(...))`, distinct from the
profiling receipt's raw-byte SHA256. Existing bindings at checkpoint225:

```text
prepare_immigration_shared_candidate.py d40f86e686467a23459a2818de7eb3cb044d3600107b65dea4354f88362402e6
prepare_shared_domain_candidate.py      acad448d612df797d0cdde3b9d488ca69edcbef5495a0c5cadd01ee8ba0e8b58
shared_corpus.py                        7545c6ecbf5b8e2b6cff0c3ef3fdd8db0154697432c2bf51e4afe70c4332d2bd
```

Preserve checkpoint224/225 and prior proofs as exact historical evidence. Do not
silently repair current proof hashes or regenerate candidate conclusions here.
The owner must reserve a new checkpoint, inventory the exact proof bindings on
the then-current head, generate a new separately identified proof, and retain
prior input/output identities and explicit supersession evidence. Helper hash
changes need review even if every semantic output is identical. New proof
identity does not confer editorial acceptance or publication authority.

Apply the reviewed engineering change only through the owning workstream and
its authorized main integration procedure. Do not integrate main into `.w/ib`
from this lane. Exact feature-head CI and synthetic integration-tree gates keep
their current contracts. Independent review remains required before merge.

## CI evidence and validation

[Checkpoint224 run38464592096](https://github.com/dhart54/political_fingerprint/actions/runs/38464592096)
has361 passing candidate-lane tests in630.49s.
[Checkpoint225 run38473383452](https://github.com/dhart54/political_fingerprint/actions/runs/38473383452)
checks out `eb9d70ab` and has364 passing tests in536.37s. Its ten jobs succeeded.
The four-module command is shared-domain, shared-corpus, research and Immigration
tests;209 is the Immigration-only count, not the complete CI lane. Raw logs
confirm the command and positive summary. This report does not rerun or modify
those historical CI receipts.

The workflow run windows are824s at checkpoint224 and727s at checkpoint225,
matching the supplied evidence; they include other jobs and runner overhead.

Initial desktop run:363 passed, one failed, no skips in380.25s. The failed
`test_spending224_qualification_conserves_shared_health_truth` uses an unchanged
`read_text()` without an encoding at test line22. Windows CP1252 cannot decode
byte0x9d in the UTF-8 Health core. This is a baseline platform defect, not a
candidate semantic failure. Three pytest cache-write warnings reported
Windows access error5 under `.w/cvb/.local/pytest-cache-files-*`.
The unchanged full suite was rerun with process-local Python `-X utf8` and
reviewed execution: **364 passed in374.24s, zero failures/skips/warnings**.
No file, assertion, codec error handling or check changes. Identical test identity
digests verify both runs exercised the same364 cases. The UTF-8 run's class sums
are341.706s Immigration,31.831s Health,0.241s corpus and0.000s research (rounded
JUnit measurements, not proof of zero execution time).

Reproduce from `.w/cvb`:

```powershell
python -X utf8 -m pytest -q backend/tests/test_shared_domain_candidate.py backend/tests/test_shared_legislative_corpus.py backend/tests/test_shared_candidate_research.py backend/tests/test_immigration_shared_candidate.py --durations=30 --junitxml=../cvp/.local/utf8-tests.xml --basetemp=.local/utf8-profile-basetemp -o cache_dir=.local/utf8_pytest_cache
```

Harness syntax and wrong-head rejection pass; wrong head exits2 and writes no
measurement. Recursive provider dependency discovery controls pass. The harness
checks exact head, tracked cleanliness, referenced provider/input/rule bytes and
loaded input immutability; it compares all five products on every call.
Protected checkout output destinations and existing output files are rejected
before imports/measurement; both controls pass. No validators are patched or
failures softened. Both snapshots' tracked state and `.w/ib` head were checked
unchanged after validation. Markdown format/fence and diff checks pass.

Only this plan/report, profiling harness and normalized measurements are proposed.
The feature draft PR records exact delivered head and hosted CI; its purpose is
diagnosis/coordination review, not a runtime optimization or merge request.

## Limits and next action

No optimized runtime, speedup, review-time goal achievement or CI saving is
claimed. Structural validation is one component of review/research duration;
the under10-minute per-review goal still needs its own representative research
measurement. The next decision is owner coordination for a bounded, equivalent
reuse optimization with a new proof checkpoint. Runtime implementation stops
at this boundary in the independent lane.
