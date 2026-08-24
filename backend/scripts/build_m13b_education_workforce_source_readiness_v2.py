from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    build_readiness_artifact,
    canonical_file_sha256,
    load_json,
    sha256_file,
    sha256_json,
    validate_artifact,
)


POST_M13B_MAIN = "e49d416b3549d87763e375079f742f7013c1c988"
V1_ID = "interpretation-source-readiness:f000477:education_workforce:119:v1"
V1_FILE_SHA256 = "70157fa2f9d55683837d5a7e3ff92249cbf74d89def7a759e5eef4459474b198"
V1_SUBJECT_SHA256 = "7f526f1ce37d9f2ec1acd5e092d04e091b8ad5340c56aff57d478f69e45533c7"
V1_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_education_workforce_119_interpretation_source_readiness_v1.json"
)
V2_ID = "interpretation-source-readiness:f000477:education_workforce:119:v2"
V2_ROOT = ROOT / "docs/editorial/full_record_reviews/source_readiness"
V2_PATH = (
    V2_ROOT / "f000477_education_workforce_119_interpretation_source_readiness_v2.json"
)
V2_REPORT_PATH = (
    V2_ROOT / "f000477_education_workforce_119_interpretation_source_readiness_v2.md"
)
RECEIPT_PATH = V2_ROOT / (
    "corrections/f000477_education_workforce_119_m13b_v1_supersession_v2.json"
)
SCHEMA_PATH = ROOT / (
    "docs/methodology/full_record_interpretation_source_readiness_v1.schema.json"
)

ACTION_ID = "house:119:2:19"
OLD_SOURCE_ID = "congressional-record:2026-01-13:house:H677-H693:hr2262"
OLD_SOURCE_SHA256 = "a5c9f2fc9c16096d99f4939f691b8a509c9bdc62e58204eb853178f612161409"
NEW_SOURCE_ID = "congressional-record:2026-01-13:house-section:H663-H719:hr2262"
NEW_SOURCE_URL = (
    "https://www.govinfo.gov/content/pkg/CREC-2026-01-13/pdf/CREC-2026-01-13-house.pdf"
)
NEW_SOURCE_SHA256 = "d0dc2a327330c1e0137f8a593d82e107a75222ddebc8a9bfcbb5a62532afa80b"
NEW_SOURCE_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/evidence/"
    f"f000477_education_119_v2/{NEW_SOURCE_SHA256}.pdf"
)
DOCUMENT_IDENTITY = "official_house_section_H663-H719_relevant_H677-H681_H692-H693"
M13A_ACTION_SET_SHA256 = (
    "83b7b129eaa32d114c72782c70cb06dac55f7cd01c8681c8dc2ae2dca986cf5b"
)
M13A_UNIVERSE_SUBJECT_SHA256 = (
    "edc381362beb1e5700748ffe75fc12c31ae14f090887940197a50bf416aaac6d"
)


CONTENT_VERIFICATION = {
    "schema_version": "operative_floor_text_content_verification_v1",
    "extraction_engine": "pypdf",
    "document_identity": DOCUMENT_IDENTITY,
    "document_page_count": 57,
    "document_page_labels": {"first": "H663", "last": "H719"},
    "relevant_record_ranges": ["H677-H681", "H692-H693"],
    "page_checks": [
        {
            "pdf_page_number": 1,
            "record_page_label": "H663",
            "evidence_role": "document_boundary_start",
            "required_anchors": ["CONGRESSIONAL RECORD"],
        },
        {
            "pdf_page_number": 15,
            "record_page_label": "H677",
            "evidence_role": "exact_stage_adoption_and_operative_text_start",
            "required_anchors": [
                "H.R. 2262",
                "Pursuant to House Resolution 988",
                "the amendment in the nature of a substitute recommended by the Committee on Education and Workforce",
                "modified by the amendment printed in part B of House Report 119–440",
                "is adopted and the bill, as amended, is considered read",
                "The text of the bill, as amended, is as follows",
                "SEC. 2. TREATMENT OF ATTENDANCE OR PARTICIPATION IN CERTAIN ACTIVITIES",
            ],
        },
        {
            "pdf_page_number": 16,
            "record_page_label": "H678",
            "evidence_role": "operative_text_completion",
            "required_anchors": [
                "outside of the employee's regular working hours",
                "such attendance or participation is voluntary",
                "the employee does not perform any work for the employer",
                "bona fide apprenticeship program",
                "hours worked on or after the date of enactment of this Act",
            ],
        },
        {
            "pdf_page_number": 30,
            "record_page_label": "H692",
            "evidence_role": "final_passage_resumption",
            "required_anchors": [
                "Proceedings will resume on questions previously postponed",
                "Passage of H.R. 2262, if ordered",
                "the unfinished business is the vote on the motion to recommit on the bill (H.R. 2262)",
                "[Roll No. 18]",
            ],
        },
        {
            "pdf_page_number": 31,
            "record_page_label": "H693",
            "evidence_role": "roll19_final_passage_disposition",
            "required_anchors": [
                "The question is on the passage of the bill",
                "[Roll No. 19]",
                "yeas 209, nays 215, not voting 7",
                "So the bill was not passed",
            ],
        },
        {
            "pdf_page_number": 57,
            "record_page_label": "H719",
            "evidence_role": "document_boundary_end",
            "required_anchors": ["CONGRESSIONAL RECORD — HOUSE"],
        },
    ],
}


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def _bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value.replace(b"\r\n", b"\n")).hexdigest()


