"""Exact M11L human public-wording decisions from the substantive review."""

from __future__ import annotations

from typing import Any


ACCEPTED_AS_WRITTEN = {
    "wording:synthesis:war-powers",
    "wording:trajectory:milcon-va",
    "wording:notable:haiti-tps",
    "wording:notable:fy2026-ndaa",
}


REVISIONS: dict[str, list[dict[str, Any]]] = {
    "wording:issue-overview:national-security-foreign:119": [
        {
            "path": ["primary_sentence"],
            "value": "Foushee repeatedly supported War Powers resolutions to remove U.S. forces from specified hostilities involving Iran, Lebanon, and Venezuela. Her security-assistance choices differed by country and proposal.",
        },
        {
            "path": ["secondary_clarification"],
            "value": "Other findings cover FISA, terrorism preparedness, military and Defense Department policy, annual appropriations, ICC sanctions, Haiti TPS, and military-force authorizations.",
        },
        {"path": ["evidence_count_label"], "value": "15 findings · 32 votes"},
    ],
    "wording:synthesis:security-assistance": [
        {
            "path": ["primary_sentence"],
            "value": "Foushee opposed proposals to restrict aid to Ukraine and Jordan, supported a measure authorizing support for Ukraine, opposed removing Taiwan security-cooperation funding, and supported an amendment barring funds in the bill from being used for Israel and reducing the Foreign Military Financing account by $3.3 billion.",
        }
    ],
    "wording:pattern:fisa-title-vii": [
        {"path": ["evidence_count_label"], "value": "2 votes · 2 bills"}
    ],
    "wording:pattern:iran-war-powers": [
        {"path": ["evidence_count_label"], "value": "5 votes · 5 resolutions"}
    ],
    "wording:pattern:lebanon-war-powers": [
        {"path": ["evidence_count_label"], "value": "2 votes · 2 resolutions"},
        {
            "limitation_public_copy_from": "These were separate resolutions, not one continuing legislative episode.",
            "value": "These were separate resolutions, not one continuing legislative action.",
        },
    ],
    "wording:pattern:venezuela-war-powers": [
        {"path": ["evidence_count_label"], "value": "2 votes · 2 resolutions"}
    ],
    "wording:pattern:terrorism-preparedness": [
        {
            "path": ["primary_sentence"],
            "value": "Supported two federal preparedness measures addressing vehicle attacks and cascading effects on critical infrastructure.",
        },
        {"path": ["evidence_count_label"], "value": "2 votes · 2 measures"},
    ],
    "wording:pattern:ukraine-assistance": [
        {
            "path": ["evidence_count_label"],
            "value": "4 votes · 4 assistance choices",
        }
    ],
    "wording:pattern:jordan-assistance": [
        {"path": ["evidence_count_label"], "value": "2 votes · 2 amendments"}
    ],
    "wording:pattern:military-dod-sex-gender": [
        {
            "path": ["public_title"],
            "value": "Military and DoD sex-and-gender amendments",
        },
        {
            "path": ["primary_sentence"],
            "value": "Opposed five amendments restricting gender-related health care or imposing requirements based on biological sex in specified military and Defense Department settings.",
        },
        {"path": ["evidence_count_label"], "value": "5 votes · 5 amendments"},
    ],
    "wording:notable:israel-fmf-reduction": [
        {
            "path": ["public_title"],
            "value": "Israel funding and Foreign Military Financing reduction",
        },
        {"path": ["evidence_count_label"], "value": "1 vote · amendment"},
    ],
    "wording:notable:aumf-repeal": [
        {"path": ["evidence_count_label"], "value": "1 vote · amendment"}
    ],
    "wording:notable:icc-sanctions": [
        {
            "path": ["primary_sentence"],
            "value": "Opposed a bill imposing sanctions over ICC efforts to investigate, arrest, detain, or prosecute protected people from the United States and its allies.",
        }
    ],
    "wording:notable:taiwan-funding": [
        {"path": ["evidence_count_label"], "value": "1 vote · amendment"}
    ],
}


def resolved_replacements(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve human-readable limitation selection to its exact list path."""

    result = []
    for replacement in REVISIONS.get(item["wording_item_id"], []):
        if "path" in replacement:
            result.append({"path": replacement["path"], "value": replacement["value"]})
            continue
        expected = replacement["limitation_public_copy_from"]
        matches = [
            index
            for index, row in enumerate(item["limitation_treatments"])
            if row["public_copy"] == expected
        ]
        if len(matches) != 1:
            raise ValueError(
                f"human limitation target differs for {item['wording_item_id']}"
            )
        result.append(
            {
                "path": ["limitation_treatments", matches[0], "public_copy"],
                "value": replacement["value"],
            }
        )
    return result


def validate_decision_ids(candidate_ids: set[str]) -> None:
    decided = ACCEPTED_AS_WRITTEN | set(REVISIONS)
    if (
        decided != candidate_ids
        or len(ACCEPTED_AS_WRITTEN) != 4
        or len(REVISIONS) != 14
    ):
        raise ValueError("M11L human decision set differs")
