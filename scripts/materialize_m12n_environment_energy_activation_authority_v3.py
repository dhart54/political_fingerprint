from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_presentations.environment_integration_candidate import (  # noqa: E402
    load_environment_site_integration_candidate,
)
from app.editorial_presentations.site_publication import (  # noqa: E402
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
    validate_environment_positive_activation_authority,
)
from scripts.foushee_environment_energy_publication_preparation import (  # noqa: E402
    AUTHORITY_PATH,
    M12M_PATH,
    WRITE_SET_PATH,
    activation_write_set_binding,
    canonical_file_sha256,
)

sys.path.insert(0, str(ROOT / "scripts"))
from build_m12n_environment_energy_ratification_candidate_v3 import (  # noqa: E402
    CANDIDATE_PATH,
    OUTPUT_ROOT,
    RATIFICATION_CANDIDATE_ID,
    validate_candidate,
)


DECISION_RECORDED_AT_UTC = "2026-08-24T01:31:00Z"
RATIFIED_PR = 161
RATIFIED_HEAD = "ad5eeb97bd4ea62304d6a1471c7cc34935fdf05e"
RATIFIED_BASE = "c480dfabc2fcbd65bf5b22037200af509adb7b5b"
RATIFIED_CANDIDATE_FILE_SHA256 = (
    "5ead0d70159314a1fbd101f60d89d141a319e44d9ae818a7bde29e8a1a94939a"
)
RATIFIED_PROSPECTIVE_SUBJECT_SHA256 = (
    "ce14b7d8a5bc18bae87bf006e7cffe5fb4df233f590b20d7b54e42a44659f6d0"
)
POSITIVE_AUTHORITY_PATH = OUTPUT_ROOT / "positive_activation_authority.json"
MATERIALIZATION_RECEIPT_PATH = (
    OUTPUT_ROOT / "activation_ratification_materialization_receipt.json"
)


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_authority() -> dict:
    candidate = validate_candidate()
    if (
        candidate["artifact_id"] != RATIFICATION_CANDIDATE_ID
        or canonical_file_sha256(CANDIDATE_PATH) != RATIFIED_CANDIDATE_FILE_SHA256
        or candidate["prospective_authority_subject_sha256"]
        != RATIFIED_PROSPECTIVE_SUBJECT_SHA256
    ):
        raise ValueError("ratified M12N V3 candidate identity differs")
    subject = copy.deepcopy(candidate["prospective_authority_subject"])
    if "decision_recorded_at_utc" in subject:
        raise ValueError("prospective authority already contains decision timestamp")
    subject["decision_recorded_at_utc"] = DECISION_RECORDED_AT_UTC
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "accepted": True,
        "sealed": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def validate_authority(authority: dict) -> None:
    candidate = validate_candidate()
    stripped = copy.deepcopy(authority["subject"])
    if stripped.pop("decision_recorded_at_utc", None) != DECISION_RECORDED_AT_UTC:
        raise ValueError("materialized V3 decision timestamp differs")
    if (
        stripped != candidate["prospective_authority_subject"]
        or semantic_hash(stripped) != RATIFIED_PROSPECTIVE_SUBJECT_SHA256
        or authority.get("immutable") is not True
        or authority.get("accepted") is not True
        or authority.get("sealed") is not True
        or authority.get("activation_authority_subject_sha256")
        != semantic_hash(authority["subject"])
    ):
        raise ValueError("materialized V3 authority differs beyond decision timestamp")

    write_set = _load(WRITE_SET_PATH)
    metadata = copy.deepcopy(write_set["publication_registry"]["publication_metadata"])
    metadata["activation_write_set_binding"] = activation_write_set_binding(write_set)
    validate_environment_positive_activation_authority(
        authority,
        candidate=load_environment_site_integration_candidate(M12M_PATH),
        candidate_authority=_load(AUTHORITY_PATH),
        metadata=metadata,
    )


