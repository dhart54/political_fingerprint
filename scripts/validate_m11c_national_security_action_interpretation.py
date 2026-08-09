from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation import (  # noqa: E402
    ActionInterpretationError,
    BLOCKED_DISPOSITION,
    FORBIDDEN_MEANING_TERMS,
    validate_candidate_artifact,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
    load_json,
    sha256_file,
    sha256_json,
)
from backend.scripts.build_m11c_national_security_action_interpretation import (  # noqa: E402
    ARTIFACT_ID,
    ARTIFACT_PATH,
    DECISION_SCHEMA_PATH,
    DECISION_PATH,
    DOSSIER_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11B_MERGE_BASE,
    READINESS_PATH,
    SCHEMA_PATH,
    UPSTREAM_BINDINGS,
    build_outputs,
)
from scripts.validate_m11a_universe_authority import (  # noqa: E402
    validate_repository as validate_m11a,
)
from scripts.validate_m11b_national_security_source_readiness import (  # noqa: E402
    validate_repository as validate_m11b,
)


EXPECTED_ARTIFACT_SHA256 = (
    "acfd656ccce57e8ef0668bcedeb5c51b0ea6342097310db13236ffc5d16bf86c"
)
EXPECTED_READINESS_SUBJECT_SHA256 = (
    "53af365c4b06d4cc96fdeba17a1d65c80d89ae960d8cf986b7a5bf9599ec51bd"
)
EXPECTED_UNIVERSE_SUBJECT_SHA256 = (
    "b1e1a4588a4fcef6beb9dfd836ff5c2f32d8fdb340359f11453c6a0c947a17a5"
)
EXPECTED_SELECTION_SHA256 = (
    "a018b597705132f0e891c575af1dac4b880c31b0d98469f2f47001982dce0b81"
)
EXPECTED_ACTION_SET_SHA256 = (
    "190bda45c25cd32ae0a6847c862f85837eafc4a82dfda237746a66467c550400"
)
REVIEWED_OTHER_79_MEANINGS_SHA256 = (
    "688fb9533641267a095507a8ed9cab82fbe8c8b328c96491b4b05f4229476521"
)
REVIEWED_81_POSITION_EFFECTS_SHA256 = (
    "4d2d949bac2332caf109cff7de5bb980b855b68114df7c7f9ab9a8f5f6ce2095"
)
REVIEWED_EIGHT_PACKAGE_MEANINGS_SHA256 = (
    "1136d579295c18c37dcfb6ca17c4c86c42dbeeb1e6bebeaa5210d78f1c6a422c"
)
REVISED_ACTION_IDS = {"house:119:1:320", "house:119:2:142"}
STRUCTURAL_LOCATORS = {
    "top-level-division-header",
    "top-level-title-header",
    "direct-section-header",
}
CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ActionInterpretationError(message)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _raw_path(source: dict[str, Any]) -> Path:
    relative = Path(source["raw_provenance"]["governed_local_path"])
    _require(not relative.is_absolute() and ".." not in relative.parts, "unsafe path")
    path = (ROOT / relative).resolve()
    governed = (
        ROOT / "docs/editorial/full_record_reviews/source_readiness/evidence"
    ).resolve()
    _require(governed in path.parents, "source outside governed evidence")
    _require(path.is_file(), f"source missing: {relative.as_posix()}")
    _require(
        sha256_file(path) == source["raw_provenance"]["sha256"],
        f"source digest mismatch: {source['source_id']}",
    )
    return path


def _normalized_text(element: ElementTree.Element) -> str:
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def _direct_header(element: ElementTree.Element) -> str | None:
    for child in element:
        if _local_name(child.tag) == "header":
            wording = _normalized_text(child)
            return wording or None
    return None


