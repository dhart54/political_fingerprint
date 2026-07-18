from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = REPO_ROOT / "docs" / "editorial" / "valerie_foushee_economy_gold_v2"


def load(name: str) -> dict:
    return json.loads((BUNDLE / name).read_text(encoding="utf-8"))


def packet_by_roll() -> dict[int, dict]:
    packet = load("review_packet.json")
    return {item["roll"]: item for item in packet["interpretations"] + packet["controls"]}


def test_canonical_measures_rolls_and_dossiers() -> None:
    packet = load("review_packet.json")
    assert [item["roll"] for item in packet["interpretations"]] == [310, 285, 281, 182, 156, 100, 50]
    assert [item["roll"] for item in packet["controls"]] == [263, 180]
    dossiers = sorted((BUNDLE / "measures").glob("*.json"))
    assert len(dossiers) == 5
    identities = {json.loads(path.read_text(encoding="utf-8"))["measure_id"] for path in dossiers}
    assert identities == {"119-hr-2965", "119-hr-5371", "119-hr-3944", "119-hr-2966", "119-hconres-14"}


def test_member_actions_are_grounded_in_checked_in_clerk_snapshots() -> None:
    snapshot = load("house_clerk_roll_snapshots.json")
    packet = packet_by_roll()
    records = {row["roll"]: row for row in snapshot["records"]}
    assert snapshot["member"]["bioguide_id"] == "F000477"
    assert set(records) == set(packet)
    for roll, item in packet.items():
        expected = records[roll]["member_vote"]
        if expected == "No":
            expected = "No"
        assert item["member_action"]["recorded"] == expected
        assert records[roll]["source_url"].startswith("https://clerk.house.gov/")


def test_not_voting_and_episode_deduplication_boundaries() -> None:
    episodes = load("policy_episode_map.json")
    assert episodes["counts"] == {
        "substantive_yea_nay_rolls": 6,
        "distinct_policy_episodes": 4,
        "not_voting_records": 1,
        "controls": 2,
    }
    assert [episode["rolls"] for episode in episodes["episodes"]] == [[281, 285], [50, 100], [182], [156]]
    excluded = {row["roll"]: row["reason"] for row in episodes["excluded_records"]}
    assert excluded == {310: "not_voting", 263: "procedural_control", 180: "mixed_en_bloc_control"}


def test_repeated_measure_stages_remain_distinct() -> None:
    rows = packet_by_roll()
    assert rows[281]["stage"] == "Initial House passage"
    assert rows[285]["stage"] == "House agreement to Senate amendment"
    assert "November 21" in json.dumps(rows[281]["proposed"])
    assert "January 30" in json.dumps(rows[285]["proposed"])
    assert "did not become the final law" in rows[281]["proposed"]["ten_second"]["member_action_and_result"]
    assert "became law" in rows[285]["proposed"]["ten_second"]["member_action_and_result"]
    assert rows[50]["stage"] == "Initial House adoption"
    assert rows[100]["stage"] == "House agreement to Senate amendment"
    for roll in (50, 100):
        text = json.dumps(rows[roll]["proposed"])
        assert "did not itself change taxes" in text or "did not itself change taxes or programs" in text


def test_controls_preserve_procedural_and_mixed_bundle_boundaries() -> None:
    rows = packet_by_roll()
    assert rows[263]["control_type"] == "source_grounded_procedural_noncounting"
    assert "$8.2 billion WIC" in rows[263]["known"]
    assert "nonbinding" in rows[263]["why_single_policy_translation_is_unsafe"]
    assert rows[263]["issue_synthesis_counting"] == "excluded_control"
    assert rows[180]["control_type"] == "mixed_en_bloc_insufficient_evidence_for_single_position"
    assert "seven" in rows[180]["known"].lower()
    assert rows[180]["issue_synthesis_counting"] == "excluded_control"


