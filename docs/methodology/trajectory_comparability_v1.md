# Trajectory comparability V1

A trajectory is a longitudinal claim about substantively comparable governing
choices. Dates, titles, annual succession, issue membership, package labels and
opposite directions are insufficient. Comparability is a reviewed semantic input,
never a string-similarity, embedding or vote-direction inference.

Future behavioral candidate authoring supplies `comparison_binding` with a
comparison ID and content digest. The caller supplies `trusted_comparisons`
separately from authoring. The trusted comparison describes a common operative
choice, comparison scope, observed dimension, exact ordered accepted episodes,
their action lineage, and limitations. Candidate-local prose, acceptance flags
or a candidate-local comparison table cannot supply this authority.

The closed comparison record contains:

- `comparison_id`, `accepted`, `common_policy_choice`;
- `basis_kind`: `same_policy_mechanism`, `same_bounded_decision`, or
  `whole_package_equivalence`;
- `comparison_scope`: `bounded_choice` or `whole_package`;
- `change_dimension`: currently `member_direction`;
- `observations`: ordered episode ID, complete episode-content digest, exact
  primary action IDs, accepted policy proposition, and reviewed `choice_scope`
  (`bounded_choice` or `whole_package`);
- nonempty `limitations`.

Each observation records its reviewed choice scope against the complete accepted
episode digest; it does not add fields to historical episode schemas. The bound
episode must establish accepted exact action meanings, action-interpretation
record bindings and sources. Whole-package
observations require separately accepted whole-package equivalence. A comparison
about selected components cannot establish equivalence of the packages or project
component positions onto the member. A materially changed episode invalidates the
comparison binding. Unsupported dimensions need further semantic design, not
direction-derived claims of scope, mechanism, philosophy or motive changes.

The existing chronological `trajectory_change` record remains required: ordered
episodes, exact accepted dates and before/after directions, the changed dimension
and a bounded description. Comparability is an additional affirmative gate.

Deterministic validation checks bindings and contract conformance. It cannot prove
the truth of arbitrary prose. Acceptance of the common operative choice must come
from independent semantic review outside candidate authorship. A hash or an
`accepted` field submitted by the candidate author is not that review.

## Enforcement and history

`compile_behavioral_candidate_ir` enforces the rule for new full-record candidates.
The behavioral decision implementation validator applies the same gate to every
new or revised candidate; the exact frozen M11G candidate remains replayable.
`run_editorial_pipeline` also rejects structural trajectories from the original
Semantic IR compiler unless separately trusted comparison evidence binds the exact
input and member observations. Non-trajectory propositions are unaffected.

Frozen M11G replay is explicitly named and accepts only one pinned complete input
digest. Historical accepted-reference replay accepts only content-pinned frozen cases;
neither replay is forward trajectory eligibility, acceptance or publication.
Existing V1 package schema remains compatible with frozen artifacts and declares
the new binding shape. The forward compiler supplies the mandatory semantic gate.

The M11/M12/M13 path is accepted action meaning → accepted episode records →
behavioral candidate compiler → decision implementation with seals and exact
lineage → accepted public wording → site integration → public selector →
`ReviewedAnalysisSection`. M14 Education uses accepted analytical findings and
accepted wording before M14G integration; it has no trajectory. Justice's accepted
mixed HALT episode travels through the original IR/presentation path. The renderer
places overview-backed trajectories beneath “A change over time”; it cannot
establish comparability. M15B changes no accepted trajectory at runtime.

The bounded review set classifies the two active trajectory items. National
Security fails on the accepted semantics, not merely absent new fields: separate
whole-package choices, materially different contents, and no accepted common
operative comparison. Justice requires semantic review of its mixed-episode type;
M15B does not remediate or reinterpret that item.
