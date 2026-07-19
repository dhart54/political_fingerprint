from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = REPO_ROOT / "docs" / "editorial" / "valerie_foushee_economy_gold_v2"
OUTPUT = REPO_ROOT / "frontend" / "lib" / "valerieFousheeEconomyEditorialGold.mjs"
BUILDER = REPO_ROOT / "backend" / "scripts" / "build_valerie_foushee_economy_staged_content.py"


def load(name: str) -> dict:
    return json.loads((BUNDLE / name).read_text(encoding="utf-8"))


def load_builder():
    spec = importlib.util.spec_from_file_location("foushee_staged_builder", BUILDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_public_bundle_is_current_and_exactly_uses_proposed_fields() -> None:
    builder = load_builder()
    packet = load("review_packet.json")
    projected = builder.build_public_bundle(packet, load("claim_source_map.json"), load("source_manifest.json"))
    assert OUTPUT.read_text(encoding="utf-8") == builder.render(projected)

    by_roll = {item["roll"]: item for item in projected["interpretations"]}
    for source_item in packet["interpretations"]:
        public_item = by_roll[source_item["roll"]]
        proposed = source_item["proposed"]
        assert public_item["ten_second"] == proposed["ten_second"]
        assert public_item["thirty_second"] == proposed["thirty_second"]
        for key in ("detail", "argument_boundary", "later_history", "caveats"):
            assert public_item["two_minute"][key] == proposed["two_minute"][key]
        for key in ("supporter_argument", "opponent_argument"):
            assert public_item["two_minute"][key] == {
                "attribution": proposed["two_minute"][key]["attribution"],
                "argument": proposed["two_minute"][key]["argument"],
            }


def test_public_projection_preserves_status_counting_and_source_boundaries() -> None:
    builder = load_builder()
    projected = builder.build_public_bundle(
        load("review_packet.json"), load("claim_source_map.json"), load("source_manifest.json")
    )
    serialized = json.dumps(projected)
    assert projected["human_approval_status"] == "human_approval_pending"
    assert all(item["human_approval_status"] == "human_approval_pending" for item in projected["interpretations"])
    assert all(item["human_approval_status"] == "human_approval_pending" for item in projected["controls"])
    assert projected["slice_counts"] == {
        "substantive_rolls": 6,
        "policy_episodes": 4,
        "not_voting_records": 1,
        "context_controls": 2,
    }
    assert {item["roll"] for item in projected["controls"]} == {180, 263}
    assert next(item for item in projected["interpretations"] if item["roll"] == 310)["member_action"] == "Not Voting"
    assert "claim_id" not in serialized
    assert "human_approved" not in serialized
    assert "gold_benchmark" not in serialized

    roll_50 = next(item for item in projected["interpretations"] if item["roll"] == 50)
    roll_100 = next(item for item in projected["interpretations"] if item["roll"] == 100)
    assert not any(
        "concurrence in the Senate amendment" in source["locator"]
        for source in roll_50["two_minute"]["sources"]
    )
    assert any(
        "concurrence in the Senate amendment" in source["locator"]
        for source in roll_100["two_minute"]["sources"]
    )
    for item in projected["interpretations"] + projected["controls"]:
        item_sources = item["two_minute"]["sources"] if "two_minute" in item else item["sources"]
        assert all(set(source) == {"name", "locator", "group", "url"} for source in item_sources)
        canonical_urls = [source["url"].rstrip("/") for source in item_sources]
        assert len(canonical_urls) == len(set(canonical_urls))
