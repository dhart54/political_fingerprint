"""Independent, assertion-led verification for the frozen M6 review package."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.editorial_presentations.compiler import canonical_digest  # noqa: E402
from app.editorial_presentations.selector import select_public_presentations  # noqa: E402


OUT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_interface_candidates/f000477_justice_public_safety_119_v1"
)
SPECIAL = {
    "house:119:1:128": "roll-128-unresolved-text-limit",
    "house:119:2:155": "roll-155-source-identity-block",
    "house:119:2:278": "roll-278-no-safe-interpretation-block",
}
PRIMARY = [
    "prop:354da734fec2fcf6",
    "prop:e76b98cf92ef34cb",
    "prop:e75e7aebbd7b2d29",
    "prop:d7e189366b477118",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify(root: Path = OUT) -> dict[str, object]:
    candidate = load(root / "public_presentation_candidate.json")
    graph = load(
        ROOT
        / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiled_semantic_ir.json"
    )["compiled_ir"]
    member = graph["members"][0]
    props = {
        item["proposition_id"]: item
        for item in member["proposition_graph"]["propositions"]
    }
    boundaries = {
        item["boundary_id"]: item
        for item in candidate["compiled_semantic_meaning"]["presentation_boundaries"]
    }
    for item in graph["source_render_constraints"]:
        boundaries[item["constraint_id"]] = {
            **item,
            "action_ids": item["action_ids"],
            "episode_ids": [],
            "presentation_target": item.get("presentation_target", "source_note"),
        }
    mappings = load(root / "analytical_string_mappings.json")
    require(
        mappings["mapping_count"] == len(mappings["mappings"]) == 22,
        "mapping accounting differs",
    )
    mapping_ids: set[str] = set()
    statement_ids: set[str] = set()
    for statement in mappings["mappings"]:
        mapping = statement["mapping"]
        require(
            statement["content_subject_sha256"]
            == canonical_digest(
                {k: v for k, v in statement.items() if k != "content_subject_sha256"}
            ),
            f"{statement['statement_id']}: stale statement digest",
        )
        require(
            mapping["mapping_id"] not in mapping_ids
            and statement["statement_id"] not in statement_ids,
            "duplicate mapping or statement ID",
        )
        mapping_ids.add(mapping["mapping_id"])
        statement_ids.add(statement["statement_id"])
        referenced = [props[item] for item in mapping["proposition_ids"]] + [
            boundaries[item] for item in mapping["boundary_ids"]
        ]
        require(
            bool(mapping["proposition_ids"]) != bool(mapping["boundary_ids"]),
            f"{statement['statement_id']}: missing or mixed semantic owner",
        )
        expected_actions = sorted(
            {
                action
                for item in referenced
                for action in item.get(
                    "evidence_action_ids", item.get("action_ids", [])
                )
            }
        )
        expected_episodes = sorted(
            {
                episode
                for item in referenced
                for episode in item.get(
                    "evidence_episode_ids", item.get("episode_ids", [])
                )
            }
        )
        require(
            mapping["action_ids"] == expected_actions,
            f"{statement['statement_id']}: broadened or narrowed action mapping",
        )
        require(
            mapping["episode_ids"] == expected_episodes,
            f"{statement['statement_id']}: broadened or narrowed episode mapping",
        )
        require(
            mapping["source_refs"] and mapping["receipt_refs"],
            f"{statement['statement_id']}: missing source or receipt",
        )

    wording = candidate["editorial_wording"]
    pattern_ids = [item["proposition_id"] for item in wording["repeated_patterns"]]
    require(pattern_ids == PRIMARY, "four primary patterns are missing or reordered")
    conclusion = wording["conclusion"]["body"]["text"]
    lower = conclusion.lower()
    require(
        "one meaningful contrast" in lower and "not a complete explanation" in lower,
        "mechanism divide is not bounded",
    )
    require(
        "firearm-access" in lower and "fraud-enforcement" in lower,
        "firearm or fraud pattern hidden",
    )
    require(
        "her record divides" not in lower and "explains the record" not in lower,
        "complete-record mechanism claim",
    )
    halt = wording["policy_trajectories"]
    require(
        len(halt) == 1
        and halt[0]["proposition_id"] == "prop:53cda8d886a88f12"
        and "one episode" in halt[0]["body"]["text"],
        "HALT trajectory is not limiting",
    )
    limitation_boundaries = {item["boundary_id"] for item in wording["limitations"]}
    require(
        limitation_boundaries == set(SPECIAL.values()), "special-roll boundaries differ"
    )

    ledger = load(root / "exact_action_ledger.json")
    action_ids = [item["canonical_action_id"] for item in ledger["records"]]
    require(
        len(action_ids) == len(set(action_ids)) == 37, "37-action reachability differs"
    )
    ledger_by_action = {item["canonical_action_id"]: item for item in ledger["records"]}
    require(
        ledger_by_action["house:119:1:128"]["confidence"] == "low"
        and ledger_by_action["house:119:1:128"]["governed_action_meaning"],
        "roll 128 restriction differs",
    )
    require(
        ledger_by_action["house:119:2:155"]["non_proposition_state"]
        and not ledger_by_action["house:119:2:155"]["proposition_ids"],
        "roll 155 gained substantive weight",
    )
    require(
        ledger_by_action["house:119:2:278"]["governed_action_meaning"] is None
        and not ledger_by_action["house:119:2:278"]["proposition_ids"],
        "roll 278 gained public meaning",
    )
    overlap = load(
        ROOT
        / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/corrected_overlap_ledger.json"
    )
    require(
        overlap["prohibited_overlap_count"] == 0,
        "duplicated analytical weight returned",
    )
    roll298 = next(
        item
        for item in overlap["action_mappings"]
        if item["action_id"] == "house:119:1:298"
    )
    primary298 = [
        item
        for item in roll298["references"]
        if item.get("conclusion_relevance") == "primary"
        and item.get("semantic_role") == "behavioral"
    ]
    require(len(primary298) == 1, "roll 298 gained duplicate primary weight")

    fixture = load(ROOT / "frontend/fixtures/foushee_justice_m6_review.json")
    require(
        fixture["presentation"]["conclusion"]["body"] == conclusion,
        "frontend conclusion differs",
    )
    require(
        [
            item["proposition_id"]
            for item in fixture["presentation"]["repeated_patterns"]
        ]
        == PRIMARY,
        "frontend patterns differ",
    )
    component = (ROOT / "frontend/components/M6ReviewPage.js").read_text(
        encoding="utf-8"
    )
    route = (ROOT / "frontend/app/review/foushee-justice-m6/page.js").read_text(
        encoding="utf-8"
    )
    require(
        "fixture.presentation" in component
        and "fixture.ledger" in component
        and "ENABLE_M6_REVIEW_FIXTURE" in route
        and "notFound()" in route,
        "review fixture is not display-only or isolated",
    )
    forbidden_in_component = [
        PATTERN
        for PATTERN in [
            "Opposition to displacing D.C.",
            "Support for terrorism-preparedness",
            "One meaningful contrast in the reviewed record",
        ]
        if PATTERN in component
    ]
    require(not forbidden_in_component, "React generates analytical text")

    controls = candidate["controls"]
    require(
        controls["editorial"]["human_approval_status"] == "human_approval_pending",
        "false editorial approval",
    )
    require(
        controls["benchmark"]["status"] == "not_promoted"
        and not controls["production"]["eligible"]
        and not controls["publication"]["active"]
        and controls["effective_public_tier"] == "receipts_only",
        "false promotion, production, publication, or public tier",
    )
    selected = select_public_presentations(
        [],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    require(
        all(item["tier"] == "receipts_only" for item in selected["presentations"]),
        "ordinary selector exposes candidate",
    )

    images = load(root / "screenshot_manifest.json")
    require(images["image_count"] == 8, "screenshot accounting differs")
    for image in images["images"]:
        require(
            sha(ROOT / image["path"]) == image["final_file_sha256"],
            f"altered screenshot: {image['filename']}",
        )
    calibration = load(root / "calibration_sample.json")
    freeze = load(root / "public_interface_freeze.json")
    risks = load(root / "launch_risk_register.json")
    expected_seed = hashlib.sha256(
        (
            candidate["provenance"]["presentation_content_sha256"]
            + risks["content_subject_sha256"]
            + "political-fingerprint-launch-calibration-v1"
        ).encode()
    ).hexdigest()
    require(
        calibration["selected_after_freeze"]
        and calibration["freeze_content_subject_sha256"]
        == freeze["content_subject_sha256"],
        "calibration preceded freeze",
    )
    require(
        calibration["seed_sha256"] == expected_seed
        and calibration["sample_count"] == len(calibration["samples"]) == 4,
        "calibration is nondeterministic",
    )
    require(
        not (
            {sample["object_id"] for sample in calibration["samples"]}
            & {
                "house:119:1:128",
                "house:119:2:155",
                "house:119:2:278",
                "prop:7a5b23c610dc467e",
            }
        ),
        "held risk entered calibration",
    )
    packet = load(root / "compact_launch_review_packet.json")
    require(
        {item["risk_id"] for item in packet["unresolved_launch_risks"]}
        == {item["risk_id"] for item in risks["unresolved"]}
        and len(packet["unresolved_launch_risks"]) == 4,
        "compact packet risk parity differs",
    )
    require(
        len(packet["blind_calibration_samples"]) == 4,
        "compact packet calibration parity differs",
    )
    template = load(root / "empty_launch_ratification_template.json")
    require(
        all(
            template[key] is None
            for key in (
                "user_decision",
                "user_identity",
                "decision_timestamp",
                "wording_approval",
                "production_eligibility_approval",
                "publication_approval",
            )
        )
        and template["risk_specific_selections"] == [],
        "ratification template was filled",
    )
    return {
        "status": "pass",
        "mappings": len(mapping_ids),
        "actions": len(action_ids),
        "primary_patterns": len(pattern_ids),
        "screenshots": images["image_count"],
        "calibration_samples": calibration["sample_count"],
        "unresolved_risks": len(risks["unresolved"]),
        "selector_isolated": True,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
