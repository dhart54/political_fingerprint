"""Human-authored M13K Education & Workforce wording specifications."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

PATTERN_ID = "pattern-education-relationship-triggered-funding-restriction-opposition"
NOTABLE_ID = "notable-hr1048-amendment-support-final-passage-opposition"


def guard(elements: list[str]) -> dict[str, Any]:
    return {
        "statement_basis": "accepted_semantic_proposition_content",
        "raw_yea_nay_maps_to_direction": False,
        "direction_metadata_alone_establishes_public_meaning": False,
        "explicit_behavior_elements": elements,
    }


SPECS = [
    {
        "wording_item_id": "wording:issue-overview:education-workforce:119",
        "surface": "issue_overview",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": PATTERN_ID},
            {"source_kind": "behavioral", "source_id": NOTABLE_ID},
        ],
        "public_title": "Education & Workforce",
        "primary_sentence": "In the reviewed Education & Workforce record, Foushee opposed two specific federal-funding restrictions tied to institutional relationships or support. Separately, on H.R. 1048, she supported a Section 117 reporting amendment and later opposed final passage of the distinct whole package.",
        "secondary_clarification": "These are separate findings, not one overall position on education, China, or foreign-influence policy.",
        "evidence_count_label": "2 findings · 4 House votes",
        "direction_display": None,
        "retained_by_source_index": {
            (
                PATTERN_ID,
                0,
            ): "The two proposals involved different federal funding streams and education sectors.",
            (
                PATTERN_ID,
                1,
            ): "The restrictions used different triggers: a Confucius Institute relationship for higher education and Chinese-government support for elementary and secondary schools.",
            (
                PATTERN_ID,
                2,
            ): "These are separate findings, not one overall position on education, China, or foreign-influence policy.",
            (
                NOTABLE_ID,
                0,
            ): "H.Amdt. 12 was a narrower amendment; final passage concerned the distinct whole package.",
            (
                NOTABLE_ID,
                1,
            ): "The final-passage choice does not identify a position on any individual H.R. 1048 component.",
            (
                NOTABLE_ID,
                2,
            ): "These are separate findings, not one overall position on education, China, or foreign-influence policy.",
            (
                NOTABLE_ID,
                3,
            ): "The H.R. 1048 finding is a mixed episode, not a change over time.",
        },
        "compression_notes": "The overview keeps the two accepted findings separate, preserves their different objects and choices, and explicitly declines the common throughline that M13J found unsafe.",
        "prohibited_inference_risks": [
            "a synthesis or common policy throughline",
            "general opposition to China-related or foreign-influence policy",
            "general opposition to education restrictions or funding conditions",
            "turning the mixed H.R. 1048 episode into directional evidence",
            "motive, ideology, or trajectory",
        ],
        "semantic_guard": guard(
            [
                "two bounded funding-restriction choices",
                "one separate mixed H.R. 1048 episode",
                "no synthesis or overall issue direction",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:education-relationship-funding-restrictions",
        "surface": "repeated_pattern",
        "semantic_sources": [{"source_kind": "behavioral", "source_id": PATTERN_ID}],
        "public_title": "Funding restrictions tied to institutional relationships or support",
        "primary_sentence": "Across two separate proposals, Foushee opposed federal-funding restrictions tied to specified relationships or support: Confucius Institute relationships at higher-education institutions in H.R. 881 and direct or indirect Chinese-government support for elementary and secondary schools in H.R. 1069.",
        "secondary_clarification": "The proposals involved different education sectors, federal funding streams, and triggering relationships or support.",
        "evidence_count_label": "2 proposals · 2 separate education sectors",
        "direction_display": None,
        "retained_by_source_index": {
            (
                PATTERN_ID,
                0,
            ): "The proposals involved different education sectors and federal funding streams.",
            (
                PATTERN_ID,
                1,
            ): "The copy names the different sectors and triggering relationship or support for each proposal.",
            (
                PATTERN_ID,
                2,
            ): "The finding is limited to these two proposals and does not establish a general position on China, foreign influence, disclosure, education funding, or school governance.",
        },
        "compression_notes": "The sentence preserves both exact triggering conditions; the clarification and limitation text prevent their compression into a broader education-funding or foreign-influence position.",
        "prohibited_inference_risks": [
            "general opposition to China-related policy",
            "general opposition to foreign-influence regulation",
            "general opposition to education funding conditions",
            "equating higher education with elementary and secondary schools",
        ],
        "semantic_guard": guard(
            [
                "two proposals",
                "two education sectors and funding streams",
                "two distinct relationship or support triggers",
                "opposition limited to the specified restrictions",
            ]
        ),
    },
    {
        "wording_item_id": "wording:notable:hr1048-amendment-final-passage",
        "surface": "notable_choice",
        "semantic_sources": [{"source_kind": "behavioral", "source_id": NOTABLE_ID}],
        "public_title": "H.R. 1048 amendment and final passage",
        "primary_sentence": "Foushee supported H.Amdt. 12's changes to Section 117 foreign-gift reporting and later opposed final passage of the distinct whole H.R. 1048 package.",
        "secondary_clarification": "The final-passage vote does not show opposition to the accepted amendment or any other individual part of the package.",
        "evidence_count_label": "1 legislative episode · 2 distinct choices",
        "direction_display": {"label": "Mixed", "symbol": "±"},
        "retained_by_source_index": {
            (
                NOTABLE_ID,
                0,
            ): "H.Amdt. 12 was a narrower Section 117 amendment; final passage concerned the distinct whole package.",
            (
                NOTABLE_ID,
                1,
            ): "The final-passage vote does not show opposition to the accepted amendment or any other individual part of the package.",
            (
                NOTABLE_ID,
                2,
            ): "The episode does not establish one overall position on foreign influence, higher education, China, or Section 117 policy.",
            (
                NOTABLE_ID,
                3,
            ): "This is one mixed legislative episode, not a change over time.",
        },
        "compression_notes": "The public copy names both distinct choices, uses a mixed display, and explicitly blocks component-level attribution from the final-passage vote.",
        "prohibited_inference_risks": [
            "opposition to H.Amdt. 12",
            "component-level attribution from final passage",
            "a general Section 117, China, foreign-influence, or higher-education position",
            "trajectory or change over time",
        ],
        "semantic_guard": guard(
            [
                "support for H.Amdt. 12",
                "opposition to final passage of the distinct whole package",
                "mixed episode with no component attribution",
                "not a trajectory",
            ]
        ),
    },
]


def build_wording_definitions(
    behavioral_implementation: dict[str, Any], synthesis_implementation: dict[str, Any]
) -> list[dict[str, Any]]:
    behavioral = {
        row["proposition_id"]: row["accepted_candidate_content"]
        for row in behavioral_implementation["subject"]["implementation_records"]
    }
    if synthesis_implementation["subject"]["implementation_records"] != []:
        raise ValueError("M13K requires the accepted M13J no-safe-synthesis state")
    definitions = []
    for raw in SPECS:
        spec = deepcopy(raw)
        retained = spec.pop("retained_by_source_index")
        treatments = []
        for ref in spec["semantic_sources"]:
            source_id = ref["source_id"]
            for index, limitation in enumerate(
                behavioral[source_id]["material_limitations"]
            ):
                public_copy = retained.get((source_id, index))
                treatments.append(
                    {
                        "source_kind": "behavioral",
                        "source_id": source_id,
                        "source_limitation": limitation,
                        "treatment": "retained_public_copy"
                        if public_copy
                        else "compressed_or_omitted",
                        "public_copy": public_copy,
                        "reason": None if public_copy else spec["compression_notes"],
                    }
                )
        spec["limitation_treatments"] = treatments
        definitions.append(spec)
    return definitions