def _validate_schema(artifact: dict[str, Any]) -> None:
    schema = load_json(SCHEMA_PATH)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValueError(f"M13B v2 schema failed: {errors[0].message}")


def _source() -> dict[str, Any]:
    projection = {
        "schema_version": "neutral_interpretation_source_projection_v1",
        "action_id": ACTION_ID,
        "source_id": NEW_SOURCE_ID,
        "congress": 119,
        "chamber": "house",
        "exact_action_identity": "119:hr:2262",
        "house_action_stage": "final_passage_or_suspension_passage",
        "action_date": "2026-01-13",
        "roll_number": 19,
        "member_action": "nay",
        "official_action_description": (
            "Official GovInfo House-section record contains the modified committee "
            "substitute considered for H.R. 2262 at H677-H678, surrounding floor "
            "consideration at H678-H681, and delayed roll 19 at H692-H693."
        ),
        "official_purpose": None,
        "official_description": None,
        "text_version": DOCUMENT_IDENTITY,
        "source_url": NEW_SOURCE_URL,
        "raw_provenance_sha256": NEW_SOURCE_SHA256,
    }
    return {
        "source_id": NEW_SOURCE_ID,
        "source_type": "congressional_record",
        "source_subject": "119:hr:2262",
        "content_class": "operative_floor_text",
        "source_url": NEW_SOURCE_URL,
        "raw_provenance": {
            "governed_local_path": NEW_SOURCE_PATH.relative_to(ROOT).as_posix(),
            "sha256": NEW_SOURCE_SHA256,
        },
        "content_verification": deepcopy(CONTENT_VERIFICATION),
        "neutral_projection": projection,
        "neutral_projection_sha256": sha256_json(projection),
    }


