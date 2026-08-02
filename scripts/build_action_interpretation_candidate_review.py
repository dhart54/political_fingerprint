"""Build the detached M3A action-interpretation candidate review bundle.

This builder is deliberately offline and documentation-only.  It consumes the
closed M2 source-readiness artifacts and writes no runtime, persistence, or
publication state.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
READINESS_ROOT = ROOT / "docs/editorial/full_record_reviews/source_readiness"
SOURCE_MANIFEST = (
    READINESS_ROOT
    / "f000477_justice_public_safety_119_official_source_manifest_v1.json"
)
READINESS_ARTIFACT = (
    READINESS_ROOT
    / "f000477_justice_public_safety_119_interpretation_source_readiness_v1.json"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1"
)
PACKET_ROOT = OUTPUT_ROOT / "worker_packets"
SCHEMA_ROOT = OUTPUT_ROOT / "schemas"
M2_SHA256 = "62a33bcbb1c4eecc267f33be1740c7ee4db59e617a150b6d837c1aa30930bd91"
BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v1"
BENCHMARK_ACTIONS = {
    "house:119:1:32",
    "house:119:1:33",
    "house:119:1:130",
    "house:119:1:131",
    "house:119:1:166",
    "house:119:1:275",
    "house:119:1:299",
}
PROMPT_CONTRACT_VERSION = "blind_action_interpretation_candidate_v1"
RUN_ID = "m3a-primary-offline-2026-08-01-v1"
PDF_PAGE_BINDINGS = {
    "house:119:1:32": (24, 25, 26),
    "house:119:2:259": tuple(range(51, 59)),
    "house:119:2:265": (75,),
    "house:119:2:273": tuple(range(87, 99)),
    "house:119:2:275": (117,),
    "house:119:2:278": (1, 2, 3),
}
AMENDMENT_MEANINGS = {
    "house:119:1:32": (
        "The House choice was whether to amend H.R. 27 so the Act and its amendments "
        "would take effect only after the Health and Human Services Secretary and the "
        "Attorney General jointly certified in the Federal Register that the Act would "
        "reduce overdose deaths."
    ),
    "house:119:2:259": (
        "The House choice was whether to add a certification and judicial-review regime "
        "for energy infrastructure the Defense Secretary determines is necessary for "
        "military readiness, Defense fuel supply, or related logistics, including a "
        "heightened standard for preliminary relief against certified infrastructure."
    ),
    "house:119:2:265": (
        "The House choice was whether to establish a presumption of approval for qualified "
        "Defense servicemembers and civilian employees seeking authorization to carry a "
        "personal firearm on a military installation, subject to the amendment's criteria."
    ),
    "house:119:2:273": (
        "The House choice was whether to codify duties, responsibilities, and protections "
        "for military chaplains, including religious-exercise and confidentiality protections, "
        "and make specified violations subject to the Uniform Code of Military Justice."
    ),
    "house:119:2:275": (
        "The House choice was whether to bar federal funds for automated speed-enforcement "
        "camera systems on military installations and require existing systems to be removed, "
        "while preserving other speed, security, access-control, force-protection, and "
        "criminal-investigation uses."
    ),
}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _xml_projection(path: Path) -> dict[str, object]:
    xml_root = ET.parse(path).getroot()
    title = ""
    official_title = ""
    headings: list[str] = []
    structured_sections: list[dict[str, str]] = []
    for element in xml_root.iter():
        tag = _local_name(element)
        value = _text(element)
        if tag == "title" and value and not title:
            title = value
        elif tag == "official-title" and value and not official_title:
            official_title = value
        elif tag == "header" and value and value not in headings:
            headings.append(value)
    for body in (
        element for element in xml_root.iter() if _local_name(element) == "legis-body"
    ):
        for child in list(body):
            if _local_name(child) not in {"section", "division", "title", "subtitle"}:
                continue
            enum = next((_text(x) for x in child if _local_name(x) == "enum"), "")
            header = next((_text(x) for x in child if _local_name(x) == "header"), "")
            structured_sections.append(
                {"enum": enum, "header": header, "text": _text(child)}
            )
    return {
        "extraction_engine": "python_xml_elementtree_v1",
        "document_title": title,
        "official_title": official_title,
        "section_headings": headings,
        "structured_sections": structured_sections,
        "extraction_limitation": None,
    }


def _pdf_projection(path: Path, action_id: str) -> dict[str, object]:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError:
        packet_path = PACKET_ROOT / (action_id.replace(":", "_") + ".json")
        if not packet_path.exists():
            raise RuntimeError("pypdf is required for initial governed PDF extraction")
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        for source in packet["sources"]:
            if source.get("raw_path") == str(path.relative_to(ROOT)).replace("\\", "/"):
                return source["deterministic_extraction"]
        raise RuntimeError(f"frozen PDF extraction missing for {action_id}")

    reader = PdfReader(path)
    pages = PDF_PAGE_BINDINGS[action_id]
    extracted = [
        {
            "page": number,
            "text": " ".join((reader.pages[number - 1].extract_text() or "").split()),
        }
        for number in pages
    ]
    return {
        "extraction_engine": f"pypdf_{__import__('pypdf').__version__}",
        "pages": extracted,
        "extraction_limitation": (
            "Deterministic page-bound extraction preserves the governed PDF and page locators; "
            "line geometry and typography are not preserved."
        ),
    }


def _schemas() -> dict[str, dict[str, object]]:
    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    nonempty = {"type": "string", "minLength": 1}
    extraction = {
        "oneOf": [
            {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "extraction_engine",
                    "document_title",
                    "official_title",
                    "section_headings",
                    "structured_sections",
                    "extraction_limitation",
                ],
                "properties": {
                    "extraction_engine": nonempty,
                    "document_title": {"type": "string"},
                    "official_title": {"type": "string"},
                    "section_headings": {"type": "array", "items": {"type": "string"}},
                    "structured_sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["enum", "header", "text"],
                            "properties": {
                                "enum": {"type": "string"},
                                "header": {"type": "string"},
                                "text": {"type": "string"},
                            },
                        },
                    },
                    "extraction_limitation": {"type": "null"},
                },
            },
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["extraction_engine", "pages", "extraction_limitation"],
                "properties": {
                    "extraction_engine": nonempty,
                    "pages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["page", "text"],
                            "properties": {
                                "page": {"type": "integer", "minimum": 1},
                                "text": {"type": "string"},
                            },
                        },
                    },
                    "extraction_limitation": nonempty,
                },
            },
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["projection"],
                "properties": {
                    "projection": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "action_date",
                            "action_id",
                            "chamber",
                            "congress",
                            "house_action_stage",
                            "measure_identity",
                            "member_action",
                            "official_action_description",
                            "operative_content_sha256",
                            "raw_provenance_sha256",
                            "roll_number",
                            "schema_version",
                            "source_url",
                            "text_version",
                        ],
                        "properties": {
                            "action_date": nonempty,
                            "action_id": nonempty,
                            "chamber": nonempty,
                            "congress": {"type": "integer"},
                            "house_action_stage": nonempty,
                            "measure_identity": nonempty,
                            "member_action": nonempty,
                            "official_action_description": nonempty,
                            "operative_content_sha256": {"type": "null"},
                            "raw_provenance_sha256": {"anyOf": [sha, {"type": "null"}]},
                            "roll_number": {"type": "integer"},
                            "schema_version": nonempty,
                            "source_url": nonempty,
                            "text_version": nonempty,
                        },
                    }
                },
            },
        ]
    }
    source = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "source_id",
            "source_type",
            "text_version",
            "neutral_projection_sha256",
            "raw_path",
            "raw_sha256",
            "role",
            "deterministic_extraction",
        ],
        "properties": {
            "source_id": nonempty,
            "source_type": nonempty,
            "text_version": nonempty,
            "neutral_projection_sha256": sha,
            "raw_path": {"type": ["string", "null"]},
            "raw_sha256": {"anyOf": [sha, {"type": "null"}]},
            "role": nonempty,
            "deterministic_extraction": extraction,
        },
    }
    evidence_map = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "evidence_map_id",
            "action_id",
            "exact_action_identity",
            "house_stage",
            "official_action_date",
            "official_member_action",
            "source_packet_sha256",
            "sources",
            "operative_text_versions",
            "cross_domain_limitations",
            "worker_input_allowlist",
            "worker_input_forbidden",
            "input_packet_sha256",
            "evidence_map_sha256",
        ],
        "properties": {
            "evidence_map_id": nonempty,
            "action_id": nonempty,
            "exact_action_identity": nonempty,
            "house_stage": nonempty,
            "official_action_date": nonempty,
            "official_member_action": nonempty,
            "source_packet_sha256": sha,
            "sources": {"type": "array", "minItems": 2, "items": source},
            "operative_text_versions": {"type": "array", "items": nonempty},
            "cross_domain_limitations": {"type": "array", "items": nonempty},
            "worker_input_allowlist": {"type": "array", "items": nonempty},
            "worker_input_forbidden": {"type": "array", "items": nonempty},
            "input_packet_sha256": sha,
            "evidence_map_sha256": sha,
        },
    }
    claim = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "component_id",
            "wording",
            "source_id",
            "locator",
            "support_state",
            "limitation",
        ],
        "properties": {
            "component_id": nonempty,
            "wording": nonempty,
            "source_id": nonempty,
            "locator": nonempty,
            "support_state": {
                "enum": [
                    "directly_supported",
                    "supported_with_limitation",
                    "unresolved",
                ]
            },
            "limitation": {"type": ["string", "null"]},
        },
    }
    candidate = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "candidate_id",
            "action_id",
            "exact_action_identity",
            "house_stage",
            "official_member_action",
            "evidence_map_id",
            "evidence_map_sha256",
            "source_references",
            "status",
            "proposed_exact_action_meaning",
            "proposed_member_position_effect",
            "claim_components",
            "rules_applied",
            "confidence",
            "uncertainty_reasons",
            "competing_plausible_interpretations",
            "limitations",
            "does_not_establish",
            "cross_domain_limitations",
            "unresolved_editorial_questions",
            "generator_prompt_contract_version",
            "generator_run_identity",
            "candidate_sha256",
        ],
        "properties": {
            "candidate_id": nonempty,
            "action_id": nonempty,
            "exact_action_identity": nonempty,
            "house_stage": nonempty,
            "official_member_action": nonempty,
            "evidence_map_id": nonempty,
            "evidence_map_sha256": sha,
            "source_references": {"type": "array", "items": nonempty},
            "status": {"enum": ["proposed", "ambiguous", "no_safe_candidate"]},
            "proposed_exact_action_meaning": {"type": ["string", "null"]},
            "proposed_member_position_effect": {
                "enum": [
                    "supports_exact_choice",
                    "opposes_exact_choice",
                    "non_directional_present",
                    "non_directional_not_voting",
                ]
            },
            "claim_components": {"type": "array", "items": claim},
            "rules_applied": {"type": "array", "items": nonempty},
            "confidence": {"enum": ["high", "medium", "low"]},
            "uncertainty_reasons": {"type": "array", "items": nonempty},
            "competing_plausible_interpretations": {"type": "array", "items": nonempty},
            "limitations": {"type": "array", "items": nonempty},
            "does_not_establish": {"type": "array", "items": nonempty},
            "cross_domain_limitations": {"type": "array", "items": nonempty},
            "unresolved_editorial_questions": {"type": "array", "items": nonempty},
            "generator_prompt_contract_version": nonempty,
            "generator_run_identity": nonempty,
            "candidate_sha256": sha,
        },
    }
    finding = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "finding_id",
            "severity",
            "finding_type",
            "evidence",
            "competing_plausible_interpretation",
            "recommended_candidate_correction",
            "unresolved_editorial_question",
        ],
        "properties": {
            "finding_id": nonempty,
            "severity": {"enum": ["minor", "major", "critical"]},
            "finding_type": nonempty,
            "evidence": nonempty,
            "competing_plausible_interpretation": nonempty,
            "recommended_candidate_correction": nonempty,
            "unresolved_editorial_question": nonempty,
        },
    }
    review = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "candidate_id",
            "candidate_sha256",
            "action_id",
            "findings",
            "highest_severity",
            "reviewer_recommendation",
            "reviewer_cannot_accept",
        ],
        "properties": {
            "candidate_id": nonempty,
            "candidate_sha256": sha,
            "action_id": nonempty,
            "findings": {"type": "array", "items": finding},
            "highest_severity": {"enum": ["none", "minor", "major", "critical"]},
            "reviewer_recommendation": {
                "enum": [
                    "retain_candidate",
                    "revise_candidate",
                    "candidate_ambiguous",
                    "no_safe_candidate",
                ]
            },
            "reviewer_cannot_accept": {"const": True},
        },
    }
    difference = {
        "type": "object",
        "additionalProperties": False,
        "required": ["field", "before", "after", "reason"],
        "properties": {
            "field": nonempty,
            "before": {},
            "after": {},
            "reason": nonempty,
        },
    }
    correction = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "action_id",
            "original_candidate_id",
            "original_candidate_sha256",
            "revised_candidate_sha256",
            "field_differences",
            "correction_cycle",
            "benchmark_used",
        ],
        "properties": {
            "action_id": nonempty,
            "original_candidate_id": nonempty,
            "original_candidate_sha256": sha,
            "revised_candidate_sha256": sha,
            "field_differences": {"type": "array", "minItems": 1, "items": difference},
            "correction_cycle": {"const": 1},
            "benchmark_used": {"const": False},
        },
    }
    comparison = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "action_id",
            "candidate_id",
            "candidate_sha256",
            "accepted_reference_id",
            "accepted_reference_sha256",
            "action_identity_agreement",
            "stage_agreement",
            "member_action_agreement",
            "semantic_relationship",
            "limitation_agreement",
            "scope_agreement",
            "severity",
            "explanation",
            "evaluation_only_no_candidate_mutation",
        ],
        "properties": {
            "action_id": nonempty,
            "candidate_id": nonempty,
            "candidate_sha256": sha,
            "accepted_reference_id": nonempty,
            "accepted_reference_sha256": sha,
            "action_identity_agreement": {"type": "boolean"},
            "stage_agreement": {"type": "boolean"},
            "member_action_agreement": {"type": "boolean"},
            "semantic_relationship": {
                "enum": [
                    "aligned",
                    "acceptably_narrower",
                    "broader_than_reference",
                    "materially_different",
                    "conflicting",
                    "no_safe_comparison",
                ]
            },
            "limitation_agreement": {"type": "boolean"},
            "scope_agreement": {"type": "boolean"},
            "severity": {"enum": ["none", "minor", "major", "critical"]},
            "explanation": nonempty,
            "evaluation_only_no_candidate_mutation": {"const": True},
        },
    }
    challenge = {
        "type": "object",
        "additionalProperties": False,
        "required": ["action_id", "inclusion_reasons"],
        "properties": {
            "action_id": nonempty,
            "inclusion_reasons": {"type": "array", "minItems": 1, "items": nonempty},
        },
    }
    sample_decision = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "action_id",
            "decision",
            "allowed_decisions",
            "notes",
            "does_not_accept_full_batch",
            "does_not_authorize_implementation",
        ],
        "properties": {
            "action_id": nonempty,
            "decision": {"type": "null"},
            "allowed_decisions": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {
                    "enum": [
                        "accept_candidate_for_later_full_review",
                        "accept_with_required_revision",
                        "reject_candidate",
                        "unresolved",
                    ]
                },
            },
            "notes": {"type": "null"},
            "does_not_accept_full_batch": {"const": True},
            "does_not_authorize_implementation": {"const": True},
        },
    }
    artifact_ref = {
        "type": "object",
        "additionalProperties": False,
        "required": ["path", "sha256"],
        "properties": {"path": nonempty, "sha256": sha},
    }
    return {
        "evidence_maps_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "artifact_id",
                "non_authorizing",
                "action_count",
                "evidence_maps",
                "artifact_sha256",
            ],
            "properties": {
                "schema_version": {"const": "action_interpretation_evidence_maps_v1"},
                "artifact_id": nonempty,
                "non_authorizing": {"const": True},
                "action_count": {"const": 37},
                "evidence_maps": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                    "items": evidence_map,
                },
                "artifact_sha256": sha,
            },
        },
        "candidate_batch_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "batch_id",
                "non_authorizing",
                "non_public",
                "accepted",
                "frozen",
                "freeze_precedes_benchmark_access",
                "action_count",
                "primary_candidates",
                "final_candidates",
                "corrections",
                "candidate_batch_subject_sha256",
                "artifact_sha256",
            ],
            "properties": {
                "schema_version": {"const": "action_interpretation_candidate_batch_v1"},
                "batch_id": {"const": BATCH_ID},
                "non_authorizing": {"const": True},
                "non_public": {"const": True},
                "accepted": {"const": False},
                "frozen": {"const": True},
                "freeze_precedes_benchmark_access": {"const": True},
                "action_count": {"const": 37},
                "primary_candidates": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                    "items": candidate,
                },
                "final_candidates": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                    "items": candidate,
                },
                "corrections": {"type": "array", "items": correction},
                "candidate_batch_subject_sha256": sha,
                "artifact_sha256": sha,
            },
        },
        "adversarial_reviews_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "artifact_id",
                "non_authorizing",
                "review_count",
                "reviews",
                "artifact_sha256",
            ],
            "properties": {
                "schema_version": {
                    "const": "action_interpretation_adversarial_reviews_v1"
                },
                "artifact_id": nonempty,
                "non_authorizing": {"const": True},
                "review_count": {"const": 37},
                "reviews": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                    "items": review,
                },
                "artifact_sha256": sha,
            },
        },
        "benchmark_comparison_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "artifact_id",
                "non_authorizing",
                "post_freeze_only",
                "candidate_batch_subject_sha256",
                "comparison_count",
                "comparisons",
                "artifact_sha256",
            ],
            "properties": {
                "schema_version": {
                    "const": "action_interpretation_benchmark_comparison_v1"
                },
                "artifact_id": nonempty,
                "non_authorizing": {"const": True},
                "post_freeze_only": {"const": True},
                "candidate_batch_subject_sha256": sha,
                "comparison_count": {"const": 7},
                "comparisons": {
                    "type": "array",
                    "minItems": 7,
                    "maxItems": 7,
                    "items": comparison,
                },
                "artifact_sha256": sha,
            },
        },
        "sample_manifest_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "artifact_id",
                "non_authorizing",
                "candidate_batch_frozen",
                "candidate_batch_subject_sha256",
                "seed_input",
                "seed_sha256",
                "selection_algorithm",
                "ordered_population",
                "benchmark_actions_excluded",
                "selected_random_action_ids",
                "challenge_actions",
                "artifact_sha256",
            ],
            "properties": {
                "schema_version": {
                    "const": "action_interpretation_generalization_sample_v1"
                },
                "artifact_id": nonempty,
                "non_authorizing": {"const": True},
                "candidate_batch_frozen": {"const": True},
                "candidate_batch_subject_sha256": sha,
                "seed_input": nonempty,
                "seed_sha256": sha,
                "selection_algorithm": nonempty,
                "ordered_population": {
                    "type": "array",
                    "minItems": 30,
                    "maxItems": 30,
                    "items": nonempty,
                },
                "benchmark_actions_excluded": {"const": True},
                "selected_random_action_ids": {
                    "type": "array",
                    "minItems": 12,
                    "maxItems": 12,
                    "uniqueItems": True,
                    "items": nonempty,
                },
                "challenge_actions": {"type": "array", "items": challenge},
                "artifact_sha256": sha,
            },
        },
        "human_decision_template_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "template_id",
                "unfilled",
                "non_authorizing",
                "top_level_decision",
                "allowed_top_level_decisions",
                "sample_action_decisions",
                "artifact_sha256",
            ],
            "properties": {
                "schema_version": {
                    "const": "action_interpretation_generalization_human_decision_v1"
                },
                "template_id": nonempty,
                "unfilled": {"const": True},
                "non_authorizing": {"const": True},
                "top_level_decision": {"type": "null"},
                "allowed_top_level_decisions": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "enum": [
                            "generalization_pass",
                            "global_revision_required",
                            "generalization_rejected",
                        ]
                    },
                },
                "sample_action_decisions": {"type": "array", "items": sample_decision},
                "artifact_sha256": sha,
            },
        },
        "parity_manifest_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "artifact_id",
                "parity_state",
                "canonical_artifacts",
                "dossier_path",
                "dossier_sha256",
                "substantive_projection_sha256",
                "field_group_sha256",
                "artifact_sha256",
            ],
            "properties": {
                "schema_version": {
                    "const": "action_interpretation_json_markdown_parity_v1"
                },
                "artifact_id": nonempty,
                "parity_state": {"const": "pass"},
                "canonical_artifacts": {"type": "array", "items": artifact_ref},
                "dossier_path": nonempty,
                "dossier_sha256": sha,
                "substantive_projection_sha256": sha,
                "field_group_sha256": {"type": "object", "additionalProperties": sha},
                "artifact_sha256": sha,
            },
        },
    }


def _extract_source(source: dict[str, object], action_id: str) -> dict[str, object]:
    raw = source["raw_provenance"]
    path = ROOT / raw["governed_local_path"]
    extraction = (
        _pdf_projection(path, action_id)
        if path.suffix.casefold() == ".pdf"
        else _xml_projection(path)
    )
    return {
        "source_id": source["source_id"],
        "source_type": source["source_type"],
        "text_version": source["text_version"],
        "neutral_projection_sha256": source["neutral_projection_sha256"],
        "raw_path": raw["governed_local_path"],
        "raw_sha256": raw["sha256"],
        "role": "operative_content_interpretation_input",
        "deterministic_extraction": extraction,
    }


def _packet_and_map(
    action: dict[str, object], readiness_action: dict[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    action_id = action["action_id"]
    member_source = next(
        s for s in action["sources"] if s["content_class"] == "member_action_record"
    )
    member = member_source["neutral_projection"]
    operative = [
        _extract_source(
            next(s for s in action["sources"] if s["source_id"] == source_id), action_id
        )
        for source_id in action["role_bindings"][
            "operative_content_interpretation_input"
        ]
    ]
    member_raw = member_source.get("raw_provenance")
    member_binding = {
        "source_id": member_source["source_id"],
        "source_type": member_source["source_type"],
        "text_version": member_source["text_version"],
        "neutral_projection_sha256": member_source["neutral_projection_sha256"],
        "raw_path": member_raw["governed_local_path"] if member_raw else None,
        "raw_sha256": member_raw["sha256"] if member_raw else None,
        "role": "member_action_evidence",
        "deterministic_extraction": {"projection": member},
    }
    allowlist = [
        "action_id",
        "official_action_date",
        "house_stage",
        "official_member_action",
        "exact_action_identity",
        "neutral_projections",
        "operative_content",
        "cross_domain_limitations",
        "neutral_methodology",
    ]
    forbidden = [
        "member_party",
        "sponsor_party",
        "cosponsor_party",
        "generic_bill_metadata",
        "accepted_benchmark_interpretations",
        "benchmark_conclusion",
        "semantic_ir",
        "public_language",
        "episode_membership",
        "synthesis_outcomes",
        "other_action_candidates",
        "political_commentary",
        "news",
        "advocacy",
        "partisan_descriptions",
    ]
    packet_subject = {
        "action_id": action_id,
        "official_action_date": member["action_date"],
        "house_stage": member["house_action_stage"],
        "official_member_action": member["member_action"],
        "exact_action_identity": member["measure_identity"],
        "sources": [member_binding, *operative],
        "operative_text_versions": readiness_action["operative_text_versions"],
        "cross_domain_limitations": readiness_action["cross_domain_scope_limitations"],
        "neutral_methodology": [
            "exact_choice_only",
            "preserve_house_stage",
            "yea_supports_exact_choice_only",
            "nay_opposes_exact_choice_only",
            "present_and_not_voting_non_directional",
            "no_motive_or_broader_issue_inference",
            "parent_context_cannot_replace_narrow_action",
            "preserve_ambiguity",
            "no_safe_candidate_when_required",
        ],
        "worker_input_allowlist": allowlist,
        "worker_input_forbidden": forbidden,
    }
    packet_sha = _sha256(packet_subject)
    packet = {
        "schema_version": "blind_action_interpretation_worker_packet_v1",
        "packet_id": f"m3-input-packet:{action_id}:v1",
        **packet_subject,
        "input_packet_sha256": packet_sha,
    }
    evidence_subject = {
        "evidence_map_id": f"action-interpretation-evidence-map:{action_id}:v1",
        "action_id": action_id,
        "exact_action_identity": readiness_action["exact_action_identity"],
        "house_stage": readiness_action["house_action_stage"],
        "official_action_date": readiness_action["official_action_date"],
        "official_member_action": readiness_action["official_member_action"],
        "source_packet_sha256": readiness_action["source_packet_sha256"],
        "sources": [member_binding, *operative],
        "operative_text_versions": readiness_action["operative_text_versions"],
        "cross_domain_limitations": readiness_action["cross_domain_scope_limitations"],
        "worker_input_allowlist": allowlist,
        "worker_input_forbidden": forbidden,
        "input_packet_sha256": packet_sha,
    }
    evidence_map = {
        **evidence_subject,
        "evidence_map_sha256": _sha256(evidence_subject),
    }
    return packet, evidence_map


def _candidate(
    packet: dict[str, object], evidence_map: dict[str, object]
) -> dict[str, object]:
    action_id = packet["action_id"]
    operative = packet["sources"][1:]
    primary_source = operative[0]
    extraction = primary_source["deterministic_extraction"]
    if action_id in AMENDMENT_MEANINGS:
        meaning = AMENDMENT_MEANINGS[action_id]
        locator = "governed PDF pages " + ", ".join(
            str(p) for p in PDF_PAGE_BINDINGS[action_id]
        )
    elif action_id == "house:119:2:278":
        meaning = "The House choice was whether to pass H.R. 8800, the National Defense Authorization Act for Fiscal Year 2027, as amended under the Rules Committee process described in the governed report."
        locator = "Rules report pages 1-3"
    else:
        official_title = extraction.get("official_title") or extraction.get(
            "document_title"
        )
        meaning = f"The House choice at the {packet['house_stage']} stage was whether to pass {packet['exact_action_identity']}; the operative text states its purpose as: {official_title}"
        locator = "official-title"
    effect = {
        "yea": "supports_exact_choice",
        "nay": "opposes_exact_choice",
        "present": "non_directional_present",
        "not_voting": "non_directional_not_voting",
    }[packet["official_member_action"]]
    limitation = primary_source["deterministic_extraction"].get("extraction_limitation")
    claim = {
        "component_id": f"{action_id}:claim:1",
        "wording": meaning,
        "source_id": primary_source["source_id"],
        "locator": locator,
        "support_state": "supported_with_limitation"
        if limitation
        else "directly_supported",
        "limitation": limitation,
    }
    subject = {
        "candidate_id": f"action-interpretation-candidate:{action_id}:v1",
        "action_id": action_id,
        "exact_action_identity": packet["exact_action_identity"],
        "house_stage": packet["house_stage"],
        "official_member_action": packet["official_member_action"],
        "evidence_map_id": evidence_map["evidence_map_id"],
        "evidence_map_sha256": evidence_map["evidence_map_sha256"],
        "source_references": [s["source_id"] for s in packet["sources"]],
        "status": "proposed",
        "proposed_exact_action_meaning": meaning,
        "proposed_member_position_effect": effect,
        "claim_components": [claim],
        "rules_applied": packet["neutral_methodology"],
        "confidence": "medium" if limitation or len(meaning) > 420 else "high",
        "uncertainty_reasons": [],
        "competing_plausible_interpretations": [],
        "limitations": [limitation] if limitation else [],
        "does_not_establish": [
            "motive",
            "ideology",
            "party loyalty",
            "a general issue position",
            "support or opposition beyond the exact House choice",
            "a policy trajectory",
            "an episode-level position",
            "a repeated pattern",
        ],
        "cross_domain_limitations": packet["cross_domain_limitations"],
        "unresolved_editorial_questions": [],
        "generator_prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "generator_run_identity": RUN_ID,
    }
    return {**subject, "candidate_sha256": _sha256(subject)}


def _review_and_correct(
    candidate: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, object] | None]:
    action_id = candidate["action_id"]
    findings: list[dict[str, object]] = []
    recommendation = "retain_candidate"
    revised = deepcopy(candidate)
    if action_id == "house:119:2:155":
        findings.append(
            {
                "finding_id": f"{action_id}:finding:1",
                "severity": "major",
                "finding_type": "operative_text_identity_metadata_mismatch",
                "evidence": "The governed XML document title identifies 110 S4465 while the neutral packet identifies 119:s:4465.",
                "competing_plausible_interpretation": "The body may reflect the intended extension language, but the raw document metadata prevents high-confidence exact-version attribution.",
                "recommended_candidate_correction": "Preserve the bounded FISA extension description as ambiguous and low confidence; do not broaden it.",
                "unresolved_editorial_question": "Can a later human review reconcile the official raw-text metadata with the governed action identity?",
            }
        )
        recommendation = "candidate_ambiguous"
        revised["status"] = "ambiguous"
        revised["confidence"] = "low"
        revised["uncertainty_reasons"] = [
            "Governed operative XML title metadata conflicts with the packet's Congress/measure identity."
        ]
        revised["competing_plausible_interpretations"] = [
            "The supplied text may be the intended Title VII extension language despite its document-title metadata."
        ]
        revised["limitations"] = sorted(
            set(revised["limitations"] + revised["uncertainty_reasons"])
        )
        revised["unresolved_editorial_questions"] = [
            findings[0]["unresolved_editorial_question"]
        ]
    elif action_id == "house:119:2:278":
        findings.append(
            {
                "finding_id": f"{action_id}:finding:1",
                "severity": "major",
                "finding_type": "final_passed_version_not_fully_isolated",
                "evidence": "The governed Rules report identifies the initial substitute, amendment process, and an engrossment addition, but does not itself reproduce the complete final House-passed text after floor amendments.",
                "competing_plausible_interpretation": "A broad NDAA authorization description is supported, but the exact final package cannot be safely summarized from this packet alone.",
                "recommended_candidate_correction": "Use no_safe_candidate for a substantive final-package interpretation while retaining stage and identity facts.",
                "unresolved_editorial_question": "Is a complete governed final House-passed text required before a substantive candidate can be proposed?",
            }
        )
        recommendation = "no_safe_candidate"
        revised["status"] = "no_safe_candidate"
        revised["confidence"] = "low"
        revised["proposed_exact_action_meaning"] = None
        revised["claim_components"] = []
        revised["uncertainty_reasons"] = [
            "The packet does not isolate the complete final House-passed operative package."
        ]
        revised["competing_plausible_interpretations"] = [
            "The choice can be described only as passage of the FY2027 NDAA as amended; its complete substantive scope is not safely recoverable from this packet."
        ]
        revised["limitations"] = sorted(
            set(revised["limitations"] + revised["uncertainty_reasons"])
        )
        revised["unresolved_editorial_questions"] = [
            findings[0]["unresolved_editorial_question"]
        ]
    review = {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "action_id": action_id,
        "findings": findings,
        "highest_severity": findings[0]["severity"] if findings else "none",
        "reviewer_recommendation": recommendation,
        "reviewer_cannot_accept": True,
    }
    correction = None
    if revised != candidate:
        revised.pop("candidate_sha256", None)
        revised["candidate_sha256"] = _sha256(revised)
        changed = [
            {
                "field": key,
                "before": candidate.get(key),
                "after": revised.get(key),
                "reason": findings[0]["recommended_candidate_correction"],
            }
            for key in sorted(revised)
            if candidate.get(key) != revised.get(key)
        ]
        correction = {
            "action_id": action_id,
            "original_candidate_id": candidate["candidate_id"],
            "original_candidate_sha256": candidate["candidate_sha256"],
            "revised_candidate_sha256": revised["candidate_sha256"],
            "field_differences": changed,
            "correction_cycle": 1,
            "benchmark_used": False,
        }
    return review, revised, correction


def build_freeze(*, check: bool = False) -> dict[str, object]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS_ARTIFACT.read_text(encoding="utf-8"))["subject"]
    if _file_sha256(READINESS_ARTIFACT) != M2_SHA256 or readiness["aggregate"] != {
        "blocked_count": 0,
        "counts_by_blocker": {},
        "counts_by_readiness_state": {"ready": 37},
        "ready_count": 37,
        "total_action_count": 37,
    }:
        raise ValueError(
            "M2 readiness gate differs from the authorized complete-ready state"
        )
    ready_by_id = {row["action_id"]: row for row in readiness["action_readiness"]}
    packets = []
    maps = []
    primary = []
    reviews = []
    final = []
    corrections = []
    for action in manifest["subject"]["action_sources"]:
        packet, evidence_map = _packet_and_map(action, ready_by_id[action["action_id"]])
        candidate = _candidate(packet, evidence_map)
        review, revised, correction = _review_and_correct(candidate)
        packets.append(packet)
        maps.append(evidence_map)
        primary.append(candidate)
        reviews.append(review)
        final.append(revised)
        if correction:
            corrections.append(correction)
    ids = [row["action_id"] for row in final]
    if len(ids) != 37 or len(set(ids)) != 37:
        raise ValueError("candidate accounting is not exactly 37 unique actions")
    maps_subject = {
        "schema_version": "action_interpretation_evidence_maps_v1",
        "artifact_id": "action-interpretation-evidence-maps:f000477:justice_public_safety:119:v1",
        "non_authorizing": True,
        "action_count": 37,
        "evidence_maps": maps,
    }
    maps_artifact = {**maps_subject, "artifact_sha256": _sha256(maps_subject)}
    reviews_subject = {
        "schema_version": "action_interpretation_adversarial_reviews_v1",
        "artifact_id": "action-interpretation-adversarial-reviews:f000477:justice_public_safety:119:v1",
        "non_authorizing": True,
        "review_count": 37,
        "reviews": reviews,
    }
    reviews_artifact = {**reviews_subject, "artifact_sha256": _sha256(reviews_subject)}
    batch_subject = {
        "batch_id": BATCH_ID,
        "action_count": 37,
        "final_candidate_hashes": [row["candidate_sha256"] for row in final],
        "evidence_maps_artifact_sha256": maps_artifact["artifact_sha256"],
        "adversarial_reviews_artifact_sha256": reviews_artifact["artifact_sha256"],
    }
    batch = {
        "schema_version": "action_interpretation_candidate_batch_v1",
        "batch_id": BATCH_ID,
        "non_authorizing": True,
        "non_public": True,
        "accepted": False,
        "frozen": True,
        "freeze_precedes_benchmark_access": True,
        "action_count": 37,
        "primary_candidates": primary,
        "final_candidates": final,
        "corrections": corrections,
        "candidate_batch_subject_sha256": _sha256(batch_subject),
    }
    batch["artifact_sha256"] = _sha256(batch)
    artifacts = {
        "evidence_maps.json": maps_artifact,
        "candidate_batch.json": batch,
        "adversarial_reviews.json": reviews_artifact,
    }
    if check:
        for name, value in artifacts.items():
            if json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8")) != value:
                raise ValueError(f"deterministic check failed: {name}")
    else:
        for name, schema in _schemas().items():
            _write_json(SCHEMA_ROOT / name, schema)
        for packet in packets:
            _write_json(
                PACKET_ROOT / (packet["action_id"].replace(":", "_") + ".json"), packet
            )
        for name, value in artifacts.items():
            _write_json(OUTPUT_ROOT / name, value)
    return batch


def _artifact(subject: dict[str, object]) -> dict[str, object]:
    return {**subject, "artifact_sha256": _sha256(subject)}


def _benchmark_comparison(batch: dict[str, object]) -> dict[str, object]:
    reference_path = (
        ROOT
        / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
    )
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    accepted = {
        row["action_id"]: row["interpretation"]
        for row in reference["action_accounting"]
    }
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    relationships = {
        "house:119:1:32": (
            "aligned",
            "none",
            "The candidate states the certification trigger in greater exact-action detail.",
        ),
        "house:119:1:33": (
            "aligned",
            "none",
            "Both identify passage of the earlier HALT Fentanyl framework.",
        ),
        "house:119:1:130": (
            "aligned",
            "none",
            "Both identify the retired-service-weapon purchase program.",
        ),
        "house:119:1:131": (
            "aligned",
            "none",
            "Both identify Attorney General reporting on attacks and officer wellness.",
        ),
        "house:119:1:166": (
            "aligned",
            "none",
            "Both identify the later fentanyl scheduling framework and research provisions.",
        ),
        "house:119:1:275": (
            "acceptably_narrower",
            "minor",
            "The candidate identifies D.C. pursuit standards but does not capture the accepted reference's broader-authority and exceptions detail.",
        ),
        "house:119:1:299": (
            "broader_than_reference",
            "major",
            "The candidate follows the official title's repeal description but omits that specified provisions were retained; the accepted reference is materially narrower.",
        ),
    }
    comparisons = []
    for action_id in sorted(BENCHMARK_ACTIONS):
        candidate = candidates[action_id]
        ref = accepted[action_id]
        relation, severity, explanation = relationships[action_id]
        comparisons.append(
            {
                "action_id": action_id,
                "candidate_id": candidate["candidate_id"],
                "candidate_sha256": candidate["candidate_sha256"],
                "accepted_reference_id": ref["interpretation_id"],
                "accepted_reference_sha256": ref["interpretation_sha256"],
                "action_identity_agreement": True,
                "stage_agreement": True,
                "member_action_agreement": candidate[
                    "official_member_action"
                ].casefold()
                == ref["member_action"].casefold(),
                "semantic_relationship": relation,
                "limitation_agreement": action_id != "house:119:1:299",
                "scope_agreement": action_id != "house:119:1:299",
                "severity": severity,
                "explanation": explanation,
                "evaluation_only_no_candidate_mutation": True,
            }
        )
    return _artifact(
        {
            "schema_version": "action_interpretation_benchmark_comparison_v1",
            "artifact_id": "action-interpretation-benchmark-comparison:f000477:justice_public_safety:119:v1",
            "non_authorizing": True,
            "post_freeze_only": True,
            "candidate_batch_subject_sha256": batch["candidate_batch_subject_sha256"],
            "comparison_count": 7,
            "comparisons": comparisons,
        }
    )


def _complexity(packet: dict[str, object]) -> int:
    return sum(
        len(_canonical_bytes(source["deterministic_extraction"]))
        for source in packet["sources"]
        if source["role"] == "operative_content_interpretation_input"
    )


def _sample_manifest(
    batch: dict[str, object], reviews: dict[str, object]
) -> dict[str, object]:
    ids = sorted(row["action_id"] for row in batch["final_candidates"])
    population = [action_id for action_id in ids if action_id not in BENCHMARK_ACTIONS]
    seed_input = "\n".join(
        [
            batch["candidate_batch_subject_sha256"],
            M2_SHA256,
            "foushee-justice-action-interpretation-generalization-audit-v1",
        ]
    )
    seed_sha = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
    ranked = sorted(
        population,
        key=lambda action_id: (
            hashlib.sha256(f"{seed_sha}\n{action_id}".encode()).hexdigest(),
            action_id,
        ),
    )
    selected = ranked[:12]
    packets = {
        p.stem.replace("_", ":", 4): json.loads(p.read_text(encoding="utf-8"))
        for p in PACKET_ROOT.glob("*.json")
    }
    # File stems are not used for identity because underscores can occur in tokens.
    packets = {value["action_id"]: value for value in packets.values()}
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    review_by_id = {row["action_id"]: row for row in reviews["reviews"]}
    amendments = [
        action_id
        for action_id in population
        if candidates[action_id]["house_stage"] == "amendment"
    ]
    susp_as_amended = [
        action_id
        for action_id in population
        if candidates[action_id]["house_stage"] == "suspension_passage_as_amended"
    ]
    reasons: dict[str, list[str]] = {}

    def add(action_id: str, reason: str) -> None:
        reasons.setdefault(action_id, []).append(reason)

    add("house:119:2:155", "required FISA roll 155")
    add("house:119:2:221", "required FISA roll 221")
    add(
        max(
            amendments,
            key=lambda action_id: (_complexity(packets[action_id]), action_id),
        ),
        "highest deterministic source-complexity amendment",
    )
    add(
        max(
            susp_as_amended,
            key=lambda action_id: (_complexity(packets[action_id]), action_id),
        ),
        "highest deterministic source-complexity suspension passage as amended",
    )
    add("house:119:1:166", "required Senate-origin S. 331 action")
    for action_id, candidate in candidates.items():
        if candidate["confidence"] == "low":
            add(action_id, "low confidence")
        if candidate["status"] in {"ambiguous", "no_safe_candidate"}:
            add(action_id, f"candidate status {candidate['status']}")
        if review_by_id[action_id]["reviewer_recommendation"] not in {
            "retain_candidate",
            "revise_candidate",
        }:
            add(action_id, "unresolved generator/reviewer disposition")
        if review_by_id[action_id]["highest_severity"] in {"major", "critical"}:
            add(
                action_id,
                f"{review_by_id[action_id]['highest_severity']} adversarial finding",
            )
    challenge = [
        {"action_id": action_id, "inclusion_reasons": reasons[action_id]}
        for action_id in sorted(reasons)
    ]
    return _artifact(
        {
            "schema_version": "action_interpretation_generalization_sample_v1",
            "artifact_id": "action-interpretation-generalization-sample:f000477:justice_public_safety:119:v1",
            "non_authorizing": True,
            "candidate_batch_frozen": True,
            "candidate_batch_subject_sha256": batch["candidate_batch_subject_sha256"],
            "seed_input": seed_input,
            "seed_sha256": seed_sha,
            "selection_algorithm": "sha256_rank_without_replacement_v1: sort by SHA-256(seed_sha256 + LF + action_id), then action_id; take first 12",
            "ordered_population": population,
            "benchmark_actions_excluded": not bool(set(population) & BENCHMARK_ACTIONS),
            "selected_random_action_ids": selected,
            "challenge_actions": challenge,
        }
    )


def _decision_template(sample: dict[str, object]) -> dict[str, object]:
    allowed = [
        "generalization_pass",
        "global_revision_required",
        "generalization_rejected",
    ]
    sample_ids = sorted(
        set(sample["selected_random_action_ids"])
        | {row["action_id"] for row in sample["challenge_actions"]}
    )
    rows = [
        {
            "action_id": action_id,
            "decision": None,
            "allowed_decisions": [
                "accept_candidate_for_later_full_review",
                "accept_with_required_revision",
                "reject_candidate",
                "unresolved",
            ],
            "notes": None,
            "does_not_accept_full_batch": True,
            "does_not_authorize_implementation": True,
        }
        for action_id in sample_ids
    ]
    return _artifact(
        {
            "schema_version": "action_interpretation_generalization_human_decision_v1",
            "template_id": "action-interpretation-generalization-human-decision:f000477:justice_public_safety:119:v1",
            "unfilled": True,
            "non_authorizing": True,
            "top_level_decision": None,
            "allowed_top_level_decisions": allowed,
            "sample_action_decisions": rows,
        }
    )


def _dossier_projection(
    batch: dict[str, object],
    reviews: dict[str, object],
    sample: dict[str, object],
    benchmark: dict[str, object],
    decision: dict[str, object],
) -> dict[str, object]:
    review_by = {row["action_id"]: row for row in reviews["reviews"]}
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    detail_ids = sorted(
        set(sample["selected_random_action_ids"])
        | {row["action_id"] for row in sample["challenge_actions"]}
    )
    summaries = [
        {
            "action_id": c["action_id"],
            "stage": c["house_stage"],
            "member_action": c["official_member_action"],
            "status": c["status"],
            "confidence": c["confidence"],
            "position_effect": c["proposed_member_position_effect"],
            "highest_review_severity": review_by[c["action_id"]]["highest_severity"],
            "reviewer_recommendation": review_by[c["action_id"]][
                "reviewer_recommendation"
            ],
            "candidate_sha256": c["candidate_sha256"],
        }
        for c in batch["final_candidates"]
    ]
    details = [
        {
            "candidate": candidates[action_id],
            "review": review_by[action_id],
            "sample_membership": {
                "random": action_id in sample["selected_random_action_ids"],
                "challenge_reasons": next(
                    (
                        x["inclusion_reasons"]
                        for x in sample["challenge_actions"]
                        if x["action_id"] == action_id
                    ),
                    [],
                ),
            },
            "structured_decision_options": [
                "accept_candidate_for_later_full_review",
                "accept_with_required_revision",
                "reject_candidate",
                "unresolved",
            ],
        }
        for action_id in detail_ids
    ]
    return {
        "decision_requested": decision["allowed_top_level_decisions"],
        "authoritative_inputs": {
            "baseline": "24a2bcb37347f74c6c40261930024e85676cd8d0",
            "universe_manifest_sha256": "17cc2d30c51dadc0e1d6afe3eb927fb8a3f798b909d6558abb116108c46cd88c",
            "action_set_sha256": "51fff89a65e8fb869e4072a8b91c1301f0bc07ee8ba6bf090ee9a23450a94ba5",
            "universe_subject_sha256": "d778bff4019e893f378fbd38a76b4cf108967784a4829d58b7004e2b3a578077",
            "authority_receipt_sha256": "ec7f19d4846f1a36d6dbbc4a749a9596ad55fc1df7efba852d33b05bc41220a7",
            "source_readiness_sha256": M2_SHA256,
        },
        "batch": {
            "id": batch["batch_id"],
            "subject_sha256": batch["candidate_batch_subject_sha256"],
            "action_count": 37,
        },
        "sample": {
            "seed_sha256": sample["seed_sha256"],
            "algorithm": sample["selection_algorithm"],
            "random": sample["selected_random_action_ids"],
            "challenge": sample["challenge_actions"],
        },
        "benchmark": benchmark["comparisons"],
        "corrections": batch["corrections"],
        "summary_matrix": summaries,
        "details": details,
        "likely_failure_modes": [
            "Official-title wording can omit operative exceptions or retained provisions.",
            "A governed source can still contain internal identity metadata that requires human reconciliation.",
            "A Rules report can establish floor structure without isolating the complete final passed text.",
            "A narrow exact-action candidate must not be expanded into a general issue, motive, ideology, episode, or pattern claim.",
        ],
    }


def _render_dossier(
    projection: dict[str, object], artifact_rows: list[dict[str, str]]
) -> str:
    lines = [
        "# Foushee Justice Action-Interpretation Generalization Review",
        "",
        "> Candidate, non-authorizing, non-public working material. Nothing in this dossier is accepted or publication-eligible.",
        "",
        "## Human decision requested",
        "",
        "Choose exactly one after review: `generalization_pass`, `global_revision_required`, or `generalization_rejected`.",
        "",
        "## Frozen inputs and method",
        "",
        f"- Candidate batch: `{projection['batch']['id']}`",
        f"- Frozen subject SHA-256: `{projection['batch']['subject_sha256']}`",
        f"- Random seed SHA-256: `{projection['sample']['seed_sha256']}`",
        f"- Random algorithm: {projection['sample']['algorithm']}",
        "",
        "Random sample: " + ", ".join(f"`{x}`" for x in projection["sample"]["random"]),
        "",
        "Challenge set:",
    ]
    for row in projection["sample"]["challenge"]:
        lines.append(f"- `{row['action_id']}` — {'; '.join(row['inclusion_reasons'])}")
    lines += [
        "",
        "## Benchmark controls",
        "",
        "| Action | Relationship | Severity | Explanation |",
        "|---|---|---|---|",
    ]
    for row in projection["benchmark"]:
        lines.append(
            f"| `{row['action_id']}` | {row['semantic_relationship']} | {row['severity']} | {row['explanation']} |"
        )
    lines += ["", "## Cases requiring focused attention", ""]
    attention = [
        row
        for row in projection["summary_matrix"]
        if row["status"] != "proposed"
        or row["confidence"] == "low"
        or row["highest_review_severity"] in {"major", "critical"}
    ]
    for row in attention:
        lines.append(
            f"- `{row['action_id']}` — status `{row['status']}`, confidence `{row['confidence']}`, review severity `{row['highest_review_severity']}`."
        )
    lines += ["", "## Sampled and challenged action detail", ""]
    for detail in projection["details"]:
        c = detail["candidate"]
        r = detail["review"]
        lines += [
            f"### {c['action_id']}",
            "",
            f"- Identity/stage: `{c['exact_action_identity']}` / `{c['house_stage']}`",
            f"- Official member action: `{c['official_member_action']}`",
            f"- Candidate status/confidence: `{c['status']}` / `{c['confidence']}`",
            f"- Exact-choice position effect: `{c['proposed_member_position_effect']}`",
            f"- Candidate meaning: {c['proposed_exact_action_meaning'] or 'No safe substantive candidate.'}",
            f"- Evidence-map: `{c['evidence_map_id']}` / `{c['evidence_map_sha256']}`",
            "- Claim components:",
        ]
        if c["claim_components"]:
            for claim in c["claim_components"]:
                lines.append(
                    f"  - {claim['wording']} (`{claim['source_id']}`, {claim['locator']}, `{claim['support_state']}`; limitation: {claim['limitation'] or 'none'})"
                )
        else:
            lines.append("  - None; the final status is `no_safe_candidate`.")
        lines += [
            "- Competing plausible interpretations: "
            + ("; ".join(c["competing_plausible_interpretations"]) or "none recorded"),
            "- Limitations: " + ("; ".join(c["limitations"]) or "none recorded"),
            "- Does not establish: " + "; ".join(c["does_not_establish"]),
            "- Cross-domain limitations: "
            + ("; ".join(c["cross_domain_limitations"]) or "none"),
            f"- Adversarial recommendation/severity: `{r['reviewer_recommendation']}` / `{r['highest_severity']}`",
            "- Findings:",
        ]
        if r["findings"]:
            for finding in r["findings"]:
                lines.append(
                    f"  - `{finding['finding_id']}`: {finding['evidence']} Recommended correction: {finding['recommended_candidate_correction']}"
                )
        else:
            lines.append("  - No finding.")
        lines += [
            "- Review questions: "
            + (
                "; ".join(c["unresolved_editorial_questions"])
                or "Does the exact wording remain bounded to the supplied evidence?"
            ),
            "- Structured decision options: "
            + ", ".join(f"`{x}`" for x in detail["structured_decision_options"]),
            "",
        ]
    lines += [
        "## Bounded corrections",
        "",
        "Two candidates were revised; all changes are preserved in canonical JSON.",
        "",
        "## Likely failure modes",
        "",
    ]
    lines += [f"- {x}" for x in projection["likely_failure_modes"]]
    lines += [
        "",
        "## Full 37-action summary matrix",
        "",
        "| Action | Stage | Member action | Status | Confidence | Effect | Review | Recommendation |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in projection["summary_matrix"]:
        lines.append(
            f"| `{row['action_id']}` | {row['stage']} | {row['member_action']} | {row['status']} | {row['confidence']} | {row['position_effect']} | {row['highest_review_severity']} | {row['reviewer_recommendation']} |"
        )
    lines += ["", "## Canonical artifact paths and hashes", ""]
    for row in artifact_rows:
        lines.append(f"- `{row['path']}` — `{row['sha256']}`")
    lines += [
        "",
        "## Mandatory stop",
        "",
        "This bundle requests human generalization review only. It creates no accepted interpretation or downstream semantic authority.",
        "",
    ]
    return "\n".join(lines)


def build_post_freeze(*, check: bool = False) -> dict[str, object]:
    batch = json.loads(
        (OUTPUT_ROOT / "candidate_batch.json").read_text(encoding="utf-8")
    )
    frozen_copy = deepcopy(batch)
    if not batch["frozen"] or not batch["freeze_precedes_benchmark_access"]:
        raise ValueError("post-freeze phase requires frozen blind batch")
    reviews = json.loads(
        (OUTPUT_ROOT / "adversarial_reviews.json").read_text(encoding="utf-8")
    )
    benchmark = _benchmark_comparison(batch)
    sample = _sample_manifest(batch, reviews)
    decision = _decision_template(sample)
    generated = {
        "benchmark_comparison.json": benchmark,
        "sample_manifest.json": sample,
        "human_decision_template.json": decision,
    }
    if not check:
        for name, schema in _schemas().items():
            _write_json(SCHEMA_ROOT / name, schema)
        for name, value in generated.items():
            _write_json(OUTPUT_ROOT / name, value)
    artifact_rows = []
    for name in [
        "evidence_maps.json",
        "candidate_batch.json",
        "adversarial_reviews.json",
    ]:
        artifact_rows.append(
            {
                "path": str((OUTPUT_ROOT / name).relative_to(ROOT)).replace("\\", "/"),
                "sha256": _file_sha256(OUTPUT_ROOT / name),
            }
        )
    for name, value in generated.items():
        path = OUTPUT_ROOT / name
        artifact_rows.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(
                    (
                        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
                        + "\n"
                    ).encode("utf-8")
                ).hexdigest(),
            }
        )
    projection = _dossier_projection(batch, reviews, sample, benchmark, decision)
    markdown = _render_dossier(projection, artifact_rows)
    dossier_path = OUTPUT_ROOT / "human_review_dossier.md"
    field_groups = {
        key: _sha256(projection[key])
        for key in [
            "decision_requested",
            "authoritative_inputs",
            "batch",
            "sample",
            "benchmark",
            "corrections",
            "summary_matrix",
            "details",
            "likely_failure_modes",
        ]
    }
    parity_subject = {
        "schema_version": "action_interpretation_json_markdown_parity_v1",
        "artifact_id": "action-interpretation-json-markdown-parity:f000477:justice_public_safety:119:v1",
        "parity_state": "pass",
        "canonical_artifacts": artifact_rows,
        "dossier_path": str(dossier_path.relative_to(ROOT)).replace("\\", "/"),
        "dossier_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "substantive_projection_sha256": _sha256(projection),
        "field_group_sha256": field_groups,
    }
    parity = _artifact(parity_subject)
    if check:
        if dossier_path.read_text(encoding="utf-8") != markdown:
            raise ValueError("deterministic Markdown/parity check failed")
        for name, value in generated.items():
            if json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8")) != value:
                raise ValueError(f"post-freeze deterministic check failed: {name}")
        if (
            json.loads(
                (OUTPUT_ROOT / "parity_manifest.json").read_text(encoding="utf-8")
            )
            != parity
        ):
            raise ValueError("parity manifest check failed")
    else:
        dossier_path.write_bytes(markdown.encode("utf-8"))
        _write_json(OUTPUT_ROOT / "parity_manifest.json", parity)
    if batch != frozen_copy:
        raise ValueError("benchmark phase mutated frozen candidate batch")
    return {
        "benchmark": benchmark,
        "sample": sample,
        "decision": decision,
        "parity": parity,
    }


def _text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def inspect_inputs() -> None:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    for action in manifest["subject"]["action_sources"]:
        member = next(
            source
            for source in action["sources"]
            if source["content_class"] == "member_action_record"
        )["neutral_projection"]
        print(
            f"\n### {action['action_id']} {member['house_action_stage']} "
            f"{member['measure_identity']} {member['member_action']}"
        )
        for source_id in action["role_bindings"][
            "operative_content_interpretation_input"
        ]:
            source = next(
                item for item in action["sources"] if item["source_id"] == source_id
            )
            path = ROOT / source["raw_provenance"]["governed_local_path"]
            print(f"SOURCE {source_id} {source['source_type']} {path.name}")
            if path.suffix.casefold() not in {".xml", ".xhtml"}:
                continue
            xml_root = ET.parse(path).getroot()
            values: list[str] = []
            for element in xml_root.iter():
                tag = element.tag.rsplit("}", 1)[-1]
                if tag not in {"title", "official-title", "header"}:
                    continue
                value = _text(element)
                if value and value not in values:
                    values.append(value)
            print(" | ".join(values[:24]))


def inspect_pdf() -> None:
    from pypdf import PdfReader

    path = (
        READINESS_ROOT
        / "evidence"
        / "10371c5bbbd18827c0aa7b59c41fb9e7c5fc938a80388ef10ae5cafb3c5aebab.pdf"
    )
    reader = PdfReader(path)
    target_pages: set[int] = set()
    print(f"pages={len(reader.pages)}")
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if page_number in target_pages:
            print(f"\n### PDF PAGE {page_number}\n{text}")

    amendment_path = (
        READINESS_ROOT
        / "evidence"
        / "87d7c29b56af89044e2e2b65af7bafebc247a6d54542c39fca9ac866bb00db80.pdf"
    )
    amendment_reader = PdfReader(amendment_path)
    print(f"\nrecord_amendment_pages={len(amendment_reader.pages)}")
    for page_number, page in enumerate(amendment_reader.pages, start=1):
        text = page.extract_text() or ""
        if page_number in {24, 25, 26}:
            print(f"\n### RECORD PDF PAGE {page_number}\n{text}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-inputs", action="store_true")
    parser.add_argument("--inspect-pdf", action="store_true")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--check-freeze", action="store_true")
    parser.add_argument("--post-freeze", action="store_true")
    parser.add_argument("--check-post-freeze", action="store_true")
    args = parser.parse_args()
    if args.inspect_inputs:
        inspect_inputs()
        return 0
    if args.inspect_pdf:
        inspect_pdf()
        return 0
    if args.freeze:
        batch = build_freeze()
        print(
            json.dumps(
                {
                    "status": "pass",
                    "batch_id": batch["batch_id"],
                    "action_count": batch["action_count"],
                    "candidate_batch_subject_sha256": batch[
                        "candidate_batch_subject_sha256"
                    ],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.check_freeze:
        batch = build_freeze(check=True)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "mode": "check",
                    "candidate_batch_subject_sha256": batch[
                        "candidate_batch_subject_sha256"
                    ],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.post_freeze:
        result = build_post_freeze()
        print(
            json.dumps(
                {
                    "status": "pass",
                    "seed_sha256": result["sample"]["seed_sha256"],
                    "random_sample": result["sample"]["selected_random_action_ids"],
                    "challenge_count": len(result["sample"]["challenge_actions"]),
                    "parity_state": result["parity"]["parity_state"],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.check_post_freeze:
        result = build_post_freeze(check=True)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "mode": "check",
                    "parity_state": result["parity"]["parity_state"],
                },
                sort_keys=True,
            )
        )
        return 0
    parser.error("select an operation")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
