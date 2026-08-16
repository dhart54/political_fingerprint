# Full-Record Policy-Episode Decision Authority V1

This contract generalizes the accepted Justice separation between human episode
authority and deterministic implementation. A human authority record may accept,
revise, reject/reassign, or retain ambiguity for every candidate. The
implementation must bind each decision, every accepted action-interpretation
record, and complete primary-membership accounting.

New authority and implementation artifacts use the generic
`interpretation_implementation_binding` and
`policy_episode_candidate_binding` fields. The schemas explicitly retain the
historical `m11d_implementation_binding` and `m11e_candidate_binding` fields so
accepted M11F artifacts remain valid unchanged. Reviewer identity is
content-bound and nonempty; reviewer authority remains the closed
`full_record_policy_episode_review_authority_v1` class.

Episode acceptance establishes canonical internal organization only. It does
not create Editorial Semantic IR, synthesis, public wording, publication,
persistence, database-write, production, or deployment authority.

Directional and resolved non-directional episode states remain distinct.
`non_directional_present` and `non_directional_not_voting` are never converted
to support, opposition, or mixed direction.

Cross-measure primary episodes require both semantic proposition agreement and
explicit legislative-path or event continuity. Repeated separate measures are
separate primary episodes when continuity is not established. Rejected groups
may remain non-primary relationship evidence with zero authority effect.