def _xml_evidence(path: Path) -> dict[str, Any]:
    root = ElementTree.parse(path).getroot()
    official_titles: list[str] = []
    short_titles: list[str] = []
    for element in root.iter():
        name = _local_name(element.tag)
        if name not in {"official-title", "short-title"}:
            continue
        wording = _normalized_text(element)
        if not wording:
            continue
        if name == "official-title":
            if wording not in official_titles:
                official_titles.append(wording)
        elif wording not in short_titles:
            short_titles.append(wording)
    title = next(iter(official_titles), None) or next(iter(short_titles), None)
    _require(title is not None, f"operative XML title missing: {path}")

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

    divisions: list[tuple[str, str]] = []
    for element in root.iter():
        if _local_name(element.tag) != "division":
            continue
        ancestor_names = ancestors(element)
        if {"quoted-block", "toc", "table"}.intersection(
            ancestor_names
        ) or "division" in ancestor_names:
            continue
        header = _direct_header(element)
        if header:
            divisions.append(("top-level-division-header", header))

    structural_components: list[tuple[str, str]] = []
    if len(divisions) >= 2:
        structural_components = divisions
    else:
        titles: list[tuple[str, str]] = []
        for element in root.iter():
            if _local_name(element.tag) != "title":
                continue
            ancestor_names = ancestors(element)
            if (
                {"quoted-block", "toc", "table"}.intersection(ancestor_names)
                or "division" in ancestor_names
                or "title" in ancestor_names
            ):
                continue
            header = _direct_header(element)
            if not header:
                continue
            title_components = [("top-level-title-header", header)]
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
                title_components.append(("direct-section-header", section_header))
            titles.extend(title_components)
        title_header_count = sum(
            locator == "top-level-title-header" for locator, _ in titles
        )
        section_header_count = sum(
            locator == "direct-section-header" for locator, _ in titles
        )
        if title_header_count >= 2 or (
            title_header_count == 1 and section_header_count >= 2
        ):
            structural_components = titles

    return {
        "title": title,
        "descriptive_official_title": bool(official_titles)
        and title.startswith(("To ", "Making ", "Directing ")),
        "structural_components": structural_components,
    }


def _validate_official_meanings(
    artifact: dict[str, Any], readiness: dict[str, Any]
) -> None:
    records = {
        record["action_id"]: record
        for record in readiness["subject"]["action_readiness"]
    }
    for candidate in artifact["subject"]["candidates"]:
        action_id = candidate["action_id"]
        record = records[action_id]
        operative_id = record["source_roles"]["operative_content_interpretation_input"][
            0
        ]
        operative = next(
            source
            for source in record["sources"]
            if source["source_id"] == operative_id
        )
        official = candidate["official_title_or_purpose"]
        _require(
            official["source_id"] == operative_id,
            f"candidate official source mismatch: {action_id}",
        )
        if record["mechanism_class"] == "amendment":
            projection = operative["neutral_projection"]
            expected = projection.get("official_purpose") or projection.get(
                "official_description"
            )
            expected = re.sub(r"\s+", " ", str(expected)).strip()
            _require(
                official["wording"] == expected
                and official["locator"] == "official_purpose_or_description",
                f"exact amendment meaning source mismatch: {action_id}",
            )
        else:
            xml_evidence = _xml_evidence(_raw_path(operative))
            _require(
                official["wording"] == xml_evidence["title"],
                f"operative text title mismatch: {action_id}",
            )
            if xml_evidence["descriptive_official_title"]:
                _require(
                    official["locator"] == "official-title"
                    and not any(
                        component["locator"] in STRUCTURAL_LOCATORS
                        for component in candidate["claim_components"]
                    ),
                    f"descriptive official-title handling mismatch: {action_id}",
                )
            else:
                expected_components = xml_evidence["structural_components"]
                actual_components = [
                    (component["locator"], component["wording"])
                    for component in candidate["claim_components"]
                    if component["locator"] in STRUCTURAL_LOCATORS
                ]
                _require(
                    bool(expected_components),
                    f"short/proper title lacks safe operative structure: {action_id}",
                )
                _require(
                    official["locator"] == "structured_operative_summary"
                    and candidate["confidence"] != "high"
                    and candidate["coverage_assessment"]
                    == "package_level_bounded_summary",
                    f"short/proper title treated as complete meaning: {action_id}",
                )
                _require(
                    actual_components == expected_components,
                    f"structured component/source mismatch: {action_id}",
                )
                meaning_casefold = candidate["proposed_exact_action_meaning"].casefold()
                _require(
                    all(
                        wording.casefold() in meaning_casefold
                        for _, wording in expected_components
                    ),
                    f"fabricated or omitted structured component: {action_id}",
                )
                _require(
                    not re.search(
                        r"\b(?:the )?member (?:supported|opposed|endorsed|rejected)\b",
                        meaning_casefold,
                    ),
                    f"component-level position attribution: {action_id}",
                )
        meaning = candidate["proposed_exact_action_meaning"]
        _require(
            candidate["exact_action_identity"].split(":")[-1] in meaning,
            f"exact identity absent from meaning: {action_id}",
        )
        _require(
            not any(term in meaning.casefold() for term in FORBIDDEN_MEANING_TERMS),
            f"forbidden political input leaked: {action_id}",
        )
        if candidate["coverage_assessment"] == "package_level_bounded_summary":
            _require(
                any("whole-package choice" in item for item in candidate["limitations"])
                and candidate["unresolved_editorial_questions"],
                f"package boundary missing: {action_id}",
            )


