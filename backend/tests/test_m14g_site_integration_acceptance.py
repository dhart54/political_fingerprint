from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_m14g_site_integration_acceptance as a  # noqa: E402


def artifacts() -> tuple[dict, dict, dict, dict, dict]:
    candidate, review, manifest = a.load_reviewed_artifacts()
    authority = a.load(a.AUTHORITY_PATH)
    accepted = a.load(a.ACCEPTED_PATH)
    return candidate, review, manifest, authority, accepted


def test_acceptance_artifacts_are_exact_and_deterministic() -> None:
    candidate, review, manifest, authority, accepted = artifacts()
    assert authority == a.expected_authority(candidate, review, manifest)
    assert accepted == a.accepted_artifact(candidate, review, manifest, authority)
    assert authority["immutable"] is True
    assert authority["subject"]["decision"] == "accept_as_rendered"
    assert accepted["accepted"] is True
    assert accepted["canonical_internal_site_integration"] is True
    assert accepted["public"] is False
    assert accepted["production_selectable"] is False
    assert all(authority[key] is False for key in a.DOWNSTREAM)
    assert all(accepted[key] is False for key in a.DOWNSTREAM)
    assert all(value is False for value in authority["subject"]["downstream_authorizations"].values())
    assert accepted["subject"]["downstream_authorizations"] == a.DOWNSTREAM


def test_reviewed_candidate_and_render_evidence_are_byte_exact() -> None:
    for path, expected in {**a.FILE_DIGESTS, **a.SCREENSHOTS}.items():
        raw = (ROOT / path).read_bytes()
        assert raw == subprocess.check_output(["git", "show", f"{a.REVIEWED}:{path}"], cwd=ROOT)
        assert a.file_digest(raw) == expected


def test_exact_accepted_presentation_receipt_and_source_contract() -> None:
    _, _, _, authority, accepted = artifacts()
    subject = accepted["subject"]
    assert subject["presentation_accounting"] == {
        "overviews": 1, "repeated_patterns": 2, "directionless_repeated_patterns": 2,
        "notable_choices": 1, "hr1048_direction_label": "Mixed", "syntheses": 0,
        "trajectories": 0, "findings": 3, "main_takeaway_linked_findings": 2,
        "main_takeaway_actions": 4, "main_takeaway_episodes": 3,
        "rendered_retained_limitation_instances": 7,
    }
    assert subject["receipt_accounting"]["reviewed_actions"] == 17
    assert subject["receipt_accounting"]["reviewed_episodes"] == 16
    assert len(subject["receipt_accounting"]["finding_supporting_action_ids"]) == 6
    assert subject["wording_item_sha256s"] == a.WORDING
    assert subject["source_label_contract"]["accepted_sources"] == a.SOURCE_ROWS
    assert authority["subject"]["reviewed_screenshot_manifest"]["capture_head"] == a.CAPTURE_HEAD


def test_exact_receipt_states_and_boundary_are_retained() -> None:
    _, _, _, _, accepted = artifacts()
    states = accepted["subject"]["receipt_state_bindings"]
    assert states["hr1005"]["official_status"] == "Not Voting"
    assert states["hr1005"]["exact_choice_effect"] == "resolved_non_directional"
    assert states["hr1005"]["supports_finding"] is False
    assert len(states["hr1048"]["action_ids"]) == 2
    assert states["hr1048"]["episode_id"] == "hr-1048-amendment-and-final-passage"
    assert states["hr5408_exact_action_meaning"].startswith(a.H5408_PREFIX)
    assert "does not convert" in accepted["subject"]["substantive_boundary"]


@pytest.mark.parametrize("target", ["candidate", "review", "manifest", "authority"])
def test_resealed_mutations_fail_closed(target: str) -> None:
    candidate, review, manifest, authority, _ = artifacts()
    if target == "candidate":
        changed = deepcopy(candidate)
        changed["subject"]["presentation"]["overview"]["primary_sentence"] += " changed"
        changed["candidate_subject_sha256"] = a.canonical_digest(changed["subject"])
        with pytest.raises(ValueError):
            a.expected_authority(changed, review, manifest)
    elif target == "review":
        changed = deepcopy(review)
        changed["rendered_hierarchy"]["counts"]["findings"] = 4
        with pytest.raises(ValueError):
            a.expected_authority(candidate, changed, manifest)
    elif target == "manifest":
        changed = deepcopy(manifest)
        changed["captures"][0]["file_sha256"] = "0" * 64
        with pytest.raises(ValueError):
            a.expected_authority(candidate, review, changed)
    else:
        changed = deepcopy(authority)
        changed["subject"]["downstream_authorizations"]["publication"] = True
        changed["authority_subject_sha256"] = a.canonical_digest(changed["subject"])
        with pytest.raises(ValueError):
            a.accepted_artifact(candidate, review, manifest, changed)


def test_exactly_one_accepted_m14g_site_integration_record_exists() -> None:
    records = []
    for path in ROOT.glob("docs/editorial/site_integration_candidates/**/accepted_site_integration.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("artifact_id") == "accepted-site-integration:f000477:education_workforce:m14g:v1":
            records.append(path)
    assert records == [ROOT / a.ACCEPTED_PATH]


def test_public_label_compatibility_contract_remains_strict() -> None:
    source = (ROOT / "frontend/lib/publicReceipt.mjs").read_text(encoding="utf-8")
    for label in a.source_contract()["allowed_action_source_labels"]:
        assert f'"{label}"' in source
    assert "ALLOWED_ACTION_SOURCE_LABELS.has(supplied)" in source
    assert ": actionSourceLabel(url)" in source
