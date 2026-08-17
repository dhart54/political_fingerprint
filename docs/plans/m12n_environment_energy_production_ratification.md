# Milestone Plan: M12N Environment & Energy Runtime Correction And Ratification

## Intent

- Immediate task: correct the publication-authority runtime contract so stable human ratification is separate from fresh execution proof, merge and deploy that correction while Environment remains inactive, then publish a newly evidenced unaccepted/unsealed activation-ratification candidate.
- Larger-goal alignment: preserve the separation between reviewed publication preparation, independent activation ratification, and any later mechanical production activation.

## Outcome

- User-visible or operational result: PR158 becomes the corrected runtime-only change; after its guarded merge and deployment, a follow-on draft PR contains fresh production evidence and a non-authorizing prospective stable authority subject. Environment & Energy remains inactive throughout.

## Scope And Boundaries

- In scope: generic stable-runtime/fresh-execution-proof authority correction, adversarial tests, corrected PR158 merge/deployment, exact runtime health proof, fresh read-only production preflight, deterministic evidence regeneration, disposable PostgreSQL proof, a new ratification candidate, validation, and a follow-on draft PR.
- Out of scope: production dry-run/apply/rollback, registry mutation, persistence, accepted or sealed authority, Environment activation, configuration/secrets changes, and all protected ZIPs.
- Files/systems likely touched: generic publication authority validation, Environment production executor, focused tests, this plan, and—only after corrected deployment—the governed Environment ratification evidence package.

## Decision Envelope

- Codex may decide and execute: truthful production-specific binding regeneration and mechanical validation corrections that do not alter runtime or civic semantics.
- Explicit approval required for: positive authority sealing, production database writes, activation, rollback, deployment configuration/secrets, and follow-on ratification PR merge. The current request authorizes the bounded runtime correction, PR158 merge, and corrected runtime deployment.

## Definition Of Done

- [ ] Stable authority binds only the exact reviewed manifest and ratified reviewed/deployed/health commits; ratification-time proof remains historical evidence.
- [ ] Production execution requires a separately fresh (at most 1,800 seconds) digest-valid proof matching the ratified runtime identity, without proof-digest equality.
- [ ] Historical M11N artifacts remain byte-identical and valid.
- [ ] Corrected PR158 passes exact-head hosted checks, merges with expected-head protection, and deploys while Environment remains inactive.
- [ ] Fresh read-only production state matches the accepted 5/149/161/2 baseline and issue boundaries after corrected deployment.
- [ ] Regenerated 1/3/2/1 additive write set and new immutable accepted=false/sealed=false ratification candidate validate and grant no authority.
- [ ] Follow-on exact-head hosted checks are obtained and final reconciliation is complete.

## Baseline

- Branch/base commit: `codex/m12n-environment-energy-production-ratification` from `79d49f3e613e7914e4dc81d2f3b6a348cf80fafc`.
- Production/deployment state: `/health` reports exact post-PR157 main; production data still requires fresh read-only verification.
- Tracked working tree: clean isolated linked worktree.
- Known unrelated artifacts: original checkout contains historical Windows EOL noise and user-owned ZIPs; neither is touched.

## Implementation Sequence

1. Remove the rejected pre-correction evidence/candidate from PR158 and implement the generic authority/runtime-proof split with adversarial tests.
2. Run release-level, M11N compatibility, disposable PostgreSQL, diff, and frozen-file validation; push corrected PR158 and obtain exact-head checks.
3. Guarded-merge PR158, verify the corrected backend deployment and exact `/health` commit while Environment remains inactive.
4. From exact corrected main, capture a new runtime proof and read-only production preflight; regenerate bindings/write set and a new non-authorizing candidate using `candidate_prepared_at_utc` rather than a fabricated decision time.
5. Validate, push a follow-on draft PR, obtain exact-head checks, and stop before activation.

## Progress Checklist

- [x] Discovery
- [x] Runtime correction implementation
- [ ] Runtime correction validation/merge/deployment
- [ ] Fresh evidence and candidate regeneration
- [ ] Follow-on validation/PR readiness

## Discoveries