def build_materialization_receipt(authority: dict) -> dict:
    stripped = copy.deepcopy(authority["subject"])
    removed = stripped.pop("decision_recorded_at_utc")
    subject = {
        "ratified_candidate": {
            "artifact_id": RATIFICATION_CANDIDATE_ID,
            "file_sha256": RATIFIED_CANDIDATE_FILE_SHA256,
            "prospective_authority_subject_sha256": (
                RATIFIED_PROSPECTIVE_SUBJECT_SHA256
            ),
            "pull_request": RATIFIED_PR,
            "reviewed_head": RATIFIED_HEAD,
            "reviewed_base": RATIFIED_BASE,
        },
        "ratification": {
            "decision": "approve_exact_publication_activation",
            "reviewer": "chatgpt:political_fingerprint_authority_thread",
            "reviewer_authority": "publication_activation_review_authority_v1",
            "decision_recorded_at_utc": DECISION_RECORDED_AT_UTC,
        },
        "materialized_authority": {
            "artifact_id": authority["artifact_id"],
            "subject_sha256": authority["activation_authority_subject_sha256"],
            "file_sha256": canonical_file_sha256(POSITIVE_AUTHORITY_PATH),
            "accepted": True,
            "sealed": True,
            "immutable": True,
        },
        "timestamp_only_parity": {
            "removed_field": "decision_recorded_at_utc",
            "removed_value": removed,
            "stripped_subject_sha256": semantic_hash(stripped),
            "reproduces_ratified_prospective_subject": (
                stripped == _load(CANDIDATE_PATH)["prospective_authority_subject"]
                and semantic_hash(stripped) == RATIFIED_PROSPECTIVE_SUBJECT_SHA256
            ),
        },
    }
    return {
        "schema_version": "m12n_activation_ratification_materialization_receipt_v3",
        "receipt_id": (
            "activation-ratification-materialization-receipt:"
            "f000477:environment_energy:119:v3"
        ),
        "immutable": True,
        "subject": subject,
        "receipt_subject_sha256": semantic_hash(subject),
    }


def write_and_validate() -> tuple[dict, dict]:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    authority = build_authority()
    POSITIVE_AUTHORITY_PATH.write_text(
        _json_text(authority), encoding="utf-8", newline="\n"
    )
    validate_authority(authority)
    receipt = build_materialization_receipt(authority)
    MATERIALIZATION_RECEIPT_PATH.write_text(
        _json_text(receipt), encoding="utf-8", newline="\n"
    )
    return validate_files()


def validate_files() -> tuple[dict, dict]:
    authority = _load(POSITIVE_AUTHORITY_PATH)
    validate_authority(authority)
    receipt = _load(MATERIALIZATION_RECEIPT_PATH)
    if receipt != build_materialization_receipt(authority):
        raise ValueError("M12N V3 materialization receipt differs deterministically")
    if (
        receipt["receipt_subject_sha256"] != semantic_hash(receipt["subject"])
        or receipt["subject"]["timestamp_only_parity"][
            "reproduces_ratified_prospective_subject"
        ]
        is not True
    ):
        raise ValueError("M12N V3 materialization parity differs")
    return authority, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    authority, receipt = write_and_validate() if args.write else validate_files()
    print(
        json.dumps(
            {
                "status": "valid_sealed_v3_activation_authority",
                "authority_subject_sha256": authority[
                    "activation_authority_subject_sha256"
                ],
                "authority_file_sha256": canonical_file_sha256(POSITIVE_AUTHORITY_PATH),
                "materialization_receipt_subject_sha256": receipt[
                    "receipt_subject_sha256"
                ],
                "materialization_receipt_file_sha256": canonical_file_sha256(
                    MATERIALIZATION_RECEIPT_PATH
                ),
                "stripped_subject_sha256": receipt["subject"]["timestamp_only_parity"][
                    "stripped_subject_sha256"
                ],
                "prospective_subject_reproduced": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
