# Shared-Episode Reuse Contract

## Stable shared layer

The five researched episodes remain owned by `docs/editorial/valerie_foushee_justice_public_safety_gold_v1/policy_episode_map.json`, versioned in overlays as `justice-public-safety-pr95-five-episodes@1.0.0`:

- `halt-fentanyl-legislative-path`: rolls 32, 33, and 166, counted once;
- `retired-service-weapon-purchases`: roll 130;
- `officer-safety-data-reporting`: roll 131;
- `dc-police-pursuit-rules`: roll 275;
- `dc-policing-reform-repeal`: roll 299.

The PR #95 measure dossiers, source mappings, factual claims, stage interpretations, and Foushee artifacts are unchanged. A future factual correction to the shared episode map is joined at inference time and therefore applies to every overlay without copying the dossier.

## Member-varying layer

`editorial_member_overlay_v1` contains only:

- member ID, display identity, and descriptive party metadata;
- reviewed period and stable shared-set reference;
- per-roll recorded action, counting status, episode reference, source ID, and descriptive party alignment;
- per-episode action signature, coverage, member trajectory, candidate theme evidence, conclusion effect, contrary evidence, and limitations;
- coverage counts and pending publication metadata.

The validator rejects dossier-shaped fields such as bill titles, measure summaries, primary-purpose text, legislative history, source URLs, and pro/con argument text. Not Voting and Present are never converted to support or opposition. Procedural controls are `counting: false`.

## Inference boundary

The generic inference join consumes shared episode annotations, complete member trajectories, an editorially proposed candidate, supporting/weakening/neutral effects, and limitations. Party metadata is not passed to inference. Coverage below three complete independent episodes returns `insufficient_coverage` instead of a cross-episode candidate.

Serialized candidates retain stable episode references but omit the joined shared annotations, preventing seven copies of shared facts. All output remains `human_approval_pending`, `not_promoted`, and `production_eligible: false`.
