from __future__ import annotations

import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from backend.app.etl.full_record_source_readiness import (
    sha256_file,
    sha256_json,
    validate_artifact as validate_readiness_artifact,
)


SCHEMA_VERSION = "full_record_action_interpretation_candidates_v1"
CRITERIA_VERSION = "source_first_exact_action_interpretation_v1"

READY_STATE = "ready_for_action_interpretation"
BLOCKED_DISPOSITION = "source_blocked_not_interpreted"

ALLOWED_COVERAGE_ASSESSMENTS = {
    "bounded_official_purpose_summary",
    "package_level_bounded_summary",
}
ALLOWED_POSITION_EFFECTS = {
    "supports_exact_choice",
    "opposes_exact_choice",
    "non_directional_present",
    "non_directional_not_voting",
}
DESCRIPTIVE_OFFICIAL_TITLE_PREFIXES = (
    "To ",
    "Making ",
    "Directing ",
    "Providing ",
)
STRUCTURAL_CLAIM_LOCATORS = {
    "top-level-division-header",
    "top-level-title-header",
    "direct-section-header",
}
STRUCTURE_EXCLUDED_ANCESTORS = {"quoted-block", "toc", "table"}
FORBIDDEN_MEANING_TERMS = (
    "democrat",
    "republican",
    "party loyalty",
    "sponsor",
    "cosponsor",
    "ideology",
    "left-wing",
    "right-wing",
)
DOES_NOT_ESTABLISH = (
    "motive",
    "ideology",
    "party loyalty",
    "a general issue position",
    "support or opposition beyond the exact House choice",
    "a policy episode",
    "a policy trajectory",
    "a repeated pattern",
    "a synthesis conclusion",
    "public wording",
)


class ActionInterpretationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ActionInterpretationError(message)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _normalized_element_text(element: ElementTree.Element) -> str:
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def _direct_header(element: ElementTree.Element) -> str | None:
    for child in element:
        if _local_name(child.tag) == "header":
            wording = _normalized_element_text(child)
            return wording or None
    return None


def _top_level_structure(root: ElementTree.Element) -> dict[str, Any] | None:
    parent_by_id = {
        id(child): parent for parent in root.iter() for child in list(parent)
    }

    def ancestors(element: ElementTree.Element) -> list[str]:
        names: list[str] = []
        parent = parent_by_id.get(id(element))
        while parent is not None:
            names.append(_local_name(parent.tag))
            parent = parent_by_id.get(id(parent))
        return names

    divisions: list[dict[str, Any]] = []
    for element in root.iter():
        if _local_name(element.tag) != "division":
            continue
        ancestor_names = ancestors(element)
        if (
            STRUCTURE_EXCLUDED_ANCESTORS.intersection(ancestor_names)
            or "division" in ancestor_names
        ):
            continue
        header = _direct_header(element)
        if header:
            divisions.append({"heading": header, "subheadings": []})
    if len(divisions) >= 2:
        return {"level": "division", "components": divisions}

    titles: list[dict[str, Any]] = []
    for element in root.iter():
        if _local_name(element.tag) != "title":
            continue
        ancestor_names = ancestors(element)
        if (
            STRUCTURE_EXCLUDED_ANCESTORS.intersection(ancestor_names)
            or "division" in ancestor_names
            or "title" in ancestor_names
        ):
            continue
        header = _direct_header(element)
        if not header:
            continue
        section_headers: list[str] = []
        for child in element:
            if _local_name(child.tag) != "section":
                continue
            section_header = _direct_header(child)
            if not section_header:
                continue
            normalized = section_header.casefold()
            if (
                normalized.startswith("short title")
                or "table of contents" in normalized
            ):
                continue
            section_headers.append(section_header)
        titles.append({"heading": header, "subheadings": section_headers})
    if len(titles) >= 2 or (len(titles) == 1 and len(titles[0]["subheadings"]) >= 2):
        return {"level": "title", "components": titles}
    return None


