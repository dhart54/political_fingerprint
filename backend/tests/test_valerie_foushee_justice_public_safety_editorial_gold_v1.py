import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/editorial/valerie_foushee_justice_public_safety_gold_v1"


def load(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def test_inventory_episode_counts_and_classes():
    packet = load("review_packet.json")
    assert packet["slice_counts"] == {"substantive_rolls": 7, "policy_episodes": 5, "not_voting_records": 0, "context_controls": 6}
    assert [row["roll"] for row in packet["interpretations"]] == [32, 33, 166, 130, 131, 275, 299]
    assert [row["roll"] for row in packet["controls"]] == [160, 161, 267, 268, 290, 291]
    assert len({row["episode_id"] for row in packet["interpretations"]}) == 5
    assert {row["roll"] for row in packet["interpretations"] if row["episode_id"] == "halt-fentanyl-legislative-path"} == {32, 33, 166}


def test_episode_inference_is_generated_from_five_independent_episodes():
    packet = load("review_packet.json")
    inference = load("episode_inference.json")
    assert packet["inference_candidate"] == inference
    assert inference["independent_episode_count"] == 5
    assert inference["assessment"] == "candidate_supported_by_current_sample"
    assert len(inference["repeated_cross_episode_themes"]) == 2
    assert next(item for item in inference["within_episode_trajectories"] if item["episode_id"] == "halt-fentanyl-legislative-path")["relationship_to_repeated_stages"]
    assert len(next(item for item in inference["episode_annotations"] if item["episode_id"] == "halt-fentanyl-legislative-path")["rolls"]) == 3
    assert inference["human_review_status"] == "human_approval_pending"
    assert "strengthen, narrow, contradict, or replace" in inference["future_expansion_rule"]


def test_every_status_stays_pending_and_sources_resolve():
    packet = load("review_packet.json")
    manifest = load("source_manifest.json")
    episodes = load("policy_episode_map.json")
    claims = load("claim_source_map.json")
    manifest_ids = {item["source_id"] for item in manifest["sources"]}
    serialized = json.dumps([packet, manifest, episodes, claims])
    assert "human_approved" not in serialized
    assert "gold_benchmark" not in serialized
    assert "productionEligible" not in serialized
    assert all(item["human_approval_status"] == "human_approval_pending" for item in manifest["sources"])
    assert all(set(item["source_ids"]) <= manifest_ids for item in claims["claims"])


def test_one_sided_argument_and_precision_boundaries_are_explicit():
    packet = load("review_packet.json")
    roll131 = next(row for row in packet["interpretations"] if row["roll"] == 131)
    assert "opponent_argument" not in roll131["two_minute"]
    assert "No adequate stage-specific opposing argument" in roll131["two_minute"]["argument_boundary"]
    assert packet["argument_evidence_review"]["roll_131"]["opponent_argument_omitted"] is True
    roll299 = next(row for row in packet["interpretations"] if row["roll"] == 299)
    assert "most" in roll299["ten_second"]["practical_choice"]


def test_generator_is_deterministic():
    result = subprocess.run([sys.executable, str(ROOT / "backend/scripts/build_valerie_foushee_justice_public_safety_editorial.py"), "--check"], cwd=ROOT)
    assert result.returncode == 0


def test_production_registry_remains_dependency_safe():
    source = (ROOT / "frontend/lib/editorialIssueProductionSlices.mjs").read_text(encoding="utf-8")
    assert "JusticePublicSafety" not in source
    assert "JUSTICE_PUBLIC_SAFETY" not in source


def test_public_source_groups_are_reader_facing_while_manifest_taxonomy_stays_internal():
    packet = load("review_packet.json")
    manifest = load("source_manifest.json")
    allowed = {
        "Vote and legislative status",
        "Bill or resolution text",
        "Nonpartisan analysis",
        "Competing arguments",
        "Additional official evidence",
    }
    public_sources = [source for row in packet["interpretations"] for source in row["two_minute"]["sources"]]
    public_sources.extend(source for row in packet["controls"] for source in row["sources"])
    assert {source["group"] for source in public_sources} <= allowed
    assert all("_" not in source["group"] for source in public_sources)
    assert any("_" in source["source_type"] for source in manifest["sources"])
    assert {source["url"] for source in public_sources} == {source["url"] for source in manifest["sources"]}
