# Full-Record Behavioral Semantic IR Candidates V1

This contract governs detached, pre-acceptance behavioral proposition packages.
It is an opt-in candidate path within the canonical Editorial Semantic IR
compiler architecture; it does not replace accepted Semantic IR V1.

## Evidence and compilation rules

- Human-accepted policy episodes are the primary semantic evidence units.
- Exact actions may appear only as lineage projected from those episodes.
- Candidate roles are limited to `notable_choice`, `repeated_pattern`, and
  `trajectory`.
- A notable choice has exactly one episode. A repeated pattern has at least two
  distinct episodes and explicit episode-level semantic evidence. A trajectory
  additionally requires a structured substantive change record; chronology alone
  is insufficient. A direction-change record binds the ordered evidence episode
  IDs, accepted dates, accepted before/after episode directions, change type, and
  a nonempty bounded change description. Dates must be strictly chronological,
  directions must match the accepted episodes, and before/after directions must
  differ.
- Direction is derived from accepted episode direction. Mixed accepted episode
  directions compile to `mixed`. The canonical M11F
  `mixed_on_episode_choices` value and the retained historical
  `mixed_or_non_directional` value both compile to `mixed`.
- Each accepted episode receives exactly one accounting row. A proposition is
  the primary owner of an episode at most once unless a declared overlap names
  the prior owner.
- Unused episodes remain explicit. The compiler never promotes uncovered actions
  or episodes into notable choices automatically.
- Relationship hints may route review but have no inherited authority.

## Authority boundary

Candidate output is non-canonical and non-authorizing. It contains no synthesis
propositions or public wording and cannot authorize publication, persistence,
database writes, production effects, or deployment. A later governed human
decision and deterministic implementation milestone is required for acceptance.
