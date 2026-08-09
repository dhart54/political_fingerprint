# M11E National Security Policy-Episode Candidates V1

Status: human review complete; accepted as the exact non-authorizing candidate
input to M11F at PR #137 head
`1256bb84603305c6f2da037a80d5c167e805a503`.

## Intent and larger-goal alignment

Build a deterministic, detached episode-candidate package from the 81
human-accepted M11D action interpretations. This is the organizational bridge to
possible later Semantic IR work, but it grants no episode or downstream
authority.

## Baseline

- Accepted M11D head: `8452ca3dfb5ba740343983c2288303fe87064b19`.
- Exact post-M11D merge main:
  `104e0bf67854342b0cde5c7247cfa302a338c527`.
- Accepted M11D implementation: 81 internal canonical action interpretations.
- H.R. 8800 final passage remains source-blocked and uninterpreted.
- Justice remains the accepted publication-active production reference.

## Scope and decision envelope

In scope: episode propositions, primary membership candidates, direction
candidates derived from accepted effects, contrasts, limitations, source and
digest bindings, an empty human-decision template, a readable review dossier,
independent validation, adversarial tests, and a draft PR.

Out of scope: episode acceptance, Semantic IR, propositions beyond episode
organization, synthesis, public wording, publication, persistence, database or
production writes, deployment, and merge of the M11E PR.

## Implementation sequence

1. Merge accepted PR #136 only at its exact head and record post-merge main.
2. Generalize the Justice episode-candidate contract around M11D records.
3. Propose conservative primary membership with explicit cross-measure review.
4. Generate candidate, decision, dossier, schema, and parity artifacts.
5. Independently validate upstream identities, exact accounting, grouping
   boundaries, determinism, and all false downstream authorities.
6. Open a draft PR and stop for human episode decisions.

## Definition of done and progress

- [x] Exact M11D head merged and post-merge main captured.
- [x] All 81 accepted records accounted for exactly once.
- [x] H.R. 8800 excluded from construction.
- [x] Same-parent, package, topic-only, direction, and cross-measure boundaries
      are explicit and adversarially tested.
- [x] Concise human review surface and detailed governed JSON generated.
- [x] Full regression validation and CI pass at the final draft-PR head.
- [x] Human decisions are recorded in M11F: 70 candidates accepted as written
      and four cross-measure candidates rejected/reassigned to 11 singletons.

## Current candidate accounting

- 74 proposed episodes.
- 70 single-action episodes.
- Four multi-action, cross-measure episodes: Iran War Powers (five actions),
  Lebanon War Powers (two), Venezuela War Powers (two), and FISA title VII
  extension attempts (two).
- Zero ambiguous or unassigned accepted actions.
- One blocked action outside construction: `house:119:2:278`.

## Decisions and rationale

Broad packages and amendments remain separate. Ukraine, Jordan, military
sex/gender, and defense-energy actions with shared topics remain contrasts when
their mechanisms or scopes differ. The four cross-measure candidates are
presented at medium confidence with the explicit competing option of retaining
each measure as a separate repeated episode.

## Production, rollback, and blockers

No production, persistence, database, publication, or deployment write is
authorized or performed. The branch is documentation/data/tooling-only, so
rollback is ordinary Git reversion before any later authority milestone. No
current blocker is known; human episode review is the required stopping gate.

## Validation results

- Independent M11A–M11E identity, digest, action-set, episode-membership,
  blocked-action, schema, parity, and deterministic-regeneration validation
  passes at 82 = 81 interpreted + one blocked and 74 = 70 single + four
  cross-measure candidates.
- Eleven new adversarial tests pass, including every requested grouping,
  direction, blocked-action, and authority-leakage case.
- Accepted Justice episode decision implementation, action decision
  implementation, M5R1 Semantic IR, and full-record validators pass without a
  Justice-state change. The older Justice episode-candidate unittest retains a
  Windows CRLF raw-byte sensitivity in four assertions; canonicalized hashes
  match the frozen expected acceptance identities, and no Justice file changed.
- Documentation and terminology governance, Semantic IR schema validation,
  Ruff, formatting, compilation, JSON parsing, ancestry, and diff checks pass.
