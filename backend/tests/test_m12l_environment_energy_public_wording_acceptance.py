from copy import deepcopy

import pytest

from backend.app.etl.full_record_public_wording_decisions import (
    PublicWordingDecisionError,
    validate_implementation,
)
from backend.scripts.build_m12l_environment_energy_public_wording_acceptance import (
    build,
    load,
    PACKAGE_PATH,
    TEMPLATE_PATH,
    CANDIDATE_PARITY_PATH,
)


def artifacts():
    built = build(check=True)
    return built, load(PACKAGE_PATH), load(TEMPLATE_PATH), load(CANDIDATE_PARITY_PATH)


def test_m12l_is_exact_and_closed() -> None:
    built, package, template, parity = artifacts()
    final = validate_implementation(
        built["implementation"],
        authority=built["authority"],
        package=package,
        decision_template=template,
        parity=parity,
    )
    assert final["canonical_reviewed_wording_count"] == 5
    assert all(
        row["decision"] == "accept_candidate_as_written"
        and row["bounded_revision"] is None
        for row in built["authority"]["subject"]["wording_decisions"]
    )
    assert built["authority"]["subject"]["blocked_action_boundaries"] == []
    assert not any(built["authority"]["subject"]["downstream_authorizations"].values())


def test_m12l_rejects_invented_direction_and_reviewer_is_content_bound() -> None:
    built, package, template, parity = artifacts()
    mutated = deepcopy(built["implementation"])
    mutated["subject"]["implementation_records"][0]["implemented_reviewed_wording"][
        "direction_display"
    ] = "Opposition"
    with pytest.raises(PublicWordingDecisionError):
        validate_implementation(
            mutated,
            authority=built["authority"],
            package=package,
            decision_template=template,
            parity=parity,
        )
    assert (
        built["authority"]["subject"]["reviewer"]
        == "chatgpt:political_fingerprint_authority_thread"
    )
