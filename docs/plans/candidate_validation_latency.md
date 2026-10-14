# Candidate validation latency

## Intent and outcome

Measure candidate validation on this Windows desktop without weakening checks.
Deliver a test-only improvement if measurements support one; otherwise deliver
an owner-coordinated proposal for the measured bottleneck. Review stops before
merge. No production, publication, deployment, configuration or schema writes.

## Scope and decision envelope

Main-based feature branch `codex/candidate-validation-profile`, `.w/cvp`.
Disposable exact Immigration snapshot `.w/cvb` may be benchmarked. Root checkout,
`.w/ib`, PR198 and PR193 are protected. No candidate conclusions or fixtures change.
The scope refinement prohibits edits to rule-bound helpers, schemas, compilers,
or candidate-owned adapters. Every assertion and invalid-input path must remain.

Expected diff: plan, reproducible profiling harness and measured report; tests
only if a worthwhile independent optimization is established. No regeneration.

## Baseline and instructions

- GitHub main verified `9337ed516621875709f6bb33ca4f9fb20c4ef2b7`.
- PR198 open draft: `eb9d70ab3ca28ea3ee11eae572d2f2befd6f4aea`.
- PR193 open draft: `a1ea3035606d6b47987dea5606513a2d5e6ad71e`.
- Other open lanes: 223 voter diagnosis; 209 combined validation; 199 operating
  brief; older publication-preparation lanes. No latency owner found.
- Main and PR198 have identical generic preparation, shared-corpus and both
  shared-domain/corpus test files (verified by Git diff).
- Root contains unrelated tracked/untracked work; leave untouched.
- Read global/root AGENTS, current-main AGENTS, operating model, development test
  instructions, plan/PR runbooks, interpretation principles and pipeline preread.
- Operating brief read from unmerged PR199's `.w/dot-brief/docs/DOT_OPERATING_BRIEF.md`;
  it grants no authority. No repository/ancestor `.agents/skills` or local memory
  entries found. Relevant test rules use workspace-local pytest basetemp.

## Sequence and definition of done

1. Reconcile ownership and create isolated exact-head worktrees. Complete.
2. Run single-process bounded profiling with cold-process/warm-call labels,
   input/rule identities, test counts and timings. Direct prepare profile complete;
   full four-module first run and UTF-8 rerun complete; final hardened profiles complete.
3. Establish whether a test-only optimization can retain all existing behavior.
   No worthwhile independent change established. Measured cost is helper-owned;
   implementation stops at the coordination proposal in the review packet.
4. Targeted validation and scoped diff inspection complete. Diagnostic commit/
   push/draft PR and exact-head CI remain. No manufactured implementation.

## Discoveries and decisions

- Both large candidate suites already prepare baseline once per class.
- Generic rule files are hash-bound in committed proofs. Equivalent output alone
  cannot authorize changing their identity in this lane.
- Candidate-owned reuse adapter repeatedly calls common preparation with full
  captures; the initial lead is now confirmed by profiling below.
- Use one benchmark process at a time to avoid material research interference.
- Immigration prepare measured10.549s first/10.120s warm. cProfile15.546s:
  16 reused actions,17 common prepares/source validations,46 core validations,
  100 schema traversals. Eleven qualified actions repeatedly validate the same
  115-action/19.3MB Health provider. File read/JSON load is about1s cumulative;
  validator traversal and hashing dominate. Cumulative rows overlap.
- Historical CI verified from raw job logs: checkpoint224361tests/630.49s;
  checkpoint225364tests/536.37s, with209 Immigration tests included. No change
  to exact-head/synthetic checkout contracts.
- Current generated Immigration proof binds the candidate-owned adapter;
  Immigration and Health proofs bind generic prepare/shared_corpus. Existing
  proof identity cannot silently change when equivalent helper code changes.

## Access and deviations

Initial sandbox CLI remote reads failed: Git SSH signal pipe Windows error5;
gh configured proxy 127.0.0.1:9 refused connection. Connector reads succeeded.
Worktree creation succeeded with reviewed escalation. CPU WMI read was denied;
use Python-reported processor/platform and logical CPU count, no WMI workaround.
Unrelated existing root/wf pytest temporary directories denied enumeration;
left untouched. No automatic approval rejection occurred.

## Validation and resume

Direct prepare repeats and profile have identical product digests. Harness
compiles; wrong-head rejection exits2 without writing results. Provider-path
discovery controls pass. Full baseline lane uses all four unchanged modules:
363pass/1failure in380.25s, no skipped tests. The one failure is unchanged
candidate test line22 `read_text()` using Windows CP1252 on UTF-8 bytes; initial
ad-hoc analysis hit the same default-codec failure and was corrected to explicit
UTF-8. Three pytest cache-write warnings are sandbox access denials. No code,
assertion or data change; full rerun uses process-local `python -X utf8` and
reviewed execution per the Windows test runbook. This aligns default file reads
with the Linux CI encoding without suppressing validation.
Full UTF-8 rerun:364pass/0fail/0skip/0warnings in374.24s. Test identity digests
match all364 cases across both runs. Immigration class341.706s, Health31.831s,
corpus0.241s, research0.000s (JUnit rounding).
Final hardened profiles: Immigration10.990s first/11.730s warm,21.120s profiled;
Health0.807s first/0.796s warm,1.210s profiled. Every call executes every check.
All five product digests match across initial/final Immigration runs; loaded
inputs,13 provider files, rule/input bytes, head and tracked state unchanged.
Hardened destination/overwrite rejection controls pass. Raw receipts remain in
`.w/cvp/.local/`; normalized values/hashes/counts are in the review packet.
Next: commit/push diagnostic draft PR, exact-head CI. Record
delivered head/PR/CI in the PR body and `.local/delivery.json`; do not amend the
head merely to add CI-status prose. Independent review remains pending.

## Production writes and rollback

None. Local profiling creates only ignored diagnostic artifacts. Feature changes
are reversible through Git; do not clean other worktrees.

## Final reconciliation and blockers

The measured proposal is delivered in the review packet. Runtime implementation
is blocked by the refined ownership/proof boundary;
helper changes need a separately authorized owner-coordinated checkpoint. No
optimized timing or speedup claimed. A measured proposal is the authorized
fallback outcome. CI savings cannot establish the under10-minute research goal.
