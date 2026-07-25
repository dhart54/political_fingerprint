# Commissioning Domain V1 — Corrected Corpus

This directory contains the distinct corrected `ENVIRONMENT_ENERGY`
commissioning corpus. It does not overwrite the original eight-action result.

The correction:

- rejects House roll 5 as
  `exact_action_not_materially_environment_energy`;
- retains seven eligible actions across four episodes;
- bounds roll 6 to the combined Divisions B-C retention action;
- bounds roll 7 to cross-domain final passage and keeps it in the same
  appropriations episode;
- evaluates 432 members, 35 observed vectors, and all 128 binary vectors;
- separates eight unique shared-review dependencies from member-specific
  routing;
- preserves exactly four possible member routes without adding a schema;
- produces the distinct pending batch
  `commissioning-domain-v1-environment-energy-corrected`.

The corrected batch contains 66 artifacts and 60 relationships. Its manifest
SHA-256 is
`dea1b8c7a0071462a5eb91f24d22287dc156fda9edcfa71a2abf6e570c2459c5`.
Its exported artifact and relationship semantic hashes are
`ac393b0fe4fd3d06186cfa4637d10f25357c4f3893c2d54cc8c42b7ec23af45e`
and
`d42f22e8bfd3c635b6153cd1235aaa2be1bf1e65c93b91ea52adb8522f322628`.

All artifacts remain `human_approval_pending`, `not_promoted`, and
`production_eligible: false`. Production rollback and corrected application
are prepared but were not executed.