def test_every_material_claim_maps_to_official_sources() -> None:
    manifest = load("source_manifest.json")
    source_ids = {source["source_id"] for source in manifest["sources"]}
    assert len(source_ids) == len(manifest["sources"])
    assert all(source["url"].startswith("https://") for source in manifest["sources"])
    claim_map = load("claim_source_map.json")
    claims = {claim["claim_id"]: claim for claim in claim_map["claims"]}
    assert len(claims) == len(claim_map["claims"])
    for claim in claims.values():
        assert claim["source_ids"]
        assert set(claim["source_ids"]) <= source_ids
        assert claim["locator"]
        assert claim["claim_support_status"]
    packet = load("review_packet.json")
    for item in packet["interpretations"]:
        assert set(item["proposed"]["two_minute"]["claim_ids"]) <= claims.keys()
    for item in packet["controls"]:
        assert set(item["claim_ids"]) <= claims.keys()
    for dossier_path in (BUNDLE / "measures").glob("*.json"):
        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
        assert set(dossier["claim_ids"]) <= claims.keys()
        assert dossier["directly_affected"]


def test_competing_arguments_are_attributed_supported_and_reviewable() -> None:
    for dossier_path in (BUNDLE / "measures").glob("*.json"):
        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
        assert dossier["argument_review_status"] == "complete_supported_pair"
        for key in ("documented_supporter_argument", "documented_opponent_argument"):
            argument = dossier[key]
            assert argument["argument"]
            assert argument["attribution"]
            assert argument["source_ids"]
            assert argument["claim_ids"]
            assert argument["support_status"] == "supported_official_attributed"
            assert argument["uncertainty_and_evidence_limits"]

    packet = load("review_packet.json")
    for item in packet["interpretations"]:
        two_minute = item["proposed"]["two_minute"]
        for key in ("supporter_argument", "opponent_argument"):
            assert two_minute[key]["argument"]
            assert two_minute[key]["attribution"]
            assert two_minute[key]["claim_id"] in two_minute["claim_ids"]
        assert two_minute["argument_boundary"]


def test_unreviewed_official_evidence_is_distinct_from_insufficient_after_review() -> None:
    contract = load("review_packet.json")["argument_evidence_status_contract"]
    unreviewed = contract["official_evidence_not_yet_reviewed"]
    insufficient = contract["insufficient_official_evidence_after_review"]
    assert unreviewed["editorial_complete"] is False
    assert unreviewed["blocking"] is True
    assert insufficient["editorial_complete"] == "human_exception_only"
    assert {"search_log", "sources_reviewed", "limitation", "human_factual_reviewer_acceptance"} <= set(
        insufficient["requires"]
    )
    assert "insufficient_official_evidence" not in contract


def test_reader_layers_comprehension_and_pending_human_review() -> None:
    packet = load("review_packet.json")
    assert packet["editorial_status"] == "human_approval_pending"
    assert "human_approved" in packet["status_constraints"]["forbidden"]
    assert "gold_benchmark" in packet["status_constraints"]["forbidden"]
    for item in packet["interpretations"]:
        assert set(item["proposed"]) == {"ten_second", "thirty_second", "two_minute"}
        assert len(item["proposed"]["ten_second"]["headline"].split()) <= 14
        assert len(item["comprehension"]) == 5
        assert all(check["expected"] and check["acceptable"] and check["misconception"] and check["field"] for check in item["comprehension"])
        assert item["material_improvement"]
        assert item["human_approval_status"] == "human_approval_pending"
        assert item["public_field_availability_proxy"]["exact_runtime_render"] is False
    for item in packet["controls"]:
        assert item["human_approval_status"] == "human_approval_pending"
        assert item["material_improvement"]
        assert item["public_field_availability_proxy"]["exact_runtime_render"] is False


