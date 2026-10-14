# Corrected isolated Health-provider validation prototype

The corrected prototype reduces direct prepare time by 39.7–43.1% in the final
paired desktop sample and preserves all six semantic output files byte for byte.
It is based on frozen `eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea`, with tested
source at `b606500f4e61848b2b15e3e510ff1641742f661d`. Independent review is
required before the sole Immigration owner integrates a current-head-aware
patch and generates a newly bound proof.

## Deliverables and scope

- [Adapter patch](adapter.patch): only repeated Health-provider qualification
  validation in `scripts/prepare_immigration_shared_candidate.py`; 128 added,
  six removed lines relative to the frozen head.
- [Control patch](controls.patch): 19 new controls; no original test changes.
- [Harness](run_prototype.py), [measurements](measurements.json) and
  [living plan](../../plans/health_provider_validation_prototype.md).

Branch `codex/health-provider-validation-prototype`, worktree `.w/cvo`.
Generic helpers, schemas, full-source checks, existing tests, canonical
source/candidate/proof artifacts and CI gates have zero diff. Root checkout,
`.w/ib`, PR198 and PR193 were not edited. Diagnostic draft PR227 remains separate
at `d9809414605a099abe3da31cf81f810d90f2b504`. No acceptance, publication,
production, deployment, merge or candidate integration occurred.

## Corrections prompted by independent review

Review of `c30f790c6d053acd93dc9add9c4a07a66aec4e88` found two correctness gaps.
Both were reproduced before correction:

1. In-place changes to the date format checker or type keyword validator allowed
   a warm session to borrow an earlier success, while direct and fresh validation
   rejected the real 115-action Health provider. Two differential tests failed.
   The prototype now snapshots both mutable registries. Changed or unobservable
   dependency configuration disables reuse for that invocation and calls the
   existing validator with the actual root.
2. A changed validator raising ValueError combined with a denied schema read
   surfaced PermissionError first. The combined regression failed. Cold
   validation now observes the schema lazily inside validator dispatch. Changed
   dependencies dispatch before eager schema observation. Cold and warm error
   class/message and absence of premature schema reads are tested.

A subsequent real-provider probe found that replacing TYPE_CHECKER also let a
warm session accept input rejected by direct/fresh validation. Observe TYPE_CHECKER,
ID_OF and the applicable-keyword dispatch configuration as dependencies. The new
real-provider type-checker regression compares identical rejection class/messages.
All 19 controls pass in the focused correction run (24.65s). The final labelled383 suite also passes on the exact committed source blobs.

Each prepare invocation owns one private deep-copied successful observation.
Every provider occurrence is still read and parsed; every qualification boundary
still observes its schema once. Reuse requires unchanged provider text, complete
type-strict payload, schema text, retained root identity/path, provider path,
known helper identities, member-field policy and mutable registry snapshots.
Booleans/numbers/signed zero cannot borrow a different validation; NaN is not
reused. Failures and separate invocations do not share results. All action guards
and 17 full-source passes remain.

## Measured behavior

Windows desktop, AMD64 Family 25 Model 97 Stepping 2 / AuthenticAMD, 16 logical
CPUs; Python 3.13.3, jsonschema 4.26.0, pytest 8.3.5. Baseline and prototype run
serially with identical frozen inputs and generic rules. First means the first
prepare in a fresh Python process; OS cache was not cleared. Warm means the
second prepare in that process, with a fresh invocation-local observation.
Desktop load was uncontrolled.

| Condition | Baseline seconds | Corrected seconds | Observed reduction |
| --- | ---: | ---: | ---: |
| First call | 11.1198 | 6.7039 | 39.71% |
| Warm call | 11.1703 | 6.3506 | 43.15% |

| Work per complete prepare | Baseline | Corrected |
| --- | ---: | ---: |
| Shared-core validation calls | 46 | 36 |
| Schema traversals | 100 | 90 |
| Full-source validation calls | 17 | 17 |
| Health-provider actual reads | 13 | 13 |
| Health qualification validations | 11 | 1 |

All six disposable JSON files produced by the actual serializer are byte-equal.
All six semantic values equal frozen generated JSON; current rendered packet
digests match; historical packet bytes remain unchanged. Two-call integration
controls verify 26 actual provider reads, 34 full-source passes and two full
Health qualification validations. These are two measured prepare calls, not a
CI estimate or an under-10-minute research/review guarantee.