def build_artifact() -> tuple[dict[str, Any], dict[str, str]]:
    v1 = load_json(V1_PATH)
    if (
        v1["artifact_id"] != V1_ID
        or canonical_file_sha256(V1_PATH) != V1_FILE_SHA256
        or v1["source_readiness_subject_sha256"] != V1_SUBJECT_SHA256
    ):
        raise ValueError("historical M13B v1 identity changed")
    if sha256_file(NEW_SOURCE_PATH) != NEW_SOURCE_SHA256:
        raise ValueError("corrected official House-section PDF missing or changed")

    action_records = deepcopy(v1["subject"]["action_readiness"])
    v1_packet_sha256_by_action = {
        row["action_id"]: row["source_packet_sha256"] for row in action_records
    }
    for record in action_records:
        for key in (
            "readiness_criteria",
            "blocker_codes",
            "readiness_state",
            "source_packet_sha256",
        ):
            record.pop(key)
        if record["action_id"] != ACTION_ID:
            continue
        if record["source_roles"]["operative_content_interpretation_input"] != [
            OLD_SOURCE_ID
        ]:
            raise ValueError("historical roll-19 operative source identity changed")
        record["sources"] = [
            source
            for source in record["sources"]
            if source["source_id"] != OLD_SOURCE_ID
        ] + [_source()]
        record["sources"] = sorted(
            record["sources"], key=lambda source: source["source_id"]
        )
        for role in (
            "exact_action_identity_and_stage_evidence",
            "operative_content_interpretation_input",
        ):
            record["source_roles"][role] = [
                NEW_SOURCE_ID if source_id == OLD_SOURCE_ID else source_id
                for source_id in record["source_roles"][role]
            ]
        record["material_limitations"] = [
            "Congress.gov exposes no House-engrossed bill text for the failed passage. The complete official GovInfo House-section Congressional Record is the operative-content source because it records adoption of the modified committee substitute, prints the complete amended H.R. 2262 operative text on H677-H678, and links delayed roll 19 on H692-H693."
        ]

    v1_subject = v1["subject"]
    subject = {
        key: deepcopy(v1_subject[key])
        for key in (
            "member_name",
            "member_id",
            "legislator_id",
            "issue_id",
            "chamber",
            "congress",
            "official_cutoff",
            "action_ids",
            "action_set_sha256",
            "universe_subject_sha256",
        )
    }
    artifact = build_readiness_artifact(
        artifact_id=V2_ID,
        input_bindings=deepcopy(v1["input_bindings"]),
        subject=subject,
        action_records=action_records,
        repository_root=ROOT,
    )
    _validate_schema(artifact)
    validate_artifact(artifact, repository_root=ROOT)
    v2_packet_sha256_by_action = {
        row["action_id"]: row["source_packet_sha256"]
        for row in artifact["subject"]["action_readiness"]
    }
    unchanged = {
        action_id: digest
        for action_id, digest in v1_packet_sha256_by_action.items()
        if action_id != ACTION_ID and v2_packet_sha256_by_action[action_id] == digest
    }
    if len(unchanged) != 16:
        raise ValueError("one or more non-roll-19 source packets changed")
    return artifact, unchanged


def build_receipt(
    artifact: dict[str, Any], artifact_bytes: bytes, unchanged: dict[str, str]
) -> dict[str, Any]:
    subject = {
        "historical_m13b_v1": {
            "artifact_id": V1_ID,
            "artifact_path": V1_PATH.relative_to(ROOT).as_posix(),
            "artifact_sha256": V1_FILE_SHA256,
            "source_readiness_subject_sha256": V1_SUBJECT_SHA256,
            "m13b_v1_current_interpretation_readiness": (
                "superseded_due_to_incomplete_roll19_operational_source"
            ),
        },
        "defect": {
            "stop_reason": (
                "house:119:2:19_operational_congressional_record_source_incomplete"
            ),
            "defective_action_id": ACTION_ID,
            "defective_source_id": OLD_SOURCE_ID,
            "defective_raw_pdf_sha256": OLD_SOURCE_SHA256,
            "claimed_coverage": "H677-H693",
            "actual_coverage": "H676-H677",
            "discovery_stage": "m13c_fail_closed_source_inspection",
            "defect_class": "source_readiness_evidence_defect",
            "universe_membership_defect": False,
            "action_interpretation_judgment": False,
        },
        "corrected_operational_source": {
            "source_id": NEW_SOURCE_ID,
            "source_url": NEW_SOURCE_URL,
            "raw_pdf_sha256": NEW_SOURCE_SHA256,
            "document_coverage": "H663-H719",
            "relevant_record_ranges": ["H677-H681", "H692-H693"],
            "content_verification": deepcopy(CONTENT_VERIFICATION),
        },
        "corrected_m13b_v2": {
            "artifact_id": artifact["artifact_id"],
            "artifact_path": V2_PATH.relative_to(ROOT).as_posix(),
            "artifact_sha256": _bytes_sha256(artifact_bytes),
            "source_readiness_subject_sha256": artifact[
                "source_readiness_subject_sha256"
            ],
            "ready_count": artifact["subject"]["aggregate"]["ready_count"],
            "blocked_count": artifact["subject"]["aggregate"]["blocked_count"],
        },
        "unchanged_source_packet_parity": {
            "unchanged_action_count": len(unchanged),
            "excluded_corrected_action_id": ACTION_ID,
            "source_packet_sha256_by_action": dict(sorted(unchanged.items())),
        },
        "unchanged_m13a_authority": {
            "accepted_action_count": 17,
            "action_set_sha256": M13A_ACTION_SET_SHA256,
            "universe_subject_sha256": M13A_UNIVERSE_SUBJECT_SHA256,
        },
        "authority_effect": "source_readiness_correction_only",
        "action_interpretation_authorized": False,
    }
    return {
        "schema_version": "source_readiness_correction_receipt_v1",
        "receipt_id": (
            "source-readiness-correction:f000477:education_workforce:119:m13b-v1-to-v2"
        ),
        "immutable_correction_record": True,
        "subject": subject,
        "correction_subject_sha256": sha256_json(subject),
    }


