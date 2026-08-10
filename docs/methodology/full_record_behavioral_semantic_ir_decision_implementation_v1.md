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

The complete episode-disposition ledger is authoritative. Episodes retained only
as contrasts or assigned no safe higher-level proposition cannot be promoted by a
later layer without a new governed semantic review. Primary evidence episodes have
exactly one accepted owner.

Behavioral Semantic IR acceptance does not authorize synthesis, public wording,
publication, persistence, database writes, production effects, or deployment.
Those remain separate human-governed gates.
