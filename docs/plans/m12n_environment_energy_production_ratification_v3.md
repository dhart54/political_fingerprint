# Milestone Plan: M12N Environment & Energy Production Ratification V3

## Intent

- Immediate task: deploy the independently accepted active-publication repair, bind fresh read-only production evidence to that exact runtime and unchanged inactive database state, and create a detached V3 activation-ratification candidate.
- Larger-goal alignment: preserve the separation between accepted publication content, runtime deployment, ratification review, and any later production activation.

## Outcome

- Operational result: one draft V3 review PR contains fresh runtime/preflight evidence, regenerated runtime-dependent preparation objects, disposable active-HTTP proof, and an immutable unaccepted/unsealed candidate. Environment remains inactive.

## Scope And Boundaries

- In scope: guarded PR160 merge, exact repaired-runtime deployment verification, read-only production verification, fresh runtime/preflight capture, deterministic preparation regeneration, disposable PostgreSQL proof, V3 candidate/review packet, validation, and a draft PR.
- Out of scope: sealed positive authority, production dry-run/apply/rollback, Environment registry insertion, activation, deployment configuration or secrets, semantic/public wording changes, and protected ZIPs.
- Files/systems likely touched: this plan and governed M12N runtime/preflight/preparation/V3 candidate evidence only.

## Decision Envelope

- Codex may execute the accepted merge/deployment and read-only production verification, and may regenerate deterministic non-authorizing artifacts.
- New authority sealing, production writes, activation, rollback, V3 PR merge, configuration, and secrets remain unauthorized.

## Definition Of Done

- [x] PR160 exact accepted head merged and live `/health` equals post-merge main.
- [x] Production remains exactly 5/149/161/2 with accepted fingerprint and Environment absent/receipts-only.
- [x] Fresh proof and preflight bind repaired manifest and exact deployed main.
- [x] Regenerated 1/3/2/1 prospective graph preserves accepted M12M bytes and existing issue identities.
- [ ] Disposable FastAPI activation/idempotency/rollback proof passes on the exact PR head.
- [x] V3 candidate is immutable, accepted=false, sealed=false, and no usable authority exists.
- [ ] Exact-head hosted checks pass and final reconciliation is complete.

## Baseline

- Branch/base commit: `codex/m12n-environment-energy-production-ratification-v3` from `c480dfabc2fcbd65bf5b22037200af509adb7b5b`.
- Production/deployment state: `/health` reports exact repaired main; Environment database state requires fresh read-only verification.
- Repaired runtime manifest: `a831d472f27a1785ebdcc609c174fc2e19da7213245adde3d12720736158ba8a`.
- Tracked working tree: clean before this plan.
- Known unrelated artifacts: historical Windows temporary-directory/EOL limitations and protected user-owned ZIPs remain untouched.

## Implementation Sequence

1. Capture fresh live runtime proof for exact repaired main.
2. Run read-only production preflight and stop on any count, fingerprint, issue identity, or Environment-absence drift.
3. Regenerate only runtime/preflight-dependent preparation objects and construct a distinct V3 candidate/review packet.
4. Reprove the finalized prospective graph and HTTP behavior in disposable PostgreSQL.
5. Validate, commit, open one draft PR, obtain exact-head hosted checks, and stop.

## Progress Checklist

- [x] Accepted repair merge and deployment
- [x] Fresh production evidence
- [x] Deterministic regeneration and V3 candidate
- [ ] Disposable and regression validation
- [ ] Documentation and draft PR readiness

## Discoveries

- PR160 merged as `c480dfabc2fcbd65bf5b22037200af509adb7b5b`; production `/health` already reports that exact commit.
- The fresh read-only preflight reproduced `5/149/161/2`, fingerprint `b22908fb081fa3dcefbb2e7326b0619b9f95fecc1bbebc76e783628dceddb0eb`, Environment absence, and unchanged Justice/National Security identities.
- The existing V2 candidate and failed-attempt authority must validate intrinsically as immutable history after the current runtime-dependent preparation objects advance; they must not be rebuilt from V3 preparation inputs.
- Local release validation requires normal filesystem access for temporary fixtures on this Windows sandbox; the same release gate passed outside that restriction.

## Decisions And Rationale

- Preserve the failed `a22bee...` runtime and sealed V2 authority as immutable failed-attempt history; do not freeze the unaccepted intermediate `425b263...` runtime.
- Use a distinct V3 candidate rather than mutating V2.

## Deviations Or Corrections

- None.

## Validation Results

- Deterministic V3 builder/validator: passed.
- M12N preparation builder check: passed.
- Historical V2 candidate/authority/receipt validation: passed with governed bytes unchanged.
- Focused M12M/M12N/M11M/M11N/active-dispatch tests: 81 passed.
- Ruff and formatting checks: passed.
- Python compilation: passed; inaccessible sandbox-created temporary leftovers were skipped without tracked-file impact.
- Editorial release tier: passed, 7 checks, when run outside the Windows temporary-directory sandbox restriction.
- Exact-head hosted PostgreSQL/HTTP and broad repository checks: pending draft PR.

## Production Writes

- Performed: no.
- Scope: read-only production health and database preflight only.
- Expected effects: none.
- Actual effects: production remained exactly `5/149/161/2`; Environment remained absent and receipts-only; Justice and National Security remained unchanged.

## Rollback Paths

- No production write occurs in this milestone, so no rollback is invoked. The governed historical Environment rollback remains unchanged.

## Blockers

- None currently. Any production fingerprint, deployment identity, or existing publication identity drift is a hard stop.

## Final Reconciliation

- Definition of done satisfied: pending.
- Remaining limitations: V3 remains non-authorizing and requires independent ratification review.
- Recommended next step: independent review only; no activation.