def render_report(artifact: dict[str, Any], receipt: dict[str, Any]) -> str:
    aggregate = artifact["subject"]["aggregate"]
    return "\n".join(
        [
            "# M13B v2 Education & Workforce Roll-19 Source-Readiness Correction",
            "",
            "Status: detached non-authorizing correction candidate pending independent review.",
            "",
            f"- Exact post-M13B base: `{POST_M13B_MAIN}`",
            f"- Candidate: `{artifact['artifact_id']}`",
            f"- Source-readiness subject SHA-256: `{artifact['source_readiness_subject_sha256']}`",
            f"- Ready / blocked: `{aggregate['ready_count']} / {aggregate['blocked_count']}`",
            f"- Corrected source: `{NEW_SOURCE_ID}`",
            f"- Corrected raw SHA-256: `{NEW_SOURCE_SHA256}`",
            f"- Correction receipt: `{receipt['receipt_id']}`",
            "",
            "## Correction boundary",
            "",
            "Historical M13B v1 remains byte-identical but is superseded for current interpretation readiness because its roll-19 source claimed H677-H693 while the governed granule contains only H676-H677.",
            "",
            "M13B v2 replaces only the roll-19 operative-content binding with the complete official GovInfo House section. The other 16 source packets retain their exact v1 packet digests. M13A membership, action set, cutoff, and all downstream authorization flags remain unchanged.",
            "",
            "## Deterministic raw-PDF proof",
            "",
            "- Full document: H663-H719 / 57 physical PDF pages.",
            "- H677: H.R. 2262 exact-stage adoption of the committee substitute as modified by the Rules Committee amendment; amended bill considered read; operative text begins.",
            "- H678: section 2 reaches the outside-regular-hours, voluntary/no-adverse-action, no-work, apprenticeship, and effective-date completion.",
            "- H692: postponed H.R. 2262 proceedings resume and roll 18 motion-to-recommit linkage appears.",
            "- H693: passage question, roll 19, 209-215-7 disposition, and failed-passage result appear.",
            "",
            "## Authorization boundary",
            "",
            "This correction establishes source readiness only. It does not authorize action interpretation, episodes, Semantic IR, synthesis, public wording, publication, deployment, or production work.",
            "",
        ]
    )


def build_outputs() -> dict[Path, bytes]:
    artifact, unchanged = build_artifact()
    artifact_bytes = _json_bytes(artifact)
    receipt = build_receipt(artifact, artifact_bytes, unchanged)
    receipt_bytes = _json_bytes(receipt)
    report_bytes = render_report(artifact, receipt).encode("utf-8")
    return {
        V2_PATH: artifact_bytes,
        V2_REPORT_PATH: report_bytes,
        RECEIPT_PATH: receipt_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check:
        mismatches = [
            path.relative_to(ROOT).as_posix()
            for path, content in outputs.items()
            if not path.is_file()
            or path.read_bytes().replace(b"\r\n", b"\n") != content
        ]
        if mismatches:
            raise SystemExit(f"M13B v2 deterministic output mismatch: {mismatches}")
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    artifact = json.loads(outputs[V2_PATH])
    receipt = json.loads(outputs[RECEIPT_PATH])
    print(
        json.dumps(
            {
                "status": "pass",
                "mode": "check" if args.check else "write",
                "artifact_id": artifact["artifact_id"],
                "artifact_sha256": _bytes_sha256(outputs[V2_PATH]),
                "source_readiness_subject_sha256": artifact[
                    "source_readiness_subject_sha256"
                ],
                "ready_count": artifact["subject"]["aggregate"]["ready_count"],
                "blocked_count": artifact["subject"]["aggregate"]["blocked_count"],
                "corrected_source_sha256": NEW_SOURCE_SHA256,
                "correction_receipt_id": receipt["receipt_id"],
                "correction_subject_sha256": receipt["correction_subject_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