def _validate_decision_template(artifact: dict[str, Any]) -> None:
    template = load_json(DECISION_PATH)
    schema = load_json(DECISION_SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    _require(
        not list(Draft7Validator(schema).iter_errors(template)),
        "decision template schema mismatch",
    )
    subject = template["subject"]
    _require(template["empty_non_authorizing_template"] is True, "decision template")
    _require(
        sha256_json(subject) == template["decision_template_subject_sha256"],
        "decision template digest mismatch",
    )
    _require(
        subject["candidate_artifact_id"] == artifact["artifact_id"]
        and subject["candidate_interpretation_subject_sha256"]
        == artifact["interpretation_subject_sha256"],
        "decision template candidate binding mismatch",
    )
    candidates = {
        candidate["action_id"]: candidate
        for candidate in artifact["subject"]["candidates"]
    }
    _require(len(subject["decisions"]) == 81, "decision count mismatch")
    _require(
        {item["action_id"] for item in subject["decisions"]} == set(candidates),
        "decision action set mismatch",
    )
    for decision in subject["decisions"]:
        candidate = candidates[decision["action_id"]]
        _require(
            decision["candidate_id"] == candidate["candidate_id"]
            and decision["candidate_content_subject_sha256"]
            == candidate["candidate_content_subject_sha256"],
            f"decision candidate binding mismatch: {decision['action_id']}",
        )
        _require(
            all(
                decision[field] is None
                for field in (
                    "decision",
                    "reviewer_id",
                    "reviewer_authority",
                    "rationale",
                    "decision_timestamp",
                )
            ),
            f"decision template self-authorized: {decision['action_id']}",
        )


def _validate_parity(artifact: dict[str, Any]) -> None:
    parity = load_json(PARITY_PATH)
    schema = load_json(PARITY_SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    _require(
        not list(Draft7Validator(schema).iter_errors(parity)),
        "parity schema mismatch",
    )
    subject = parity["subject"]
    _require(
        sha256_json(subject) == parity["parity_subject_sha256"],
        "parity subject digest mismatch",
    )
    _require(
        subject["candidate_artifact_id"] == artifact["artifact_id"]
        and subject["candidate_interpretation_subject_sha256"]
        == artifact["interpretation_subject_sha256"],
        "parity candidate binding mismatch",
    )
    expected_paths = {ARTIFACT_PATH, DECISION_PATH, DOSSIER_PATH}
    actual_paths: set[Path] = set()
    for entry in subject["files"]:
        path = (ROOT / entry["path"]).resolve()
        _require(ROOT in path.parents, "parity path outside repository")
        _require(path in expected_paths, "unexpected parity path")
        _require(path.is_file(), f"parity file missing: {entry['path']}")
        _require(
            canonical_file_sha256(path) == entry["sha256"],
            f"parity file digest mismatch: {entry['path']}",
        )
        actual_paths.add(path)
    _require(actual_paths == expected_paths, "parity path set mismatch")


def validate_repository() -> dict[str, Any]:
    m11a = validate_m11a()
    m11b = validate_m11b()
    readiness = load_json(READINESS_PATH)
    artifact = load_json(ARTIFACT_PATH)
    schema = load_json(SCHEMA_PATH)

    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda item: list(item.absolute_path),
    )
    _require(
        not errors,
        "schema validation failed: " + "; ".join(error.message for error in errors[:5]),
    )
    validate_candidate_artifact(
        artifact,
        readiness_artifact=readiness,
        repository_root=ROOT,
    )

    _require(artifact["artifact_id"] == ARTIFACT_ID, "artifact identity mismatch")
    subject = artifact["subject"]
    _require(
        subject["post_m11b_merge_base"] == POST_M11B_MERGE_BASE,
        "post-M11B base mismatch",
    )
    _require(
        subject["upstream_bindings"] == UPSTREAM_BINDINGS,
        "upstream binding mismatch",
    )
    _require(
        canonical_file_sha256(READINESS_PATH) == EXPECTED_ARTIFACT_SHA256,
        "accepted M11B artifact changed",
    )
    _require(
        readiness["source_readiness_subject_sha256"]
        == EXPECTED_READINESS_SUBJECT_SHA256,
        "accepted M11B subject changed",
    )
    _require(
        subject["upstream_bindings"]["m11a"]["selection_sha256"]
        == EXPECTED_SELECTION_SHA256
        and subject["upstream_bindings"]["m11a"]["universe_subject_sha256"]
        == EXPECTED_UNIVERSE_SUBJECT_SHA256
        and subject["upstream_bindings"]["m11a"]["action_set_sha256"]
        == EXPECTED_ACTION_SET_SHA256,
        "accepted M11A binding changed",
    )
    _require(
        m11a["approved_action_count"] == 82
        and m11b["ready_count"] == 81
        and m11b["blocked_count"] == 1,
        "upstream validator accounting mismatch",
    )

    _validate_official_meanings(artifact, readiness)
    candidates_by_id = {
        candidate["action_id"]: candidate for candidate in subject["candidates"]
    }
    _require(
        sha256_json(
            {
                action_id: candidate["proposed_exact_action_meaning"]
                for action_id, candidate in candidates_by_id.items()
                if action_id not in REVISED_ACTION_IDS
            }
        )
        == REVIEWED_OTHER_79_MEANINGS_SHA256,
        "one or more of the other 79 reviewed meanings changed",
    )
    _require(
        sha256_json(
            {
                action_id: candidate["proposed_member_position_effect"]
                for action_id, candidate in candidates_by_id.items()
            }
        )
        == REVIEWED_81_POSITION_EFFECTS_SHA256,
        "one or more of the 81 accepted position effects changed",
    )
    _require(
        sha256_json(
            {
                action_id: candidate["proposed_exact_action_meaning"]
                for action_id, candidate in candidates_by_id.items()
                if action_id not in REVISED_ACTION_IDS
                and candidate["coverage_assessment"] == "package_level_bounded_summary"
            }
        )
        == REVIEWED_EIGHT_PACKAGE_MEANINGS_SHA256,
        "one or more of the eight accepted package meanings changed",
    )
    s1071_meaning = candidates_by_id["house:119:1:320"]["proposed_exact_action_meaning"]
    s1318_meaning = candidates_by_id["house:119:2:142"]["proposed_exact_action_meaning"]
    _require(
        "top-level divisions" in s1071_meaning
        and "Department of Defense Authorizations" in s1071_meaning
        and "Military Construction Authorizations" in s1071_meaning
        and "Department of Energy National Security Authorizations" in s1071_meaning
        and "Intelligence Authorization Act" in s1071_meaning
        and "Coast Guard Authorization Act" in s1071_meaning,
        "S. 1071 governed structured-package regression",
    )
    _require(
        "Foreign Intelligence Accountability Act" in s1318_meaning
        and "Civil liberties review of FBI queries" in s1318_meaning
        and "Extension of authorities of title VII" in s1318_meaning
        and "Anti-CBDC Surveillance State Act" in s1318_meaning
        and "central bank digital currency" in s1318_meaning,
        "S. 1318 governed compound-package regression",
    )
    _validate_decision_template(artifact)
    _validate_parity(artifact)

    rebuilt = build_outputs()
    for path, content in rebuilt.items():
        _require(
            path.is_file() and path.read_bytes().replace(b"\r\n", b"\n") == content,
            f"deterministic regeneration mismatch: {path.relative_to(ROOT)}",
        )

    _require(
        subject["blocked_action_ids"] == ["house:119:2:278"],
        "blocked action identity mismatch",
    )
    blocked_accounting = [
        item
        for item in subject["accounting"]
        if item["disposition"] == BLOCKED_DISPOSITION
    ]
    _require(
        len(blocked_accounting) == 1
        and blocked_accounting[0]["action_id"] == "house:119:2:278",
        "blocked accounting mismatch",
    )
    _require(
        "house:119:2:278"
        not in {candidate["action_id"] for candidate in subject["candidates"]},
        "H.R. 8800 was interpreted",
    )
    _require(
        all(value is False for value in subject["downstream_authorizations"].values()),
        "later-stage authority became true",
    )

    current = load_json(CURRENT_STATE_PATH)
    m11b_state = current["active_source_readiness_milestone"]
    m11c_state = current["active_action_interpretation_milestone"]
    _require(
        m11b_state["milestone_state"] == "completed_human_accepted"
        and m11b_state["accepted_head"] == "fcc988b867a49086d7545832f9575130aef0f8ea"
        and m11b_state["post_merge_main"] == POST_M11B_MERGE_BASE,
        "current-state M11B acceptance mismatch",
    )
    _require(
        m11c_state["post_m11b_merge_base"] == POST_M11B_MERGE_BASE
        and m11c_state["approved_universe_count"] == 82
        and m11c_state["interpretation_eligible_count"] == 81
        and m11c_state["candidate_count"] == 81
        and m11c_state["source_blocked_action_ids"] == ["house:119:2:278"]
        and m11c_state["reviewed_head"] == "1a5d60cea6e8712d2bc1e20019ac37505adf39ff"
        and m11c_state["human_review_result"] == "bounded_correction_required"
        and m11c_state["reviewed_meaning_acceptance_count"] == 79
        and m11c_state["reviewed_position_effect_acceptance_count"] == 81
        and set(m11c_state["meaning_corrections_pending_final_review"])
        == REVISED_ACTION_IDS
        and m11c_state["candidate_status_counts"]
        == {"proposed": 11, "proposed_with_material_limitation": 70}
        and m11c_state["coverage_assessment_counts"]
        == {
            "bounded_official_purpose_summary": 71,
            "package_level_bounded_summary": 10,
        }
        and m11c_state["candidate_identity"]
        == {
            "id": artifact["artifact_id"],
            "sha256": canonical_file_sha256(ARTIFACT_PATH),
            "interpretation_subject_sha256": artifact["interpretation_subject_sha256"],
            "accepted": False,
            "authorizing": False,
        }
        and m11c_state["action_meaning_state"]
        == "not_accepted_candidates_pending_human_review"
        and all(
            value is False for value in m11c_state["downstream_authorizations"].values()
        ),
        "current-state M11C boundary mismatch",
    )

    return {
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": canonical_file_sha256(ARTIFACT_PATH),
        "interpretation_subject_sha256": artifact["interpretation_subject_sha256"],
        "approved_universe_count": 82,
        "candidate_count": 81,
        "blocked_count": 1,
        "blocked_action_ids": ["house:119:2:278"],
        "package_level_candidate_count": sum(
            candidate["coverage_assessment"] == "package_level_bounded_summary"
            for candidate in subject["candidates"]
        ),
        "preserved_other_meaning_count": 79,
        "preserved_position_effect_count": 81,
        "corrected_action_ids": sorted(REVISED_ACTION_IDS),
        "downstream_authorizations": subject["downstream_authorizations"],
        "m11a": m11a,
        "m11b": m11b,
    }


def main() -> int:
    print(json.dumps(validate_repository(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
