import copy
import json
from pathlib import Path

import pytest

from scripts.foushee_justice_receipt_evidence_repair import (
    StoreSafetyError,
    WRITE_CAPS,
    validate_bundle,
)


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = (
    ROOT
    / "docs/editorial/full_record_reviews/proposals"
    / "f000477_justice_public_safety_119_receipt_evidence_repair_bundle_v1.json"
)


def test_exact_repair_bundle_is_content_bound_and_fact_only() -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    validate_bundle(bundle)
    assert bundle["write_caps"] == WRITE_CAPS
    assert WRITE_CAPS == {
        "bills": 4,
        "roll_calls": 8,
        "votes_cast": 8,
        "vote_contexts": 8,
        "vote_classifications": 0,
        "vote_interpretations": 0,
        "editorial_artifacts": 0,
        "publication_registry": 0,
        "updates": 0,
        "deletes": 0,
    }
    assert len(bundle["canonical_action_ids"]) == 8
    assert len(bundle["facts"]["official_sources"]) == 8


def test_exact_repair_bundle_rejects_any_fact_or_cap_change() -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    changed_fact = copy.deepcopy(bundle)
    changed_fact["facts"]["votes_cast"][0]["position"] = "nay"
    with pytest.raises(StoreSafetyError, match="digest mismatch"):
        validate_bundle(changed_fact)
    changed_cap = copy.deepcopy(bundle)
    changed_cap["write_caps"]["roll_calls"] = 9
    with pytest.raises(StoreSafetyError, match="digest mismatch"):
        validate_bundle(changed_cap)