def test_headlines_and_progressive_disclosure_remove_action_status_ambiguity() -> None:
    rows = packet_by_roll()
    assert rows[310]["proposed"]["ten_second"]["headline"].startswith("Did not vote")
    for roll in (285, 281, 182, 156, 100, 50):
        assert rows[roll]["proposed"]["ten_second"]["headline"].startswith("Voted against")

    roll_281_top = json.dumps(rows[281]["proposed"]["ten_second"])
    assert "short-term" in roll_281_top
    assert "November 21" in roll_281_top

    roll_100_thirty = json.dumps(rows[100]["proposed"]["thirty_second"])
    assert "$4.5 trillion" not in roll_100_thirty
    assert "$2 trillion" not in roll_100_thirty
    assert "$4.5 trillion" in rows[100]["proposed"]["two_minute"]["detail"]
    assert "$2 trillion" in rows[100]["proposed"]["two_minute"]["detail"]

    roll_182 = rows[182]["proposed"]
    assert "$17.509 billion" in roll_182["thirty_second"]["prior_baseline"]
    assert "$480 million above FY2025" in roll_182["thirty_second"]["scale_or_timing"]
    assert "$29.768 million above the FY2025 enacted level" in roll_182["two_minute"]["detail"]
    assert "above the request" not in json.dumps(roll_182)
    assert "H.R. 3944 did not itself become law" in roll_182["ten_second"]["member_action_and_result"]
    assert "Roll 180" in json.dumps(roll_182["two_minute"])


def test_synthesis_and_workflow_encode_human_review_gates() -> None:
    synthesis = (BUNDLE / "issue_synthesis.md").read_text(encoding="utf-8")
    ten_second = synthesis.split("## Proposed 10-second synthesis", 1)[1].split(
        "## Proposed 30-second synthesis", 1
    )[0]
    assert "six substantive" not in ten_second.lower()
    assert "fund federal operations" in ten_second
    assert "six substantive" in synthesis.lower()
    assert "roll 263" not in ten_second.lower()

    workflow = (BUNDLE / "editorial_workflow_contract.md").read_text(encoding="utf-8")
    required = [
        "official_evidence_not_yet_reviewed",
        "insufficient_official_evidence_after_review",
        "Full gold review",
        "Routine lower-risk review",
        "at least five nonexpert participants",
        "at least three nonexpert participants",
        "Disagreement and escalation",
        "Lifecycle ownership and service levels",
        "Automated monitoring may create alerts but cannot change approval status",
    ]
    assert all(text in workflow for text in required)


def test_candidate_copy_avoids_motive_ideology_and_recommendation_claims() -> None:
    packet = load("review_packet.json")
    public_candidates = json.dumps(
        [item["proposed"] for item in packet["interpretations"]]
        + [item["proposed_control_copy"] for item in packet["controls"]]
    ).lower()
    forbidden_assertions = [
        "because she believes",
        "because she wanted",
        "liberal lawmaker",
        "conservative lawmaker",
        "party loyalist",
        "will vote",
        "you should vote",
        "corrupt",
    ]
    assert not any(phrase in public_candidates for phrase in forbidden_assertions)


def test_generated_markdown_is_current_and_reviewable() -> None:
    script_path = REPO_ROOT / "backend" / "scripts" / "build_valerie_foushee_economy_editorial_gold_v2_review.py"
    spec = importlib.util.spec_from_file_location("gold_review_builder", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = module.render(
        load("review_packet.json"), load("claim_source_map.json"), load("source_manifest.json")
    )
    rendered_path = BUNDLE / "side_by_side_review.md"
    assert rendered_path.read_text(encoding="utf-8") == expected
    assert expected.count("Roll decision:") == 7
    assert expected.count("#### Material claim receipts") == 9
    assert expected.count("| `ten_second.headline` | [ ] | [ ] | [ ] | |") == 7
    assert expected.count("| `two_minute.supporter_argument` | [ ] | [ ] | [ ] | |") == 7
    assert expected.count("| Documented supporter argument |") == 7
    assert expected.count("| Documented opponent argument |") == 7
    assert "public_field_availability_proxy" in expected


def test_bundle_is_documentation_only_and_contains_no_production_mutation_contract() -> None:
    packet = load("review_packet.json")
    serialized = json.dumps(packet).lower()
    for forbidden_status in ("\"human_approved\"", "\"gold_benchmark\""):
        assert forbidden_status not in json.dumps(
            {
                "packet_status": packet["editorial_status"],
                "interpretations": [item["human_approval_status"] for item in packet["interpretations"]],
                "controls": [item["human_approval_status"] for item in packet["controls"]],
            }
        )
    assert "database_url" not in serialized
    assert "supabase_key" not in serialized
    assert "production write" not in serialized