def _format_series(items: list[str]) -> str:
    _require(bool(items), "cannot format empty structural series")
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return "; ".join(items[:-1]) + f"; and {items[-1]}"


def _structured_meaning(
    *, label: str, action_verb: str, title: str, structure: dict[str, Any]
) -> str:
    components = structure["components"]
    if structure["level"] == "division":
        headings = [item["heading"] for item in components]
        return (
            f"The House choice was whether to {action_verb} {label}, the {title} "
            f"package, whose top-level divisions cover {_format_series(headings)}."
        )

    title_summaries = []
    for component in components:
        wording = component["heading"]
        if component["subheadings"]:
            wording += f" (sections on {_format_series(component['subheadings'])})"
        title_summaries.append(wording)
    return (
        f"The House choice was whether to {action_verb} {label} as a multi-title "
        "operative package. Its directly encoded structure includes "
        f"{_format_series(title_summaries)}."
    )


def _structural_claim_components(
    *, action_id: str, source_id: str, structure: dict[str, Any]
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    index = 0
    for component in structure["components"]:
        index += 1
        claims.append(
            {
                "component_id": f"{action_id}:structure:{index}",
                "wording": component["heading"],
                "source_id": source_id,
                "locator": f"top-level-{structure['level']}-header",
                "support_state": "directly_supported",
            }
        )
        for subheading in component["subheadings"]:
            index += 1
            claims.append(
                {
                    "component_id": f"{action_id}:structure:{index}",
                    "wording": subheading,
                    "source_id": source_id,
                    "locator": "direct-section-header",
                    "support_state": "directly_supported",
                }
            )
    return claims


def _governed_path(relative: str, *, repository_root: Path) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ActionInterpretationError("unsafe governed evidence path")
    path = (repository_root / candidate).resolve()
    governed_root = (
        repository_root / "docs/editorial/full_record_reviews/source_readiness/evidence"
    ).resolve()
    if governed_root not in path.parents:
        raise ActionInterpretationError("evidence path outside governed root")
    if not path.is_file():
        raise ActionInterpretationError(f"governed evidence missing: {relative}")
    return path


def _identity_label(identity: str) -> str:
    congress, kind, number = identity.split(":")
    del congress
    labels = {
        "hr": "H.R.",
        "s": "S.",
        "hconres": "H.Con.Res.",
        "hjres": "H.J.Res.",
        "hres": "H.Res.",
        "hamdt": "H.Amdt.",
    }
    return f"{labels.get(kind, kind.upper())} {number}"


def _position_effect(member_action: str) -> str:
    mapping = {
        "yea": "supports_exact_choice",
        "nay": "opposes_exact_choice",
        "present": "non_directional_present",
        "not_voting": "non_directional_not_voting",
    }
    try:
        return mapping[member_action]
    except KeyError as exc:
        raise ActionInterpretationError(
            f"unsupported official member action: {member_action}"
        ) from exc


def _xml_summary(path: Path) -> dict[str, Any]:
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise ActionInterpretationError(f"invalid operative XML: {path}") from exc

    official_titles: list[str] = []
    short_titles: list[str] = []
    headers: list[str] = []
    for element in root.iter():
        name = _local_name(element.tag)
        text = _normalized_element_text(element)
        if not text:
            continue
        if name == "official-title" and text not in official_titles:
            official_titles.append(text)
        elif name == "short-title" and text not in short_titles:
            short_titles.append(text)
        elif name == "header" and text not in headers:
            headers.append(text)

    title = next(iter(official_titles), None) or next(iter(short_titles), None)
    _require(bool(title), f"operative XML has no official or short title: {path}")
    return {
        "official_title": title,
        "official_titles": official_titles,
        "short_titles": short_titles,
        "sample_headers": headers[:12],
        "descriptive_official_title": bool(official_titles)
        and title.startswith(DESCRIPTIVE_OFFICIAL_TITLE_PREFIXES),
        "top_level_structure": _top_level_structure(root),
    }


def _measure_meaning(
    *,
    identity: str,
    mechanism_class: str,
    source: dict[str, Any],
    repository_root: Path,
) -> tuple[
    str,
    str,
    str,
    list[str],
    list[str],
    str,
    list[dict[str, Any]],
]:
    raw = source["raw_provenance"]
    path = _governed_path(raw["governed_local_path"], repository_root=repository_root)
    summary = _xml_summary(path)
    title = summary["official_title"]
    label = _identity_label(identity)
    descriptive_title = summary["descriptive_official_title"]
    structure = summary["top_level_structure"]
    package_level = (
        path.stat().st_size >= 100_000
        or len(summary["short_titles"]) >= 3
        or title.casefold().startswith("making appropriations")
        or (not descriptive_title and structure is not None)
    )
    action_verb = "adopt" if mechanism_class == "resolution" else "pass"
    locator = "official-title" if descriptive_title else "structured_operative_summary"
    structural_claims: list[dict[str, Any]] = []

    if not descriptive_title:
        _require(
            structure is not None,
            "short or proper title lacks safe top-level operative structure: "
            f"{identity}",
        )
        meaning = _structured_meaning(
            label=label,
            action_verb=action_verb,
            title=title,
            structure=structure,
        )
        structural_claims = _structural_claim_components(
            action_id="pending",
            source_id=source["source_id"],
            structure=structure,
        )
    elif title.startswith("To "):
        meaning = (
            f"The House choice was whether to {action_verb} {label}, which would "
            f"{title[3:]}"
        )
    elif title.startswith("Making "):
        meaning = (
            f"The House choice was whether to {action_verb} {label}, which would make "
            f"{title[7:]}"
        )
    elif title.startswith("Directing "):
        meaning = (
            f"The House choice was whether to {action_verb} {label}, which would direct "
            f"{title[10:]}"
        )
    elif title.startswith("Providing "):
        meaning = (
            f"The House choice was whether to {action_verb} {label}, which would provide "
            f"{title[10:]}"
        )
    else:
        meaning = (
            f"The House choice was whether to {action_verb} {label}, an operative measure "
            f"titled “{title}”."
        )
    meaning = meaning.rstrip()
    if not meaning.endswith((".", "?")):
        meaning += "."

    limitations: list[str] = []
    uncertainty: list[str] = []
    if package_level:
        coverage = "package_level_bounded_summary"
        limitations.append(
            "This is a whole-package choice spanning multiple provisions. The "
            "candidate does not attribute the member's action to any individual "
            "component of the package."
        )
        uncertainty.append(
            "The package-level candidate intentionally does not enumerate every "
            "operative provision."
        )
    else:
        coverage = "bounded_official_purpose_summary"
        if "and for other purposes" in title.casefold():
            limitations.append(
                "The official purpose includes ‘and for other purposes’; this "
                "candidate states the bounded official purpose and does not imply "
                "that it exhaustively enumerates every provision."
            )
    return (
        meaning,
        title,
        coverage,
        limitations,
        uncertainty,
        locator,
        structural_claims,
    )


def _amendment_meaning(
    *, identity: str, source: dict[str, Any]
) -> tuple[str, str, str, list[str], list[str]]:
    projection = source["neutral_projection"]
    official = projection.get("official_purpose") or projection.get(
        "official_description"
    )
    _require(bool(official), f"exact amendment description missing: {identity}")
    official = re.sub(r"\s+", " ", str(official)).strip()
    label = _identity_label(identity)
    meaning = (
        f"The House choice was whether to adopt {label}. The official exact-amendment "
        f"description states: “{official}”"
    )
    return (
        meaning,
        official,
        "bounded_official_purpose_summary",
        [],
        [],
    )


def _source_bindings(record: dict[str, Any]) -> list[dict[str, Any]]:
    roles_by_source: dict[str, list[str]] = {}
    for role, source_ids in record["source_roles"].items():
        for source_id in source_ids:
            roles_by_source.setdefault(source_id, []).append(role)

    bindings = []
    for source in sorted(record["sources"], key=lambda item: item["source_id"]):
        bindings.append(
            {
                "source_id": source["source_id"],
                "roles": sorted(roles_by_source.get(source["source_id"], [])),
                "source_type": source["source_type"],
                "content_class": source["content_class"],
                "source_url": source["source_url"],
                "raw_provenance": deepcopy(source["raw_provenance"]),
                "neutral_projection_sha256": source["neutral_projection_sha256"],
            }
        )
    return bindings


def _build_evidence_map(
    record: dict[str, Any], *, candidate_namespace: str
) -> dict[str, Any]:
    action_id = record["action_id"]
    subject = {
        "action_id": action_id,
        "exact_action_identity": record["exact_action_identity"],
        "house_action_stage": record["house_action_stage"],
        "source_packet_sha256": record["source_packet_sha256"],
        "source_bindings": _source_bindings(record),
    }
    return {
        "evidence_map_id": (
            f"action-interpretation-evidence-map:{action_id}:{candidate_namespace}:v1"
        ),
        **subject,
        "evidence_map_subject_sha256": sha256_json(subject),
    }


def _build_candidate(
    record: dict[str, Any],
    *,
    evidence_map: dict[str, Any],
    repository_root: Path,
    candidate_namespace: str,
) -> dict[str, Any]:
    action_id = record["action_id"]
    identity = record["exact_action_identity"]
    operative_ids = record["source_roles"]["operative_content_interpretation_input"]
    _require(len(operative_ids) == 1, f"operative source count: {action_id}")
    sources = {source["source_id"]: source for source in record["sources"]}
    operative = sources[operative_ids[0]]

    if record["mechanism_class"] == "amendment":
        meaning, official, coverage, limitations, uncertainty = _amendment_meaning(
            identity=identity, source=operative
        )
        locator = "official_purpose_or_description"
        structural_claims: list[dict[str, Any]] = []
    else:
        (
            meaning,
            official,
            coverage,
            limitations,
            uncertainty,
            locator,
            structural_claims,
        ) = _measure_meaning(
            identity=identity,
            mechanism_class=record["mechanism_class"],
            source=operative,
            repository_root=repository_root,
        )
        for index, claim in enumerate(structural_claims, start=1):
            claim["component_id"] = f"{action_id}:structure:{index}"

    limitations.extend(record.get("material_limitations", []))
    position_effect = _position_effect(record["official_member_action"])
    status = "proposed_with_material_limitation" if limitations else "proposed"
    confidence = "medium" if limitations else "high"

    subject = {
        "action_id": action_id,
        "candidate_id": (
            f"action-interpretation-candidate:{action_id}:{candidate_namespace}:v1"
        ),
        "exact_action_identity": identity,
        "house_action_stage": record["house_action_stage"],
        "mechanism_class": record["mechanism_class"],
        "official_member_action": record["official_member_action"],
        "official_action_date": record["official_action_date"],
        "evidence_map_id": evidence_map["evidence_map_id"],
        "evidence_map_subject_sha256": evidence_map["evidence_map_subject_sha256"],
        "source_references": sorted(
            {
                source_id
                for values in record["source_roles"].values()
                for source_id in values
            }
        ),
        "status": status,
        "coverage_assessment": coverage,
        "official_title_or_purpose": {
            "wording": official,
            "source_id": operative["source_id"],
            "locator": locator,
        },
        "proposed_exact_action_meaning": meaning,
        "proposed_member_position_effect": position_effect,
        "claim_components": [
            {
                "component_id": f"{action_id}:meaning",
                "wording": meaning,
                "source_id": operative["source_id"],
                "locator": locator,
                "support_state": (
                    "supported_with_limitation" if limitations else "directly_supported"
                ),
            }
        ]
        + structural_claims,
        "rules_applied": [
            "exact_recorded_action_controls",
            "meaning_before_member_position_effect",
            "exact_amendment_evidence_controls"
            if record["mechanism_class"] == "amendment"
            else "stage_compatible_operative_text_controls",
            "party_sponsor_ideology_and_synthesis_excluded",
            "material_ambiguity_preserved",
        ]
        + (
            ["short_or_proper_title_requires_structured_operative_summary"]
            if locator == "structured_operative_summary"
            else []
        ),
        "confidence": confidence,
        "uncertainty_reasons": uncertainty,
        "limitations": limitations,
        "competing_plausible_interpretations": [],
        "does_not_establish": list(DOES_NOT_ESTABLISH),
        "unresolved_editorial_questions": (
            [
                "Human review must decide whether this package-level bounded "
                "meaning is sufficient for later action-meaning acceptance."
            ]
            if coverage == "package_level_bounded_summary"
            else []
        ),
        "review_route": "human_action_meaning_review_required",
        "accepted": False,
        "authorizing": False,
    }
    return {**subject, "candidate_content_subject_sha256": sha256_json(subject)}


def build_candidate_artifact(
    *,
    readiness_artifact: dict[str, Any],
    repository_root: Path,
    artifact_id: str,
    post_merge_base: str,
    upstream_bindings: dict[str, Any],
    candidate_namespace: str = "m11c",
    source_readiness_merge_base_field: str = "post_m11b_merge_base",
) -> dict[str, Any]:
    _require(
        bool(re.fullmatch(r"[a-z][a-z0-9_]*", candidate_namespace)),
        "invalid candidate namespace",
    )
    _require(
        source_readiness_merge_base_field
        in {"post_m11b_merge_base", "post_source_readiness_merge_base"},
        "invalid source-readiness merge-base field",
    )
    validate_readiness_artifact(readiness_artifact, repository_root=repository_root)
    records = readiness_artifact["subject"]["action_readiness"]
    evidence_maps: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    accounting: list[dict[str, Any]] = []

    for record in sorted(records, key=lambda item: item["action_id"]):
        if record["readiness_state"] == READY_STATE:
            evidence_map = _build_evidence_map(
                record, candidate_namespace=candidate_namespace
            )
            candidate = _build_candidate(
                record,
                evidence_map=evidence_map,
                repository_root=repository_root,
                candidate_namespace=candidate_namespace,
            )
            evidence_maps.append(evidence_map)
            candidates.append(candidate)
            accounting.append(
                {
                    "action_id": record["action_id"],
                    "readiness_state": READY_STATE,
                    "disposition": "candidate_interpretation_proposed",
                    "candidate_id": candidate["candidate_id"],
                    "candidate_content_subject_sha256": candidate[
                        "candidate_content_subject_sha256"
                    ],
                    "source_packet_sha256": record["source_packet_sha256"],
                }
            )
        else:
            accounting.append(
                {
                    "action_id": record["action_id"],
                    "readiness_state": record["readiness_state"],
                    "disposition": BLOCKED_DISPOSITION,
                    "candidate_id": None,
                    "candidate_content_subject_sha256": None,
                    "source_packet_sha256": record["source_packet_sha256"],
                }
            )

    aggregate = {
        "approved_universe_count": len(records),
        "interpretation_eligible_count": len(candidates),
        "candidate_count": len(candidates),
        "source_blocked_count": len(records) - len(candidates),
        "evidence_source_binding_count": sum(
            len(item["source_bindings"]) for item in evidence_maps
        ),
        "unique_evidence_source_count": len(
            {
                binding["source_id"]
                for item in evidence_maps
                for binding in item["source_bindings"]
            }
        ),
        "candidate_status_counts": dict(
            sorted(Counter(item["status"] for item in candidates).items())
        ),
        "coverage_assessment_counts": dict(
            sorted(Counter(item["coverage_assessment"] for item in candidates).items())
        ),
        "member_action_counts": dict(
            sorted(
                Counter(item["official_member_action"] for item in candidates).items()
            )
        ),
        "position_effect_counts": dict(
            sorted(
                Counter(
                    item["proposed_member_position_effect"] for item in candidates
                ).items()
            )
        ),
    }
    subject = {
        source_readiness_merge_base_field: post_merge_base,
        "upstream_bindings": deepcopy(upstream_bindings),
        "member_id": readiness_artifact["subject"]["member_id"],
        "legislator_id": readiness_artifact["subject"]["legislator_id"],
        "issue_id": readiness_artifact["subject"]["issue_id"],
        "congress": readiness_artifact["subject"]["congress"],
        "official_cutoff": readiness_artifact["subject"]["official_cutoff"],
        "action_ids": list(readiness_artifact["subject"]["action_ids"]),
        "accounting": accounting,
        "evidence_maps": evidence_maps,
        "candidates": candidates,
        "aggregate": aggregate,
        "blocked_action_ids": [
            item["action_id"]
            for item in accounting
            if item["disposition"] == BLOCKED_DISPOSITION
        ],
        "review_state": "candidate_package_pending_human_action_meaning_review",
        "downstream_authorizations": {
            "action_meaning_acceptance": False,
            "policy_episode_construction": False,
            "policy_episode_acceptance": False,
            "semantic_ir": False,
            "synthesis": False,
            "public_wording": False,
            "publication": False,
            "production_persistence": False,
            "deployment": False,
        },
    }
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "criteria_version": CRITERIA_VERSION,
        "artifact_id": artifact_id,
        "artifact_role": "detached_non_authorizing_human_review_candidate_package",
        "accepted": False,
        "canonical": False,
        "non_public": True,
        "production_selectable": False,
        "subject": subject,
        "interpretation_subject_sha256": sha256_json(subject),
    }
    validate_candidate_artifact(
        artifact,
        readiness_artifact=readiness_artifact,
        repository_root=repository_root,
    )
    return artifact


