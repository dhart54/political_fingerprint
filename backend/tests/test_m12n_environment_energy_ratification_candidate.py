from __future__ import annotations

import json

import pytest

from app.editorial_presentations.environment_integration_candidate import (
    load_environment_site_integration_candidate,
)
from app.editorial_presentations.site_publication import (
    validate_environment_positive_activation_authority,
)
from scripts.foushee_environment_energy_publication_preparation import (
    AUTHORITY_PATH,
    M12M_PATH,
    WRITE_SET_PATH,
)
from scripts.validate_m12n_publication_activation_ratification_candidate import (
    validate_candidate,
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_m12n_ratification_candidate_is_exact_and_non_authorizing() -> None:
    candidate = validate_candidate()
    assert candidate["immutable"] is True
    assert candidate["accepted"] is False
    assert candidate["sealed"] is False
    assert "subject" not in candidate
    assert "activation_authority_subject_sha256" not in candidate


def test_m12n_ratification_candidate_cannot_satisfy_live_selector_authority() -> None:
    ratification_candidate = validate_candidate()
    write_set = _load(WRITE_SET_PATH)
    with pytest.raises(ValueError, match="binding differs"):
        validate_environment_positive_activation_authority(
            ratification_candidate,
            candidate=load_environment_site_integration_candidate(M12M_PATH),
            candidate_authority=_load(AUTHORITY_PATH),
            metadata=write_set["publication_registry"]["publication_metadata"],
        )