## Exact source bytes and prior receipt correction

Prior c30f790 evidence recorded mixed-line-ending worktree adapter SHA256
`a53aa9a81f890b33bd54a043127f72da50d7281a358b6da9e1411d4e3769df54`.
Its Git blob SHA256 was
`9a79a040df79836c7a4f70bd38156199ca63ec8fdef5fe18d7a03923b83913ee`.
That raw working-byte receipt must not be described as an exact Git-blob binding.

Corrected validation explicitly materializes adapter, controls and driver from
the source commit's Git blobs as LF bytes. Their worktree SHA256 and Git-blob
SHA256 match; the harness verifies the filtered Git object IDs before and after
execution and records newline counts. The corrected adapter raw/blob SHA256 is
`5528ed497033e6be14871c57d9b9dda88683bf262513899bf2378054db03c396`.
No Git configuration or attributes were changed. A future Windows checkout may
materialize CRLF; use the separately recorded raw and filtered identities.

Measurements retain exact source-head bindings, raw receipt/XML/log hashes,
before-correction failures and corrected results, including explicit immutable
Health-provider SHA256. All 287 common protected file hashes match across fixtures. The final evidence commit
may update documentation, patches and receipts while these tested source blobs
remain identical.

## Full validation and historical proof boundary

Final sourceb606500f raw suite: 363 pass, one historical binding failure,
295.77s; no normalization. Final labelled suite: all 383 cases pass in 293.20s
(364 unchanged originals plus 19 controls), zero errors/skips/pytest warnings.
Exactly one expected proof hash read is adjusted in memory; all other proof
fields remain equal. All original364 case identities and protected bytes match.
Earlier source6bcd9339 labelled382 pass/318.66s preceded type-checker hardening.

The labelled run preserves all original assertions and test identities. Only
one read of the exact frozen Immigration proof substitutes the expected old
adapter hash with the corrected hash in memory. All other proof fields compare
exactly. No proof is written or regenerated. This establishes conditional
structural equivalence; it does not make the historical proof valid for changed
code or replace the canonical exact-head/synthetic-checkout CI contract.

Sole expected rule-file binding change in the current frozen Immigration proof:

```text
rule_files_sha256["scripts/prepare_immigration_shared_candidate.py"]
old:       d40f86e686467a23459a2818de7eb3cb044d3600107b65dea4354f88362402e6
corrected: 8809b7be8503290a992a1a292576ab34c597c6b5cb2c130b885112e3c31b71a1
```

These are canonical text digests, distinct from raw-file SHA256. Every historical
proof is preserved. Health's generic proof binding is unaffected.

## Reproduction and remaining boundary

Choose fresh output paths and use the exact selected commit as expected head:

```powershell
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root ../cvb --expected-head eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea --variant baseline --repeats 2 --profile --output .local/baseline-new.json
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root . --expected-head <selected-exact-head> --variant prototype --repeats 2 --profile --include-controls --output .local/prototype-new.json
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root . --expected-head <selected-exact-head> --variant prototype --mode suite-raw --output .local/raw-new.json
python -X utf8 docs/review_packets/health_provider_validation_prototype/run_prototype.py --root . --expected-head <selected-exact-head> --variant prototype --mode suite-normalized --include-controls --output .local/normalized-new.json
```

The frozen Markdown packet retains an older 44-input generation while frozen
JSON/current renderer has 65; preserve it as historical/follow-up. Initial
Windows cache-write denials remain in prior evidence. Full suites used reviewed
execution under the Windows runbook; no access bypass or approval rejection.

Adapter/control patches pass strict read-only apply checks against the frozen
baseline. Last read-only owner head was
`e50514114857e1fde3fd3f2d5d9863cd95179c0c`; no adapter/generic/shared-corpus/CI
change from frozen head was observed then. The owner must reconcile its actual
current head before applying a reviewed patch and generating a new proof at an
authorized checkpoint. Stop for independent review here. No prototype CI-gate
adjustment, integration PR, current-head application or editorial approval.

## Shutdown checkpoint

The already-running final suites finished before the requested01:55UTC writer
stop. No further research or long validation began after the shutdown boundary.
Local operations stop after saving/pushing this evidence increment; no automatic
resume. Independent review remains pending. On explicit resume, review this
exact source/packet and reconcile the owner's then-current head before any
authorized integration or new proof. Canonical proof CI remains expected to
reject the old binding; no prototype CI success is claimed.
