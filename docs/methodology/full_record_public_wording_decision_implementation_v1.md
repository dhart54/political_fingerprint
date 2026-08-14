# Full-Record Public-Wording Decision Implementation V1

This contract records detached human decisions over a complete governed
public-wording candidate package and deterministically implements those exact
decisions as canonical reviewed wording for internal use only.

Each decision binds the original candidate object and its subject digest.
Accepted-as-written records remain byte-for-byte equivalent as structured
objects. A bounded revision contains sealed field-path replacements, the hash
of each original value, and the hash of the exact revised result. The original
candidate remains embedded unchanged beside the implemented wording.

Bounded revision authority is limited to copy fields: title, primary sentence,
secondary clarification, evidence label, compression notes, and the public
copy or explanatory reason on an existing limitation treatment. It cannot
change identities, surfaces, semantic sources, evidence lineage, direction,
conclusion relevance, synthesis roles, blocked-action boundaries, or any
downstream authority.

Canonical reviewed wording is not publication authority. Publication,
production selection, persistence, database writes, production writes, runtime
changes, and deployment require separate authorization.
