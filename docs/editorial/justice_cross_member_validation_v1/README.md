# Justice Cross-Member Validation V1

This review-only bundle applies the five Justice & Public Safety policy episodes researched in PR #95 to Valerie P. Foushee and six additional House members selected from their recorded actions. It does not add measure research or duplicate the shared dossiers.

The architecture is:

1. shared measure dossiers in `../valerie_foushee_justice_public_safety_gold_v1/measures/`;
2. shared roll-stage interpretations in the PR #95 review packet;
3. shared episode definitions in `../valerie_foushee_justice_public_safety_gold_v1/policy_episode_map.json`;
4. member-varying actions and trajectories in `member_overlays.json`;
5. recomputed candidates in `inference_candidates.json`;
6. reviewer comparison in `comparison_matrix.json`.

Supporting artifacts:

- `cohort_selection.json`: all 437 members appearing in at least one reviewed substantive roll, their seven-roll vector, completeness, and selection status;
- `official_action_sources.json`: official House Clerk roll URLs and descriptive party-majority actions;
- `shared_episode_reuse_contract.md`: the boundary between shared research and member overlays.

Every new artifact is `human_approval_pending`, `not_promoted`, and production-ineligible. This is a small-cohort framework validation, not national validation and not a ranking of representatives.
