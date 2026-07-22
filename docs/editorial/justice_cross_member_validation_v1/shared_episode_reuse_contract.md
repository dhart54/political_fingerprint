# Shared-Episode Reuse Contract

The shared set `justice-public-safety-pr95-five-episodes@1.1.0` explicitly declares seven substantive rolls, six procedural controls, five independent episode IDs, and the complete episode-to-roll mapping. Rolls 32, 33, and 166 form one fentanyl trajectory and count once; rolls 130, 131, 275, and 299 each form one episode. The referenced PR #95 dossiers, sources, factual claims, and stage interpretations remain unchanged.

`editorial_member_overlay_v2` accepts recorded actions but derives all coverage from that contract. A missing roll cannot reduce the 7-roll or 5-episode denominator. Missing, Present, and Not Voting actions make the affected episode partial or missing and emit no support/opposition themes. Unknown or duplicate rolls, duplicate or unknown episode IDs, mismatched episode-to-roll assignments, and incorrect counting flags fail closed.

Justice-specific action meanings are declarative in `episode_action_interpretations.json`. Single-roll episodes cover Yea, Nay, Present, Not Voting, and missing. All eight complete Yes/No fentanyl signatures are interpreted as one trajectory; incomplete signatures remain non-counting.

The generic evaluator receives complete episode trajectories and their atomic themes, plus shared mechanism families and the Justice candidate catalog. It selects by required themes, competing themes, independent-episode coverage, and mechanism diversity. It does not receive a seven-roll lookup key, a member-specific template, or party metadata. Member identity is inserted only after candidate selection.

Overlays reject duplicated dossier fields. Serialized results retain stable shared references rather than copying research. Every artifact remains `human_approval_pending`, `not_promoted`, and `production_eligible: false`.
