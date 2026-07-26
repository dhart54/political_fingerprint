# Editorial Semantic IR V1

Status: design candidate pending external semantic review.

## Canonical boundary

Semantic IR V1 is the review contract between authoritative evidence and later
presentation. Its canonical result is the proposition graph plus conclusion
plan, not a paragraph. Example prose is optional, non-authoritative review aid.

The stage order is:

1. authoritative action;
2. exact-action eligibility;
3. action meaning;
4. episode;
5. policy family;
6. structural metadata and policy traits;
7. member action;
8. evidence proposition;
9. proposition relationship;
10. conclusion plan;
11. section ownership;
12. render plan.

Every later stage consumes stable identities and decisions from earlier stages.
It may select, relate, omit, or render them, but may not reinterpret them.

## Three layers

Shared legislative semantics contain canonical actions, exact-action domain
eligibility, claim/source references, action meaning, legislative stage,
structural metadata, episodes, policy families, policy traits, trait
relationships, and shared review dependencies. These fields are member-neutral.
Action-meaning and policy-trait IDs may resolve to the referenced reviewed
dossier contracts rather than being copied into every case. When a case needs
to introduce or override one, the schema provides typed `policy_traits`,
`trait_relationships`, and `shared_review_dependencies` records; shared
dependencies carry their review route and cannot be resolved per member.

Member semantics contain exact action status, service status, evidence status,
coverage, propositions grounded in the shared layer, and a review route. Member
and party fields provide identity/context only and cannot change the shared
semantic result.

Composition semantics contain primary and limiting proposition IDs, one primary
section per proposition, intentionally omitted sections, exact coverage and
method notes, prohibited claims, and a render plan that cannot add analysis.

## Identity rules

- Action IDs use `house:{congress}:{session}:{roll}` for this corpus.
- Episode and policy-family IDs reuse existing corpus IDs where available.
- Case IDs are stable review identities and do not encode member names.
- Proposition IDs are case-scoped semantic identities. Their meaning is the
  proposition type, evidence identities, direction, traits/mechanisms, primary
  section, and relationships—not exact prose.
- Reordering actions, changing titles, or changing member/party identity cannot
  change semantic identities or proposition selection.

## Universal invariants

1. Member vote direction cannot alter action eligibility, episode identity, or
   policy-family identity.
2. Member and party identity cannot alter semantics for identical evidence.
3. Parent-measure context cannot establish exact-action eligibility.
4. Structural metadata is distinct from policy traits.
5. Multiple stages of one legislative event may form one episode.
6. Separate proposals remain separate episodes within one policy family.
7. A trajectory requires multiple actions within one episode.
8. A repeated pattern requires multiple independent episodes.
9. Present and Not Voting are neither support nor opposition.
10. Known coverage cannot use generic unknown-state language.
11. Every proposition has exactly one primary analytical section.
12. Tied material patterns cannot be silently omitted.
13. Rendering cannot add analytical meaning.
14. Shared novelty is reviewed once at the shared layer.
15. Approval, production eligibility, benchmark status, and publication remain
    separate gates.

## Evidence and review states

`official_record_resolved` means the authoritative member action is known. It
does not mean the dossier, proposition, or presentation is human approved.
`missing`, `source_unresolved`, and `conflicting` stay distinct. Present and Not
Voting are resolved non-directional statuses.

All development results in this milestone use
`candidate_pending_external_semantic_review`. That label conveys neither gold
status nor approval. Held-out files contain inputs and questions only; expected
graphs and conclusions must remain outside this implementation context.

## Validation tiers

The semantic loop is implemented here: schema-shape checks, selected candidate
and held-out integrity, stable IDs, evidence references, hierarchy, coverage,
proposition ownership, and targeted invariants.

The domain loop is proposed only: all member/vector inputs for one domain,
domain fixtures, and persistence-manifest generation.

The release loop is proposed only: all domains, frontend/browser validation,
disposable PostgreSQL, broad regressions, documentation, and rollback receipts.

Run the implemented loop from the repository root:

```powershell
python scripts/validate_editorial_semantic_ir.py
python -m unittest backend.tests.test_editorial_semantic_ir
```