def validate_candidate_artifact(
    artifact: dict[str, Any],
    *,
    readiness_artifact: dict[str, Any],
    repository_root: Path,
) -> None:
    _require(artifact.get("schema_version") == SCHEMA_VERSION, "schema version")
    _require(artifact.get("accepted") is False, "candidate package accepted")
    _require(artifact.get("canonical") is False, "candidate package canonical")
    _require(artifact.get("non_public") is True, "candidate package public")
    _require(
        artifact.get("production_selectable") is False,
        "candidate package production selectable",
    )
    subject = artifact["subject"]
    _require(
        sha256_json(subject) == artifact["interpretation_subject_sha256"],
        "interpretation subject digest mismatch",
    )

    records = readiness_artifact["subject"]["action_readiness"]
    record_by_id = {item["action_id"]: item for item in records}
    universe = set(readiness_artifact["subject"]["action_ids"])
    ready = {
        item["action_id"] for item in records if item["readiness_state"] == READY_STATE
    }
    blocked = universe - ready
    candidates = subject["candidates"]
    evidence_maps = subject["evidence_maps"]
    accounting = subject["accounting"]

    _require(set(subject["action_ids"]) == universe, "universe action set mismatch")
    _require(len(subject["action_ids"]) == len(universe), "duplicate universe action")
    _require(len(accounting) == len(universe), "accounting count mismatch")
    _require(
        {item["action_id"] for item in accounting} == universe,
        "accounting action set mismatch",
    )
    _require(
        len({item["action_id"] for item in accounting}) == len(accounting),
        "duplicate accounting action",
    )
    _require(
        {item["action_id"] for item in candidates} == ready,
        "candidate action set is not exact ready set",
    )
    _require(len(candidates) == len(ready), "duplicate candidate action")
    _require(
        {item["action_id"] for item in evidence_maps} == ready,
        "evidence-map action set mismatch",
    )
    _require(
        set(subject["blocked_action_ids"]) == blocked,
        "blocked action set mismatch",
    )

    evidence_by_id = {item["evidence_map_id"]: item for item in evidence_maps}
    for candidate in candidates:
        action_id = candidate["action_id"]
        record = record_by_id[action_id]
        _require(record["readiness_state"] == READY_STATE, "blocked candidate")
        _require(
            candidate["exact_action_identity"] == record["exact_action_identity"]
            and candidate["house_action_stage"] == record["house_action_stage"]
            and candidate["official_member_action"] == record["official_member_action"],
            f"candidate identity/action mismatch: {action_id}",
        )
        candidate_subject = {
            key: value
            for key, value in candidate.items()
            if key != "candidate_content_subject_sha256"
        }
        _require(
            sha256_json(candidate_subject)
            == candidate["candidate_content_subject_sha256"],
            f"candidate digest mismatch: {action_id}",
        )
        _require(
            candidate["coverage_assessment"] in ALLOWED_COVERAGE_ASSESSMENTS,
            f"coverage assessment: {action_id}",
        )
        _require(
            candidate["proposed_member_position_effect"]
            == _position_effect(record["official_member_action"]),
            f"member-position effect mismatch: {action_id}",
        )
        _require(
            candidate["proposed_member_position_effect"] in ALLOWED_POSITION_EFFECTS,
            f"position effect invalid: {action_id}",
        )
        if candidate["coverage_assessment"] == "package_level_bounded_summary":
            _require(
                any(
                    "whole-package choice" in limitation
                    for limitation in candidate["limitations"]
                )
                and bool(candidate["unresolved_editorial_questions"]),
                f"package-level boundary missing: {action_id}",
            )
        meaning = candidate["proposed_exact_action_meaning"].casefold()
        leaked = [term for term in FORBIDDEN_MEANING_TERMS if term in meaning]
        _require(not leaked, f"forbidden semantic input in meaning: {action_id}")
        if candidate["coverage_assessment"] == "package_level_bounded_summary":
            _require(
                not re.search(
                    r"\b(?:the )?member (?:supported|opposed|endorsed|rejected)\b",
                    meaning,
                ),
                f"component-level member attribution prohibited: {action_id}",
            )
        operative_ids = record["source_roles"]["operative_content_interpretation_input"]
        meaning_components = [
            component
            for component in candidate["claim_components"]
            if component["component_id"] == f"{action_id}:meaning"
        ]
        _require(
            len(operative_ids) == 1
            and len(meaning_components) == 1
            and meaning_components[0]["source_id"] == operative_ids[0]
            and meaning_components[0]["wording"]
            == candidate["proposed_exact_action_meaning"]
            and meaning_components[0]["locator"]
            == candidate["official_title_or_purpose"]["locator"],
            f"meaning claim uses non-exact source or locator: {action_id}",
        )
        if record["mechanism_class"] != "amendment":
            operative_id = operative_ids[0]
            operative = next(
                source
                for source in record["sources"]
                if source["source_id"] == operative_id
            )
            operative_path = _governed_path(
                operative["raw_provenance"]["governed_local_path"],
                repository_root=repository_root,
            )
            xml_summary = _xml_summary(operative_path)
            official = candidate["official_title_or_purpose"]
            structural_claims = [
                component
                for component in candidate["claim_components"]
                if component["locator"] in STRUCTURAL_CLAIM_LOCATORS
            ]
            _require(
                official["wording"] == xml_summary["official_title"]
                and official["source_id"] == operative_id,
                f"operative title/source mismatch: {action_id}",
            )
            if xml_summary["descriptive_official_title"]:
                _require(
                    official["locator"] == "official-title" and not structural_claims,
                    f"descriptive title handling mismatch: {action_id}",
                )
            else:
                structure = xml_summary["top_level_structure"]
                _require(
                    structure is not None,
                    f"short-title-only meaning lacks safe structure: {action_id}",
                )
                expected_claims = _structural_claim_components(
                    action_id=action_id,
                    source_id=operative_id,
                    structure=structure,
                )
                _require(
                    official["locator"] == "structured_operative_summary"
                    and candidate["confidence"] != "high"
                    and candidate["coverage_assessment"]
                    == "package_level_bounded_summary",
                    f"short-title-only meaning treated as complete: {action_id}",
                )
                _require(
                    structural_claims == expected_claims,
                    f"structured operative components mismatch: {action_id}",
                )
                _require(
                    all(
                        component["wording"].casefold() in meaning
                        for component in expected_claims
                    ),
                    f"structured operative component absent from meaning: {action_id}",
                )
                _require(
                    not re.search(
                        r"\b(?:the )?member (?:supported|opposed|endorsed|rejected)\b",
                        meaning,
                    ),
                    f"component-level member attribution prohibited: {action_id}",
                )
        evidence_map = evidence_by_id[candidate["evidence_map_id"]]
        evidence_subject = {
            key: value
            for key, value in evidence_map.items()
            if key not in {"evidence_map_id", "evidence_map_subject_sha256"}
        }
        _require(
            sha256_json(evidence_subject)
            == evidence_map["evidence_map_subject_sha256"],
            f"evidence-map digest mismatch: {action_id}",
        )
        _require(
            evidence_map["source_packet_sha256"] == record["source_packet_sha256"],
            f"source packet mismatch: {action_id}",
        )
        source_ids = {item["source_id"] for item in evidence_map["source_bindings"]}
        _require(
            set(candidate["source_references"])
            == {
                source_id
                for values in record["source_roles"].values()
                for source_id in values
            },
            f"candidate source references mismatch: {action_id}",
        )
        for component in candidate["claim_components"]:
            _require(
                component["source_id"] in source_ids,
                f"claim component source missing: {action_id}",
            )
        if record["mechanism_class"] == "amendment":
            operative = set(
                record["source_roles"]["operative_content_interpretation_input"]
            )
            _require(
                {item["source_id"] for item in candidate["claim_components"]}
                <= operative,
                f"amendment meaning used non-exact source: {action_id}",
            )

        for binding in evidence_map["source_bindings"]:
            path = _governed_path(
                binding["raw_provenance"]["governed_local_path"],
                repository_root=repository_root,
            )
            _require(
                sha256_file(path) == binding["raw_provenance"]["sha256"],
                f"raw source digest mismatch: {action_id}",
            )

    for item in accounting:
        record = record_by_id[item["action_id"]]
        if record["readiness_state"] == READY_STATE:
            _require(
                item["disposition"] == "candidate_interpretation_proposed"
                and item["candidate_id"] is not None,
                f"ready action accounting mismatch: {item['action_id']}",
            )
        else:
            _require(
                item["disposition"] == BLOCKED_DISPOSITION
                and item["candidate_id"] is None
                and item["candidate_content_subject_sha256"] is None,
                f"blocked action interpreted: {item['action_id']}",
            )

    aggregate = subject["aggregate"]
    _require(
        aggregate["approved_universe_count"] == len(universe)
        and aggregate["interpretation_eligible_count"] == len(ready)
        and aggregate["candidate_count"] == len(candidates)
        and aggregate["source_blocked_count"] == len(blocked)
        and aggregate["evidence_source_binding_count"]
        == sum(len(item["source_bindings"]) for item in evidence_maps)
        and aggregate["unique_evidence_source_count"]
        == len(
            {
                binding["source_id"]
                for item in evidence_maps
                for binding in item["source_bindings"]
            }
        ),
        "aggregate accounting mismatch",
    )
    _require(
        all(value is False for value in subject["downstream_authorizations"].values()),
        "downstream authority became true",
    )
