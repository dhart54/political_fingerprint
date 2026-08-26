from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_presentations.site_publication import (  # noqa: E402
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
    validate_education_positive_activation_authority,
)
from scripts.foushee_education_workforce_publication_preparation import (  # noqa: E402
    canonical_file_sha256,
)

OUTPUT = (
    ROOT / "docs/editorial/full_record_reviews/publication_activation_candidates/"
    "f000477_education_workforce_119_v1"
)
CANDIDATE_PATH = OUTPUT / "positive_activation_ratification_candidate.json"
PREPARATION_PATH = OUTPUT / "production_eligibility_publication_authority.json"
WRITE_SET_PATH = OUTPUT / "expected_production_write_set.json"
AUTHORITY_PATH = OUTPUT / "positive_activation_authority.json"
RECEIPT_PATH = OUTPUT / "activation_ratification_materialization_receipt.json"

RATIFIED_HEAD = "f5b762d748e1f87dc4c5c5da58acaaf6f1c40878"
RATIFIED_BASE = "1a01725dbd3311bfa8dcdea31009466f2c51c6a1"
RATIFIED_CANDIDATE_FILE_SHA256 = (
    "655beaba23fd9c0af93ef5908c0c3040ad6f756e354c9f763e7595c2e039a315"
)
RATIFIED_PROSPECTIVE_SUBJECT_SHA256 = (
    "261d37a2b716f8e601f22b41dcf10147072a4c32a3c5b98111e4b0f488460a1a"
)
DECISION_RECORDED_AT_UTC = "2026-08-26T01:48:58.997491Z"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_authority() -> tuple[dict, str]:
    candidate = _load(CANDIDATE_PATH)
    preparation = _load(PREPARATION_PATH)
    write_set = _load(WRITE_SET_PATH)
    if (
        canonical_file_sha256(CANDIDATE_PATH) != RATIFIED_CANDIDATE_FILE_SHA256
        or candidate["prospective_authority_subject_sha256"]
        != RATIFIED_PROSPECTIVE_SUBJECT_SHA256
    ):
        raise ValueError("ratified M13N candidate identity differs")
    prospective = copy.deepcopy(candidate["prospective_authority_subject"])
    removed = prospective.pop("candidate_prepared_at_utc")
    prospective["decision_recorded_at_utc"] = DECISION_RECORDED_AT_UTC
    authority = {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": EDUCATION_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "accepted": True,
        "sealed": True,
        "subject": prospective,
        "activation_authority_subject_sha256": semantic_hash(prospective),
    }
    presentation = next(
        item["payload"]
        for item in write_set["artifacts"]
        if item["natural_key"]
        == "site-integration-candidate:f000477:education_workforce:119:v1"
    )
    validate_education_positive_activation_authority(
        authority,
        candidate=presentation,
        candidate_authority=preparation,
        metadata=write_set["publication_registry"]["publication_metadata"],
    )
    return authority, removed


def build_receipt(authority: dict, removed: str) -> dict:
    subject = {
        "ratified_pr": 172,
        "ratified_head": RATIFIED_HEAD,
        "ratified_base": RATIFIED_BASE,
        "ratified_candidate_file_sha256": RATIFIED_CANDIDATE_FILE_SHA256,
        "ratified_prospective_authority_subject_sha256": (
            RATIFIED_PROSPECTIVE_SUBJECT_SHA256
        ),
        "removed_candidate_prepared_at_utc": removed,
        "added_decision_recorded_at_utc": DECISION_RECORDED_AT_UTC,
        "every_other_subject_field_identical": True,
        "materialized_authority_subject_sha256": authority[
            "activation_authority_subject_sha256"
        ],
    }
    return {
        "schema_version": "m13n_activation_ratification_materialization_receipt_v1",
        "artifact_id": (
            "activation-ratification-materialization-receipt:"
            "f000477:education_workforce:119:v1"
        ),
        "immutable": True,
        "subject": subject,
        "receipt_subject_sha256": semantic_hash(subject),
    }


def main() -> int:
    authority, removed = build_authority()
    receipt = build_receipt(authority, removed)
    AUTHORITY_PATH.write_text(_text(authority), encoding="utf-8", newline="\n")
    RECEIPT_PATH.write_text(_text(receipt), encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
                "authority_subject_sha256": authority[
                    "activation_authority_subject_sha256"
                ],
                "receipt_file_sha256": canonical_file_sha256(RECEIPT_PATH),
                "receipt_subject_sha256": receipt["receipt_subject_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
