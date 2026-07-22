from copy import deepcopy
from pathlib import Path

import pytest

from backend.app.summaries.editorial_member_overlay import build_member_overlay


PUBLICATION = {"editorial_status": "human_approval_pending", "benchmark_status": "not_promoted", "production_eligible": False}
SHARED_SET = {
    "episode_set_id": "synthetic", "version": "1", "episode_map_path": "synthetic.json",
    "expected_substantive_roll_ids": [1, 2, 3], "expected_control_roll_ids": [9],
    "expected_independent_episode_ids": ["multi", "single"], "episode_rolls": {"multi": [1, 2], "single": [3]},
}


def catalog():
    row = lambda text, themes=None: {"member_trajectory": text, "practical_policy_direction": text, "theme_evidence": themes or []}
    return {
        "multi": {"mechanism_family": "multi", "relationship_to_repeated_stages": "two rolls are one episode",
                  "signatures": {"Yea|Nay": row("complete")}, "non_counting": row("incomplete")},
        "single": {"mechanism_family": "single", "signatures": {action: row(action) for action in ("Yea", "Nay", "Present", "Not Voting", "missing")}, "non_counting": row("missing")},
    }


def action(roll, value, episode_id, counting=True):
    return {"roll": roll, "action": value, "episode_id": episode_id, "counting": counting}


def build(rows=None, contract=None, interpretations=None, publication=None):
    return build_member_overlay(member={"bioguide_id": "X1", "display_name": "Alex Example"}, reviewed_period="period",
                                shared_episode_set=contract or SHARED_SET,
                                roll_actions=rows if rows is not None else [action(1, "Yea", "multi"), action(2, "Nay", "multi"), action(3, "Yea", "single")],
                                episode_action_interpretations=interpretations or catalog(), publication=publication or PUBLICATION)


def test_shared_contract_keeps_denominators_when_roll_is_omitted():
    value = build([action(1, "Yea", "multi"), action(3, "Yea", "single")])
    assert value["coverage"] == {"substantive_rolls_expected": 3, "substantive_rolls_observed": 2,
        "substantive_yes_no_actions": 2, "present_actions": 0, "not_voting_actions": 0, "missing_actions": 1,
        "independent_episodes_expected": 2, "independent_episodes_complete": 1,
        "independent_episodes_partial": 1, "independent_episodes_missing": 0}
    assert next(item for item in value["episode_trajectories"] if item["episode_id"] == "multi")["action_signature"] == ["Yea", "missing"]


def test_entirely_omitted_episode_stays_in_denominator_as_missing():
    value = build([action(3, "Yea", "single")])
    assert value["coverage"]["substantive_rolls_expected"] == 3
    assert value["coverage"]["independent_episodes_expected"] == 2
    assert value["coverage"]["independent_episodes_missing"] == 1
    multi = next(item for item in value["episode_trajectories"] if item["episode_id"] == "multi")
    assert multi["coverage_status"] == "missing"
    assert multi["action_signature"] == ["missing", "missing"]


def test_not_voting_inside_multi_roll_episode_makes_trajectory_partial_and_non_counting():
    value = build([action(1, "Yea", "multi"), action(2, "Not Voting", "multi"), action(3, "Yea", "single")])
    multi = next(item for item in value["episode_trajectories"] if item["episode_id"] == "multi")
    assert multi["coverage_status"] == "partial"
    assert multi["action_signature"] == ["Yea", "Not Voting"]
    assert multi["theme_evidence"] == []


def test_present_not_voting_and_missing_never_emit_counting_themes():
    for value in ("Present", "Not Voting"):
        overlay = build([action(1, "Yea", "multi"), action(2, "Nay", "multi"), action(3, value, "single")])
        single = overlay["episode_trajectories"][1]
        assert single["coverage_status"] == "partial"
        assert single["theme_evidence"] == []


@pytest.mark.parametrize("rows,match", [
    ([action(1, "Yea", "multi"), action(1, "Nay", "multi")], "duplicate roll"),
    ([action(99, "Yea", None)], "unknown rolls"),
    ([action(1, "Yea", "single")], "episode_id does not match"),
    ([action(9, "Yea", None, True)], "counting status does not match"),
])
def test_overlay_rejects_actions_outside_shared_contract(rows, match):
    with pytest.raises(ValueError, match=match): build(rows)


def test_contract_rejects_unknown_duplicate_or_mismatched_episode_mapping():
    duplicate = {**SHARED_SET, "expected_independent_episode_ids": ["multi", "multi", "single"]}
    mismatch = {**SHARED_SET, "episode_rolls": {"multi": [1, 2], "other": [3]}}
    duplicate_roll = {**SHARED_SET, "episode_rolls": {"multi": [1, 2], "single": [2, 3]}}
    for contract in (duplicate, mismatch, duplicate_roll):
        with pytest.raises(ValueError): build(contract=contract)


def test_overlay_rejects_duplicated_shared_facts_and_enforces_publication_gate():
    bad_catalog = deepcopy(catalog()); bad_catalog["single"]["signatures"]["Yea"]["bill_title"] = "duplicated"
    with pytest.raises(ValueError, match="duplicates shared dossier facts"): build(interpretations=bad_catalog)
    with pytest.raises(ValueError, match="production_eligible"): build(publication={**PUBLICATION, "production_eligible": True})


def test_generic_overlay_runtime_has_no_domain_member_or_party_decision_branch():
    source = (Path(__file__).parents[1] / "app/summaries/editorial_member_overlay.py").read_text(encoding="utf-8").lower()
    for forbidden in ("foushee", "aderholt", "massie", "fentanyl", "roll 32", "party ==", "party in"):
        assert forbidden not in source
