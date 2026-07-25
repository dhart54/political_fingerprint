"""Issue-neutral proposition construction and bounded public conclusion rendering."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy


ARCHETYPES = {
    "substantive_repeated_pattern",
    "selective_or_conditional_pattern",
    "policy_mechanism_divide",
    "uniform_direction_without_common_policy_throughline",
    "bounded_episode_trajectories",
    "limited_or_contested_evidence",
}


def build_conclusion_model(
    *,
    member_name: str,
    roll_actions: list[dict],
    complete_trajectories: list[dict],
    candidate: dict,
    selected_theme_ids: list[str],
    trait_contract: dict,
) -> dict:
    """Build semantic propositions before prose without consulting identity or party."""
    archetype = candidate.get("conclusion_archetype", "limited_or_contested_evidence")
    if archetype not in ARCHETYPES:
        raise ValueError(f"unsupported conclusion archetype: {archetype}")

    direction = action_direction(roll_actions)
    clusters = _policy_clusters(
        roll_actions=roll_actions,
        complete_trajectories=complete_trajectories,
        trait_contract=trait_contract,
        requested_cluster_ids=candidate.get("proposition_spec", {}).get("policy_cluster_ids", []),
        cluster_actions=candidate.get("proposition_spec", {}).get("cluster_actions", {}),
    )
    spec = candidate.get("proposition_spec", {})
    evidence_episode_ids = sorted({
        episode_id
        for cluster in clusters
        for episode_id in cluster["evidence_episode_ids"]
    })
    all_episode_ids = sorted(item["episode_id"] for item in complete_trajectories)
    model = {
        "schema_version": "editorial_conclusion_propositions_v1",
        "archetype": archetype,
        "action_direction": direction,
        "thesis_proposition": {
            "role": "thesis",
            "claim_type": archetype,
            "policy_dimension_present": bool(clusters),
            "theme_ids": sorted(selected_theme_ids),
        },
        "supporting_policy_clusters": clusters,
        "contrast_proposition": _contrast(clusters, trait_contract),
        "trajectory_proposition": deepcopy(spec.get("trajectory_proposition")),
        "exception_proposition": deepcopy(spec.get("exception_proposition")),
        "boundary_proposition": deepcopy(spec.get("boundary_proposition")),
        "evidence_episode_ids": evidence_episode_ids or all_episode_ids,
        "omitted_episode_ids": sorted(set(all_episode_ids) - set(evidence_episode_ids)),
        "reader_label_concept": spec.get("reader_label_concept", _default_label(archetype, direction)),
        "review_route": "standard_generation_pass",
    }
    if trait_contract.get("final_composition_contract") == "v1":
        model["final_composition_contract"] = "v1"
        limiting_proposition = _limiting_proposition(
            clusters=clusters,
            complete_trajectories=complete_trajectories,
            omitted_episode_ids=model["omitted_episode_ids"],
            trait_contract=trait_contract,
        )
        if archetype == "substantive_repeated_pattern" and limiting_proposition:
            model["boundary_proposition"] = limiting_proposition
    if archetype in {"bounded_episode_trajectories", "limited_or_contested_evidence"} or not clusters:
        model["review_route"] = "human_exception_required"
    elif archetype == "uniform_direction_without_common_policy_throughline" and not model["contrast_proposition"]:
        model["review_route"] = "human_exception_required"
    elif spec.get("deterministic_audit"):
        model["review_route"] = "sampled_audit_candidate"
    model["public_conclusion"] = render_public_conclusion(member_name=member_name, model=model)
    model["compression_report"] = compression_report(model, all_episode_ids)
    return model


def action_direction(roll_actions: list[dict]) -> dict:
    actions = [
        item["action"] for item in roll_actions
        if item.get("counting") and item.get("action") in {"Yea", "Nay"}
    ]
    if not actions:
        return {"classification": "incomplete", "direction": None, "count": 0, "total": 0}
    counts = Counter(actions)
    direction, count = counts.most_common(1)[0]
    share = count / len(actions)
    classification = (
        f"uniform_{direction.lower()}" if count == len(actions)
        else f"mostly_{direction.lower()}" if share >= .70
        else "divided"
    )
    return {
        "classification": classification,
        "direction": direction,
        "count": count,
        "total": len(actions),
        "uniform": count == len(actions),
    }


def render_public_conclusion(*, member_name: str, model: dict) -> str:
    """Render concise prose from proposition roles, never from episode titles."""
    archetype = model["archetype"]
    direction = model["action_direction"]
    clusters = model["supporting_policy_clusters"]
    contrast = model.get("contrast_proposition")
    trajectory = model.get("trajectory_proposition")
    exception = model.get("exception_proposition")
    boundary = model.get("boundary_proposition")

    if archetype == "uniform_direction_without_common_policy_throughline":
        verb = "voted Nay on" if direction.get("direction") == "Nay" else "voted Yea on"
        noun = "opposition" if direction.get("direction") == "Nay" else "support"
        first = f"Across the reviewed record, {member_name} {verb} every substantive proposal."
        if contrast:
            second = (
                f"That {noun} extended both to {contrast['left']['reader_phrase']} and to "
                f"{contrast['right']['reader_phrase']}, so the uniform vote direction does not "
                f"reveal one consistent {boundary.get('policy_domain_label', 'issue-wide')} policy throughline."
            )
        else:
            second = (
                f"The uniform vote direction spans proposals without a resolved substantive relationship, "
                f"so it does not establish one common policy throughline."
            )
        return f"{first} {second}"

    if archetype in {"selective_or_conditional_pattern", "policy_mechanism_divide"} and len(clusters) >= 2:
        lead = (
            f"{member_name}'s reviewed record {'divides by policy mechanism' if archetype == 'policy_mechanism_divide' else 'shows a selective boundary'}: "
            f"{_cluster_noun_clause(clusters[0])} and {_cluster_noun_clause(clusters[1])}."
        )
        second = _optional_sentence(trajectory) or _optional_sentence(exception) or _optional_sentence(boundary)
        return f"{lead} {second}".strip()

    if archetype == "substantive_repeated_pattern" and clusters:
        if model.get("final_composition_contract") != "v1":
            lead = (
                f"Across the reviewed record, {member_name} "
                f"{_cluster_clause(clusters[0])} across multiple independent "
                "policy episodes."
            )
            second = _optional_sentence(exception) or _optional_sentence(boundary)
            return f"{lead} {second}".strip()
        episode_count = len({
            episode_id
            for cluster in clusters
            for episode_id in cluster.get("evidence_episode_ids", [])
        })
        lead = (
            f"Across {episode_count} independent "
            f"{'proposal' if episode_count == 1 else 'proposals'}, "
            f"{member_name} {_joined_cluster_clause(clusters)}."
        )
        second = _optional_sentence(exception) or _optional_sentence(boundary)
        return f"{lead} {second}".strip()

    if archetype == "bounded_episode_trajectories" and trajectory:
        return f"Across the reviewed record, {member_name}'s clearest result is bounded to related stages within an episode. {_optional_sentence(trajectory)}"

    return (
        f"The reviewed record for {member_name} does not yet support a compressed cross-episode policy conclusion. "
        "The available episode trajectories remain visible for review."
    )


def compression_report(model: dict, all_episode_ids: list[str]) -> dict:
    named = {
        episode_id
        for proposition in (
            model.get("trajectory_proposition"),
            model.get("exception_proposition"),
            model.get("boundary_proposition"),
        )
        if proposition
        for episode_id in proposition.get("evidence_episode_ids", [])
    }
    clustered = {
        episode_id
        for cluster in model.get("supporting_policy_clusters", [])
        for episode_id in cluster.get("evidence_episode_ids", [])
    }
    text = model.get("public_conclusion", "")
    return {
        "conclusion_archetype": model["archetype"],
        "sentence_roles": [
            role for role, present in (
                ("thesis", True),
                ("contrast", bool(model.get("contrast_proposition"))),
                ("trajectory", bool(model.get("trajectory_proposition"))),
                ("exception", bool(model.get("exception_proposition"))),
                ("boundary", bool(model.get("boundary_proposition"))),
            ) if present
        ],
        "source_episode_count": len(all_episode_ids),
        "policy_cluster_count": len(model.get("supporting_policy_clusters", [])),
        "individually_named_episode_count": len(named),
        "clustered_episode_proportion": round(len(clustered) / len(all_episode_ids), 3) if all_episode_ids else 0,
        "duplicated_analytical_propositions": [],
        "boundary_count": int(bool(model.get("boundary_proposition"))),
        "public_word_count": len(text.split()),
        "validation_outcome": (
            "human_exception_required"
            if model.get("review_route") == "human_exception_required"
            else "pass"
        ),
    }


def _policy_clusters(
    *,
    roll_actions: list[dict],
    complete_trajectories: list[dict],
    trait_contract: dict,
    requested_cluster_ids: list[str],
    cluster_actions: dict,
) -> list[dict]:
    episode_by_roll = {
        roll: trajectory["episode_id"]
        for trajectory in complete_trajectories
        for roll in trajectory.get("rolls", [])
    }
    action_traits = trait_contract.get("action_traits", {})
    clusters = trait_contract.get("policy_clusters", {})
    selected = []
    cluster_ids = requested_cluster_ids or sorted(clusters)
    for cluster_id in cluster_ids:
        definition = clusters.get(cluster_id)
        if not definition:
            continue
        trait_ids = set(definition.get("trait_ids", []))
        episode_ids = sorted({
            episode_by_roll.get(int(roll))
            for roll, action in ((str(item.get("roll")), item) for item in roll_actions if item.get("counting"))
            if episode_by_roll.get(int(roll))
            and trait_ids.intersection(action_traits.get(roll, {}).get("traits", []))
        })
        if not episode_ids:
            continue
        selected.append({
            "cluster_id": cluster_id,
            "reader_phrase": definition["reader_phrase"],
            "member_action_phrase": cluster_actions.get(cluster_id, "acted on"),
            "policy_trait_ids": sorted(trait_ids),
            "evidence_episode_ids": episode_ids,
        })
    return selected


def _contrast(clusters: list[dict], trait_contract: dict) -> dict | None:
    relationships = {
        frozenset(item["cluster_ids"]): item
        for item in trait_contract.get("cluster_relationships", [])
        if item.get("relationship") == "contrasts"
    }
    for index, left in enumerate(clusters):
        for right in clusters[index + 1:]:
            relation = relationships.get(frozenset((left["cluster_id"], right["cluster_id"])))
            if relation:
                return {
                    "role": "contrast",
                    "relationship": "contrasts",
                    "left": deepcopy(left),
                    "right": deepcopy(right),
                    "basis": relation.get("basis", "reviewed policy-trait relationship"),
                }
    return None


def _cluster_clause(cluster: dict) -> str:
    phrase = cluster.get("member_action_phrase", "acted on")
    return f"{phrase} {cluster['reader_phrase']}"


def _joined_cluster_clause(clusters: list[dict]) -> str:
    phrases = [cluster.get("member_action_phrase", "acted on") for cluster in clusters]
    if len(set(phrases)) == 1:
        return f"{phrases[0]} {_join_phrases([cluster['reader_phrase'] for cluster in clusters])}"
    return _join_phrases([_cluster_clause(cluster) for cluster in clusters])


def _cluster_noun_clause(cluster: dict) -> str:
    phrase = cluster.get("member_action_phrase")
    noun = {"supported": "support for", "opposed": "opposition to"}.get(phrase, "action on")
    return f"{noun} {cluster['reader_phrase']}"


def _optional_sentence(proposition: dict | None) -> str:
    if not proposition:
        return ""
    return proposition.get("public_text", "")


def _limiting_proposition(
    *,
    clusters: list[dict],
    complete_trajectories: list[dict],
    omitted_episode_ids: list[str],
    trait_contract: dict,
) -> dict | None:
    cluster_actions = {
        cluster.get("member_action_phrase")
        for cluster in clusters
        if cluster.get("member_action_phrase") in {"supported", "opposed"}
    }
    if len(cluster_actions) != 1:
        return None
    cluster_action = next(iter(cluster_actions))
    opposite = "Yea" if cluster_action == "opposed" else "Nay"
    omitted = []
    omitted_set = set(omitted_episode_ids)
    labels = trait_contract.get("episode_reader_phrases", {})
    for trajectory in complete_trajectories:
        signature = trajectory.get("action_signature", [])
        episode_id = trajectory.get("episode_id")
        if (
            episode_id in omitted_set
            and signature
            and set(signature) == {opposite}
        ):
            omitted.append({
                "episode_id": episode_id,
                "reader_phrase": labels.get(
                    episode_id,
                    f"the reviewed {trajectory.get('mechanism_family', 'policy')} episode",
                ),
            })
    if not omitted:
        return None
    omitted.sort(key=lambda item: item["reader_phrase"])
    opposite_noun = "Support" if opposite == "Yea" else "Opposition"
    pattern_noun = "opposition" if cluster_action == "opposed" else "support"
    domain = trait_contract.get("policy_domain_display", "issue-area")
    return {
        "role": "boundary",
        "analytical_relationship": "opposite_direction_limits_scope",
        "evidence_episode_ids": [item["episode_id"] for item in omitted],
        "public_text": (
            f"{opposite_noun} for "
            f"{_join_phrases([item['reader_phrase'] for item in omitted])} "
            f"means that repeated {pattern_noun} does not extend across the "
            f"entire reviewed {domain} record."
        ),
    }


def _join_phrases(values: list[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _default_label(archetype: str, direction: dict) -> str:
    if archetype == "uniform_direction_without_common_policy_throughline":
        noun = "opposition" if direction.get("direction") == "Nay" else "support"
        return f"Uniform {noun} without a common policy throughline"
    return archetype.replace("_", " ").capitalize()