- PR157 merged as `79d49f3e613e7914e4dc81d2f3b6a348cf80fafc`; production `/health` reports that exact commit.
- The post-merge Render workflow deployed successfully but its smoke assertion failed on a historical Justice `artifact_id` expectation; the fresh milestone validator will establish the governed current identities.
- Fresh production state remained exactly `5 / 149 / 161 / 2` with fingerprint `b22908fb081fa3dcefbb2e7326b0619b9f95fecc1bbebc76e783628dceddb0eb`; Environment rows remain absent.
- Fresh runtime proof subject is `5b3d0df5464ba386d7cefe8bac3738650552e6a050955bcf5c9e5f18d582a3fc`; fresh preflight subject is `59f282ebd0888360669a4b1568a25b201ed552598cda661b40976a05d6932ab8`.
- Final preparation authority subject is `891256c341e8b4c97949559fb6a6016f926451a8aec7af15084b2d6212c31077`; final write-set subject is `b4a3a446ffb125459db63be746535b13663baa28c6c029eae32d7dfa99db9f98`.
- The ratification candidate is immutable, unaccepted, and unsealed; prospective subject digest is `725571c3319511f1f4debab25b63b842fd4fd7458056d828a2aaa06e4d88b49f`.
- Independent review rejected that prospective subject because stable authority content-bound the volatile health-proof digest while execution independently required proof freshness within 1,800 seconds. The digest is not ratified and will not be reused.
- The prospective contract now uses a four-field stable runtime identity (`reviewed_runtime_manifest_sha256`, `reviewed_commit`, `deployed_commit`, `health_commit`), a separate historical `ratification_runtime_evidence_binding`, and a newly captured digest-valid execution proof with a maximum 1,800-second age.
- The rejected production evidence/candidate was removed from PR158's effective diff; the governed pre-correction preparation remains reproducible through an explicit frozen runtime-manifest replay path.

## Decisions And Rationale

- Use a clean linked worktree to avoid altering the original checkout's historical EOL noise or user-owned artifacts.
- Use a two-stage Git lifecycle because corrected runtime must be merged and observed in production before truthful ratification evidence can be generated: PR158 carries runtime correction only, and a follow-on draft PR carries post-deployment evidence/candidate.
- Preserve the M11N accepted authority and activation artifacts exactly; its legacy validator remains an explicit historical compatibility path, while the new stable/fresh split applies prospectively.

## Deviations Or Corrections

- Initial linked-worktree paths exceeded Windows path limits; repository-local `core.longpaths` and a short `.w/r` path resolved checkout without changing content.
- Two historical validators still exceeded the linked-worktree path ceiling for one frozen source; both passed unchanged from the shorter original checkout. No historical artifact was rewritten.
- The first hosted PostgreSQL attempt correctly rejected direct use of the production-bound fingerprint because disposable surrogate IDs differ. The test now proves semantic graph parity with the finalized governed write set, then applies a disposable-state binding without weakening production drift protection.

## Validation Results

- Pre-correction evidence cycle: all 15 M12 validators, focused M12N/M11N, API, candidate, deterministic, lint/format, compile, diff, disposable PostgreSQL, and six hosted checks passed at the rejected candidate head.
- Corrected runtime focused M12N/M11N suite: 44 passed; adversarial coverage proves stale/missing/mismatched execution proof rejection and permits a distinct fresh digest for the exact ratified runtime.
- Corrected runtime editorial API suite with the read-only repository profile: 48 passed.
- Corrected runtime persistence suite: 17 passed, 9 environment-dependent PostgreSQL tests skipped locally.
- Editorial pipeline release validation: 7 checks passed.
- Deterministic historical M12N preparation replay, Ruff lint/format, compileall, and `git diff --check`: passed.
- Frozen M11N governed artifacts and accepted M12L/M12M artifacts: no Git diff.
- Corrected exact-head hosted checks: pending.

## Production Writes

- Performed: no.
- Scope: read-only production health and database preflight only.
- Expected effects: none.
- Actual effects: none; `/health` deployment and production preflight were read-only.

## Rollback Paths

- The prospective Environment-only rollback contract will be regenerated and proven solely in disposable PostgreSQL; no production rollback is authorized.

## Blockers

- None at discovery. Production database mutation remains intentionally unauthorized.

## Final Reconciliation

- Definition of done satisfied: not yet; execution is in progress.
- Required stopping point: a new post-deployment candidate is present only as accepted=false/sealed=false on a follow-on draft PR, with Environment still inactive.
