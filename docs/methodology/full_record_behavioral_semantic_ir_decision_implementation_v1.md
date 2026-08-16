# Full-Record Behavioral Semantic IR Decision Implementation V1

This contract records detached human acceptance of a complete Behavioral
Semantic IR candidate graph and deterministically implements only the accepted
semantic content.

The authority binds the exact candidate artifact, decision template, upstream
episode authority and implementation, reviewer authority, proposition decisions,
and complete episode-disposition ledger. A decision binds the full candidate
proposition content digest; it cannot authorize a paraphrased or regenerated
meaning.

The implementation preserves the accepted proposition object verbatim inside a
sealed implementation record. Canonical internal acceptance is an outer state;
candidate-era `authorizing`, `canonical`, and review-state fields remain unchanged
inside the preserved evidence object. Each evidence episode binds to its accepted
policy-episode implementation record, and each action is independently checked
through that episode against its accepted action-interpretation record.

The complete episode-disposition ledger is authoritative. It separately accounts
for primary evidence, contrast-only evidence, no-safe-proposition evidence, and
unused non-directional evidence, and it must reconcile exactly to every accepted
episode. Episodes retained only as contrasts, assigned no safe higher-level
proposition, or retained as unused non-directional evidence cannot be promoted by
a later layer without a new governed semantic review. Primary evidence episodes
have exactly one accepted owner.

New packages use milestone-neutral action-interpretation, policy-episode, and
candidate-parity bindings. The schemas and validators retain an explicit legacy
M11D/M11F/M11G vocabulary for byte-identical historical artifacts, but a governed
record must use exactly one vocabulary for each binding. Episode evidence maps
are content-validated against the accepted candidate and upstream implementation;
schemas do not hard-code historical episode IDs.

Behavioral Semantic IR acceptance does not authorize synthesis, public wording,
publication, persistence, database writes, production effects, or deployment.
Those remain separate human-governed gates.
