"""Forward trajectory eligibility; comparison meaning is separately reviewed input.

A candidate cannot manufacture a comparison by supplying persuasive prose or a
self-declared approval. The caller supplies the trusted semantic comparison set,
separately from candidate authoring, just as it supplies accepted episode meaning.
"""
import hashlib
import json


class TrajectoryComparabilityError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def validate_comparison(candidate, episodes, trusted_comparisons):
    def require(ok, reason):
        if not ok:
            raise TrajectoryComparabilityError(reason)

    ref = candidate.get("comparison_binding")
    require(isinstance(ref, dict) and set(ref) == {"comparison_id", "content_sha256"},
            "trajectory requires an explicit accepted comparison binding")
    basis = trusted_comparisons.get(ref["comparison_id"])
    require(isinstance(basis, dict) and digest(basis) == ref["content_sha256"],
            "comparison is absent from separately trusted semantic evidence")
    require(set(basis) == {"comparison_id", "accepted", "basis_kind", "common_policy_choice",
            "comparison_scope", "change_dimension", "observations", "limitations"},
            "comparison contract fields differ")
    require(basis["accepted"] is True and basis["comparison_id"] == ref["comparison_id"],
            "comparison meaning has not been accepted")
    require(basis["basis_kind"] in {"same_policy_mechanism", "same_bounded_decision", "whole_package_equivalence"},
            "topic, annual family, chronology or direction cannot establish comparability")
    require(isinstance(basis["common_policy_choice"], str) and basis["common_policy_choice"].strip(),
            "common operative policy choice is missing")
    require(basis["comparison_scope"] in {"bounded_choice", "whole_package"}, "comparison scope is missing")
    # Other dimensions need accepted observation semantics, not inference from votes.
    require(basis["change_dimension"] == "member_direction", "unsupported behavioral change dimension")
    require(isinstance(basis["limitations"], list) and basis["limitations"] and
            all(isinstance(x, str) and x.strip() for x in basis["limitations"]),
            "comparison limitations are required")
    observations = basis["observations"]
    ids = candidate["evidence_episode_ids"]
    require(len(ids) >= 2 and len(ids) == len(set(ids)), "comparison requires distinct longitudinal observations")
    require(isinstance(observations, list) and [o.get("episode_id") for o in observations] == ids,
            "comparison observations must bind every ordered evidence episode")
    for observation in observations:
        episode = episodes[observation["episode_id"]]
        expected = {"episode_id": episode["episode_id"], "episode_content_sha256": digest(episode),
                    "action_ids": episode["primary_action_ids"], "policy_proposition": episode.get("policy_proposition"),
                    "choice_scope": observation.get("choice_scope")}
        require(observation == expected and bool(expected["policy_proposition"]),
                "comparison does not bind exact accepted episode meaning and action lineage")
        require(observation.get("choice_scope") in {"bounded_choice", "whole_package"},
                "accepted comparison observation must establish its choice scope")
        require(all(a.get("accepted_exact_action_meaning") and a.get("source_references")
                    and a.get("accepted_interpretation_record_subject_sha256") for a in episode["actions"]),
                "comparison lacks accepted action semantics and source lineage")
        if observation["choice_scope"] == "whole_package":
            require(basis["comparison_scope"] == "whole_package" and
                    basis["basis_kind"] == "whole_package_equivalence",
                    "whole-package votes cannot borrow component-level comparability")
    dates = [sorted({a['official_action_date'] for a in episodes[i]['actions']}) for i in ids]
    require(all(len(d) == 1 for d in dates) and all(a[0] < b[0] for a,b in zip(dates,dates[1:])),
            "comparison observations must be strictly chronological")
    change = candidate.get('trajectory_change', {})
    require(change.get('ordered_evidence_episode_ids') == ids and
            change.get('accepted_before_direction') == episodes[ids[0]]['member_direction'] and
            change.get('accepted_after_direction') == episodes[ids[-1]]['member_direction'] and
            change.get('accepted_before_direction') != change.get('accepted_after_direction') and
            isinstance(change.get('bounded_change_description'), str) and change['bounded_change_description'].strip(),
            "comparison change must bind exact accepted member observations")
    return basis
