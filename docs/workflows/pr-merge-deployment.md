# PR, Merge, And Deployment Workflow

Use this runbook when the milestone includes PR creation, merge, or deployment verification.

## Before PR

Confirm:

- exact branch diff
- intended files only
- unrelated artifacts excluded
- tracked working tree state
- tests/build/validation results
- production data changes, if any, are documented and authorized
- review packet is present for substantial work

If local rendered validation is unavailable because of local browser, OS, or process-launch limitations, a draft or normal PR may be opened to obtain hosted preview validation. Opening a PR for hosted preview is not merge authorization. Record the local rendering limitation and complete hosted preview checks before treating rendered validation as satisfied.

## PR Summary

Summarize:

- what changed
- product or operational value
- guardrails
- validation results
- known limitations
- next recommendation

Include exact production-write results when applicable.

## Checks And Merge

Merge autonomy applies only when the milestone includes it. Treat PR creation for preview/review separately from merge authorization; a PR may exist while final merge readiness remains pending.

Before merging:

- required checks are green or skips are understood
- merge state is clean
- PR diff still contains only intended files
- no unexpected API-breaking, security, or deployment issue appears

### Editorial Integration And Publication Gates

Keep repository integration separate from editorial promotion and public publication:

- **Merge/integration eligibility:** Pending editorial artifacts, review tooling, schemas, tests, and staged rendering may merge when validation passes, the artifacts remain explicitly non-production, and pending content cannot be mistaken for approved public content.
- **Human editorial approval:** Merging does not assign `human_approved` or establish that formal per-field factual review, editorial scoring, or reader-comprehension testing is complete.
- **Gold-benchmark promotion:** Assigning `gold_benchmark` is a separate human-governed decision and must not follow automatically from merge, checks, or preview validation.
- **Public-production eligibility:** Enabling candidate interpretations in the approved public experience requires separate authorization after the applicable editorial and comprehension gates. A merge must not change production readiness, persistence, or public approval state unless the milestone explicitly authorizes those changes.

`human_approval_pending` is therefore not a categorical merge prohibition. It is a publication and promotion boundary: pending artifacts may merge only when they remain safely isolated, clearly labeled, and non-production.

After merging:

1. Check out `main`.
2. Pull with `git pull --ff-only origin main`.
3. Confirm the merge commit is present.
4. Confirm local `main` matches `origin/main`.
5. Confirm tracked working tree cleanliness.
6. Delete or prune the merged feature branch if safe.
7. Preserve unrelated untracked artifacts.

## Deployment Verification

Distinguish:

- code problem
- deployment lag
- wrong service
- wrong environment/configuration
- stale backend
- production-data issue

For frontend/backend deployments:

- confirm deployed commit
- confirm configured API base
- confirm health endpoint
- confirm key public API fields
- confirm user-visible behavior where relevant

Bounded redeploy of already-reviewed merged code is allowed only when the milestone authorizes deployment recovery and the target service/repository/branch is unambiguous.

Stop for ambiguity involving:

- secrets
- service identity
- repository connection
- branch
- environment variables
- DNS or custom domains

Do not change configuration or secrets without explicit user approval.
