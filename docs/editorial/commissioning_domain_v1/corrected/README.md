# Commissioning Domain V1 — Corrected Corpus

This directory contains the distinct corrected `ENVIRONMENT_ENERGY`
commissioning corpus. It does not overwrite the original eight-action result.

The correction:

- rejects House roll 5 as
  `exact_action_not_materially_environment_energy`;
- retains seven eligible actions across six independent episodes;
- bounds roll 6 to the combined Divisions B-C retention action;
- bounds roll 7 to cross-domain final passage and keeps it in the same
  appropriations episode;
- keeps rolls 55 and 64 as independent episodes in the Critical Mineral
  Supply policy family;
- keeps rolls 76 and 78 as independent episodes in the Home Energy Policy
  family;
- assigns episodes from legislative identity and mechanism, never vote
  direction;
- evaluates 432 members, 35 observed vectors, and all 128 binary vectors;
- separates seven unique shared-review dependencies from member-specific
  routing;
- preserves exactly four possible member routes without adding a schema;
- produces the distinct pending batch
  `commissioning-domain-v1-environment-energy-corrected-six-episode`.

The corrected batch contains 69 artifacts and 60 relationships. Its manifest
SHA-256 is
`3e1ecd448f086fae52bd69a74303899940f0e417978a82df34970317052752fc`.
Its exported artifact and relationship semantic hashes are
`c2e2f63577f9b7b4224b09c073add4fdccf443dd121d986fda76eb6ec00919ad`
and
`7e4826fc8002799a7b1702363cd6fa1859d95cd5379f3b85cdc63111ae7f1238`.

All artifacts remain `human_approval_pending`, `not_promoted`, and
`production_eligible: false`. Production rollback and corrected application
are prepared but were not executed.
