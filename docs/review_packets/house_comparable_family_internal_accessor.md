# House Comparable Family Internal Accessor

Branch: `codex/house-family-internal-accessor`  
Base: `main` at `c97286f07bd2dbf4462695600f15b6d1526aa6c6`  
Accessor: `backend/app/analysis/house_comparable_families.py`  
Artifact: `docs/derived/house_comparable_policy_question_families_v1.json`

## Why This Exists

PR #45 created a versioned derived artifact for reviewed House comparable policy-question families. This milestone adds a small internal backend accessor so future backend or product work can consume that artifact through validated code instead of reaching into raw JSON.

The accessor keeps the artifact outside the production schema and preserves the current product framing: `Record Across Congresses`.

## What The Accessor Exposes

The module exposes:

- stable artifact loading from the repository-relative v1 path;
- strict artifact validation;
- typed `ComparableFamily` and `ComparableFamilyArtifact` structures;
- all families;
- lookup by `family_id`;
- filtering by issue domain;
- filtering by comparability status;
- future-limited eligible families;
- directly comparable eligible families;
- conditionally comparable eligible families;
- related-but-not-comparable families;
- ungrouped rows as explicitly ineligible;
- roll-call IDs separated by Congress;
- governing question, inclusion criteria, exclusion criteria, source-grounded rationale, caveats, limitations, vote types, and representative examples.

## What It Does Not Expose

The accessor does not expose:

- public API routes;
- frontend components;
- product copy;
- production database writes;
- production schema objects;
- continuity/change conclusions;
- behavioral movement claims;
- ideological movement claims;
- causal claims;
- changed-position labels;
- broad-domain-only family assignment.

## Trust Boundary Preservation

Validation requires:

- artifact version `house-comparable-policy-question-families-v1`;
- PR #45 reconciliation totals;
- required top-level metadata;
- explicit non-authorization flags;
- valid comparability statuses;
- all directly and conditionally comparable families to be future-limited eligible and represented in both Congresses;
- all related families and ungrouped rows to remain ineligible;
- roll-call IDs separated by 118th and 119th Congresses.

The accessor treats `directly_comparable` and `conditionally_comparable` as internal eligibility statuses for future limited `Record Across Congresses` work only. It does not convert them into public claims.

## Optional Join Helper

The optional legislator join helper was deferred.

Reason: a useful helper would need to join artifact roll-call IDs to `votes_cast`, `vote_interpretations`, and possibly current profile semantics. That is still feasible, but it should be done as a separate bounded backend milestone so it can validate database access patterns, member identity, not-voting treatment, and support/opposition counting without broadening this accessor into a service layer.

## Tests

Targeted tests:

```text
python -m pytest backend\tests\test_house_comparable_families_accessor.py
```

Result: `13 passed`.

The tests cover successful load, missing artifact failure, version mismatch failure, required metadata, non-authorization flags, comparability status validation, family lookup, domain/status filtering, eligible filtering, related/ungrouped exclusion, roll-call IDs by Congress, caveat preservation, and absence of generated movement/changing-position fields.

No full backend suite was required because this milestone adds a focused internal module and tests without changing shared runtime behavior. No frontend validation was required because no frontend runtime changed.

## Permanent Code Added

- `backend/app/analysis/__init__.py`: creates the internal analysis helper package.
- `backend/app/analysis/house_comparable_families.py`: reusable internal loader and validator for the versioned House comparable-family artifact.

These files remain useful after the milestone because future backend work can import a validated typed accessor instead of coupling directly to artifact JSON shape.

## Recommended Next Milestone

Build a bounded read-only backend helper that joins a legislator to eligible artifact roll-call IDs and reports family-level cast Yes/No and not-voting counts by Congress, while preserving the same non-authorization boundaries.

Frontend work should remain out of scope until that backend join helper is validated.
