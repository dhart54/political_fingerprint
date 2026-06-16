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

Merge autonomy applies only when the milestone includes it.

Before merging:

- required checks are green or skips are understood
- merge state is clean
- PR diff still contains only intended files
- no unexpected API-breaking, security, or deployment issue appears

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
