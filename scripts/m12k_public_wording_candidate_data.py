"""Human-authored M12K wording specifications and limitation treatments."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CALIFORNIA_ID = "pattern-california-vehicle-emissions-waiver-disapproval-opposition"
DOE_ID = "pattern-doe-appliance-efficiency-rule-disapproval-opposition"
BLM_ID = "pattern-blm-land-decision-disapproval-opposition"
SYNTHESIS_ID = "synthesis-congressional-disapproval-uniform-opposition"


def guard(elements: list[str]) -> dict[str, Any]:
    return {
        "statement_basis": "accepted_semantic_proposition_content",
        "raw_yea_nay_maps_to_direction": False,
        "direction_metadata_alone_establishes_public_meaning": False,
        "explicit_behavior_elements": elements,
    }


SPECS = [
    {
        "wording_item_id": "wording:issue-overview:environment-energy:119",
        "surface": "issue_overview",
        "semantic_sources": [{"source_kind": "synthesis", "source_id": SYNTHESIS_ID}],
        "public_title": "Environment & Energy",
        "primary_sentence": "Across 13 resolutions, Foushee repeatedly opposed congressional efforts to overturn EPA California vehicle-emissions waiver decisions, Energy Department appliance and equipment rules, and Bureau of Land Management land decisions.",
        "secondary_clarification": "The underlying decisions differed, and these 13 resolutions are one part of the broader reviewed Environment & Energy record.",
        "evidence_count_label": "13 resolutions · 3 repeated patterns",
        "direction_display": None,
        "retained_by_index": {
            0: "The underlying decisions differed.",
            3: "These 13 resolutions are one part of the broader reviewed Environment & Energy record.",
        },
        "compression_notes": "The overview uses the exact opposed-overturning relationship, names the three decision classes, and leaves the unrestricted-support boundary visible on the synthesis item instead of repeating a legalistic limitation list.",
        "prohibited_inference_risks": [
            "support for every underlying decision",
            "general support for environmental regulation or climate policy",
            "treating 13 resolutions as the complete reviewed record",
            "motive or ideology",
        ],
        "semantic_guard": guard(
            [
                "opposition to congressional overturning efforts",
                "13 resolutions",
                "EPA, Energy Department, and BLM decision classes",
            ]
        ),
    },
    {
        "wording_item_id": "wording:synthesis:congressional-disapproval",
        "surface": "synthesis",
        "semantic_sources": [{"source_kind": "synthesis", "source_id": SYNTHESIS_ID}],
        "public_title": "Congressional efforts to overturn agency decisions",
        "primary_sentence": "Across three repeated patterns covering 13 resolutions, Foushee opposed congressional efforts to overturn separate EPA California vehicle-emissions waiver decisions, Energy Department appliance and equipment rules, and Bureau of Land Management land decisions.",
        "secondary_clarification": "The underlying decisions covered different rules and land actions, and these votes do not show support for every part of them or for the agencies generally.",
        "evidence_count_label": "13 resolutions · 3 repeated patterns",
        "direction_display": None,
        "retained_by_index": {
            0: "The underlying decisions covered different rules and land actions.",
            1: "These votes do not show support for every part of the underlying decisions or for the agencies generally.",
        },
        "compression_notes": "The public sentence preserves the three accepted pattern classes and disapproval mechanism. Broader environmental, climate, efficiency, and BLM-policy exclusions are compressed because the copy names only the exact decisions and explicitly avoids affirmative support language.",
        "prohibited_inference_risks": [
            "unrestricted support for underlying decisions",
            "general environmental or climate-policy support",
            "general support for efficiency mandates or BLM policy",
            "motive or ideology",
        ],
        "semantic_guard": guard(
            [
                "opposition to congressional overturning efforts",
                "three distinct pattern classes",
                "13 resolutions",
                "no affirmative endorsement of underlying decisions",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:california-emissions-waivers",
        "surface": "repeated_pattern",
        "semantic_sources": [{"source_kind": "behavioral", "source_id": CALIFORNIA_ID}],
        "public_title": "California vehicle-emissions waivers",
        "primary_sentence": "Across two resolutions, Foushee opposed congressional efforts to overturn two separate EPA California vehicle-emissions waiver decisions.",
        "secondary_clarification": "The resolutions involved different waiver decisions and emissions standards; the votes do not show support for every part of the underlying rules.",
        "evidence_count_label": "2 resolutions · 2 separate decisions",
        "direction_display": None,
        "retained_by_index": {
            0: "The resolutions involved different waiver decisions and emissions standards.",
            1: "The votes do not show support for every part of the underlying rules.",
        },
        "compression_notes": "Uses public-facing waiver language while retaining both the distinct-decision boundary and the prohibition on converting opposition to overturning into unrestricted support.",
        "prohibited_inference_risks": [
            "general support for California emissions policy",
            "general support for EPA regulation",
            "support for every part of either underlying rule",
        ],
        "semantic_guard": guard(
            [
                "two resolutions",
                "two distinct EPA California waiver decisions",
                "opposition to congressional overturning efforts",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:doe-appliance-equipment-rules",
        "surface": "repeated_pattern",
        "semantic_sources": [{"source_kind": "behavioral", "source_id": DOE_ID}],
        "public_title": "Appliance and commercial-equipment rules",
        "primary_sentence": "Across four resolutions, Foushee opposed congressional efforts to overturn separate Energy Department rules for appliances and commercial equipment, including standards, certification, labeling, and enforcement.",
        "secondary_clarification": "The rules covered different products and functions; these votes do not show support for every requirement or for regulation generally.",
        "evidence_count_label": "4 resolutions · 4 separate rules",
        "direction_display": None,
        "retained_by_index": {
            0: "The rules covered different products and regulatory functions.",
            1: "These votes do not show support for every requirement or for regulation generally.",
        },
        "compression_notes": "Names the accepted range of regulatory functions and keeps the distinct-product and no-general-support boundaries in public copy.",
        "prohibited_inference_risks": [
            "support for appliance efficiency mandates generally",
            "support for regulation generally",
            "support for every underlying requirement",
        ],
        "semantic_guard": guard(
            [
                "four resolutions",
                "distinct appliance and commercial-equipment rules",
                "standards, certification, labeling, or enforcement",
                "opposition to congressional overturning efforts",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:blm-land-decisions",
        "surface": "repeated_pattern",
        "semantic_sources": [{"source_kind": "behavioral", "source_id": BLM_ID}],
        "public_title": "Bureau of Land Management decisions",
        "primary_sentence": "Across seven resolutions, Foushee opposed congressional efforts to overturn separate Bureau of Land Management decisions involving land plans, leasing, activity plans, or withdrawals.",
        "secondary_clarification": "The decisions covered different places and actions; these votes do not show support for every part of each decision or for BLM policy generally.",
        "evidence_count_label": "7 resolutions · 7 separate land decisions",
        "direction_display": None,
        "retained_by_index": {
            0: "The decisions covered different places and operative actions.",
            1: "These votes do not show support for every part of each decision or for BLM policy generally.",
        },
        "compression_notes": "Compresses the formal list of plans, amendments, leasing decisions, activity plans, and withdrawal orders while retaining their geographic and operative differences.",
        "prohibited_inference_risks": [
            "support for every BLM plan component",
            "support for BLM policy generally",
            "treating distinct geographic decisions as one land action",
        ],
        "semantic_guard": guard(
            [
                "seven resolutions",
                "distinct BLM land-management decisions",
                "plans, leasing, activity plans, or withdrawals",
                "opposition to congressional overturning efforts",
            ]
        ),
    },
]


def build_wording_definitions(
    behavioral_implementation: dict[str, Any],
    synthesis_implementation: dict[str, Any],
) -> list[dict[str, Any]]:
    behavioral = {
        row["proposition_id"]: row["accepted_candidate_content"]
        for row in behavioral_implementation["subject"]["implementation_records"]
    }
    synthesis = {
        row["synthesis_candidate_id"]: row["implemented_synthesis_content"]
        for row in synthesis_implementation["subject"]["implementation_records"]
    }
    definitions = []
    for raw in SPECS:
        spec = deepcopy(raw)
        retained_by_index = spec.pop("retained_by_index")
        treatments = []
        for ref in spec["semantic_sources"]:
            kind = ref["source_kind"]
            source_id = ref["source_id"]
            content = (
                behavioral[source_id] if kind == "behavioral" else synthesis[source_id]
            )
            for index, limitation in enumerate(content["material_limitations"]):
                public_copy = retained_by_index.get(index)
                treatments.append(
                    {
                        "source_kind": kind,
                        "source_id": source_id,
                        "source_limitation": limitation,
                        "treatment": (
                            "retained_public_copy"
                            if public_copy is not None
                            else "compressed_or_omitted"
                        ),
                        "public_copy": public_copy,
                        "reason": None
                        if public_copy is not None
                        else spec["compression_notes"],
                    }
                )
        spec["limitation_treatments"] = treatments
        definitions.append(spec)
    return definitions
