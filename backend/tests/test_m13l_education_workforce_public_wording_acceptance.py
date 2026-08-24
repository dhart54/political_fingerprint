from copy import deepcopy

import pytest

from backend.app.etl.full_record_public_wording_decisions import (
    PublicWordingDecisionError,
    validate_implementation,
)
from backend.scripts.build_m13l_education_workforce_public_wording_acceptance import (
    CANDIDATE_PARITY_PATH,
    PACKAGE_PATH,
    TEMPLATE_PATH,
    build,
    load,
)
from scripts.validate_m13l_education_workforce_public_wording_acceptance import validate


def artifacts():
    built = build(check=True)
    return built, load(PACKAGE_PATH), load(TEMPLATE_PATH), load(CANDIDATE_PARITY_PATH)


def test_m13l_exact_accept_as_written_and_closed() -> None:
    built, package, template, parity = artifacts()
    final = validate_implementation(
        built["implementation"],
        authority=built["authority"],
        package=package,
        decision_template=template,
        parity=parity,
    )
    assert final == {
        "canonical_reviewed_wording_count": 3,
        "surface_accounting": {
            "issue_overview": 1,
            "repeated_pattern": 1,
            "notable_choice": 1,
        },
        "decision_accounting": {
            "accept_candidate_as_written": 3,
            "accept_with_bounded_revision": 0,
            "rejected": 0,
            "unresolved": 0,
        },
    }
    assert validate()["status"] == "pass"


def test_m13l_rejects_copy_or_direction_drift() -> None:
    built, package, template, parity = artifacts()
    changed = deepcopy(built["implementation"])
    changed["subject"]["implementation_records"][0]["implemented_reviewed_wording"][
        "primary_sentence"
    ] += " Changed."
    with pytest.raises(PublicWordingDecisionError):
        validate_implementation(
            changed,
            authority=built["authority"],
            package=package,
            decision_template=template,
            parity=parity,
        )


def test_mixed_display_belongs_only_to_notable_choice() -> None:
    built, *_ = artifacts()
    records = built["implementation"]["subject"]["implementation_records"]
    displays = {
        row["implemented_reviewed_wording"]["surface"]: row[
            "implemented_reviewed_wording"
        ]["direction_display"]
        for row in records
    }
    assert displays == {
        "issue_overview": None,
        "repeated_pattern": None,
        "notable_choice": {"label": "Mixed", "symbol": "±"},
    }
