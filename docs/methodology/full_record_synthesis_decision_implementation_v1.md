# Full-Record Synthesis Decision Implementation V1

This contract records detached human decisions for a complete synthesis
candidate package and deterministically implements only those decisions as
canonical internal synthesis.

Every decision binds the complete original candidate object and subject digest.
An accepted-as-written implementation must preserve that object exactly. A
bounded revision is represented as sealed, explicit field-path replacements;
the implementation must equal the result of applying only those replacements.
The original candidate remains embedded unchanged beside the implementation.

A deterministic structural projection is invariant across every bounded
revision. It freezes the synthesis identity, type, direction, relevance,
candidate authority state, all input proposition and implementation bindings,
relationship roles, relationship structure, structural relationship-basis
flags, complete underlying episode/action evidence, and downstream authority
state. Human-readable summaries and other explanatory semantic fields may be
revised; structural or evidence changes require a new candidate/review cycle.

Behavioral Semantic IR `direction` is proposition-relative structural metadata.
It may support structural direction accounting, but it cannot substitute for
the accepted proposition's semantic content. In particular, `mixed` direction
metadata alone cannot establish mixed substantive policy orientation.

All Behavioral Semantic IR inputs, relationship roles, episode/action lineage,
complete proposition-role accounting, overlap accounting, and accepted episode
disposition accounting remain exact. The generic authority and implementation
use milestone-neutral accepted Behavioral Semantic IR bindings; validators also
accept the frozen M11J binding vocabulary for historical compatibility. A
separate unused non-directional disposition, when present, cannot be folded into
the no-safe-proposition count. Standalone propositions and contrast-only,
no-safe, or non-directional episodes cannot be promoted or injected as raw
synthesis evidence.

Synthesis acceptance is internal only. It does not authorize public wording,
publication, persistence, database or production writes, production effects,
or deployment.
