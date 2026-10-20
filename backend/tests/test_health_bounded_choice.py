"""Exact Health admission and public isolation; no real owner decision."""

from __future__ import annotations

import json
import copy
from unittest.mock import patch

import pytest

from app.editorial_presentations import bounded_choice_review as r
from app.editorial_presentations import bounded_choice_publication as p
from app.editorial_presentations.selector import select_public_presentations
from scripts.validate_full_record_issue_interpretation import validate_review

DIRECTORY = r.ROOT / "docs/editorial/review_packages/health_bounded_choice_v1"


def load(member, suffix):
    return json.loads(
        (DIRECTORY / f"{member.lower()}-{suffix}.json").read_text(encoding="utf-8")
    )


def synthetic_candidate(member="F000477"):
    """In-memory test authority only. Never exported as a review artifact."""
    subject, presentation, rendering, receipt = [
        load(member, name)
        for name in ["semantic", "presentation", "rendering", "pending-receipt"]
    ]
    receipt.update(
        decision="accept_exact_bounded_choice_and_rendering",
        reviewer="SYNTHETIC TEST ONLY",
        reviewer_authority="bounded_choice_review_authority_v1",
        decided_at_utc="2026-10-19T00:00:00Z",
        authority_evidence=r.owner_authority.TEST_EVIDENCE,
    )
    receipt = r.seal(receipt, "receipt_subject_sha256")
    return p.candidate(
        subject, presentation, rendering, receipt, allow_test_authority=True
    )


@pytest.mark.parametrize("member", r.MEMBERS)
def test_checked_candidates_reproduce_exact_frozen_inputs_and_bounded_accounting(
    member,
):
    foundation = r.load_foundation()
    semantic = load(member, "semantic")
    r.validate_semantic_subject(semantic, foundation)
    r.validate_presentation(load(member, "presentation"), semantic, foundation)
    accounting = load(member, "accounting")
    assert accounting == semantic["accounting_review"]
    assert validate_review(accounting)["action_count"] == 1
    assert all(v is None for v in accounting["external_authority"].values())
    assert accounting["synthesis"]["full_issue_synthesis_eligible"] is False
    assert len(semantic["member_ir"]["proposition_graph"]["propositions"]) == (
        1 if member == "F000477" else 0
    )
    assert r.source_evidence() == semantic["additional_raw_evidence"]


@pytest.mark.parametrize("member", r.MEMBERS)
def test_pending_receipts_reject_at_every_acceptance_dependent_boundary(member):
    subject, presentation, rendering, receipt = [
        load(member, n)
        for n in ["semantic", "presentation", "rendering", "pending-receipt"]
    ]
    r.validate_receipt(
        receipt,
        subject=subject,
        presentation=presentation,
        rendering=rendering,
        require_accepted=False,
    )
    with pytest.raises(ValueError, match="pending"):
        p.candidate(subject, presentation, rendering, receipt)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x.update(member_id="M001184"),
        lambda x: x.update(issue_id="NATIONAL_SECURITY_FOREIGN"),
        lambda x: x.update(review_scope="full_defined_issue_record"),
        lambda x: x.update(action_ids=["house:119:2:181"]),
        lambda x: x.update(normalized_source_sha256="0" * 64),
        lambda x: x["presentation_inputs"]["records"]["finding"].update(
            text="Broad Health conclusion"
        ),
        lambda x: x["member_ir"]["proposition_graph"]["propositions"][0].update(
            conclusion_relevance="primary"
        ),
        lambda x: x["presentation_inputs"]["boundaries"].clear(),
        lambda x: x["additional_raw_evidence"][0].update(raw_sha256="0" * 64),
    ],
)
def test_resealed_wrong_semantic_subject_cannot_gain_authority(mutation):
    value = load("F000477", "semantic")
    mutation(value)
    with pytest.raises(ValueError):
        r.validate_semantic_subject(r.seal(value, "semantic_subject_sha256"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer_authority", "gold"),
        ("decided_at_utc", "2999-01-01T00:00:00Z"),
        ("reviewer", " "),
        ("decision", "approve_all_health"),
        ("rendering_subject_sha256", "0" * 64),
        ("member_id", "M001184"),
        ("authorizations", {"publication": True}),
    ],
)
def test_resealed_wrong_receipt_rejected(field, value):
    candidate = synthetic_candidate()
    candidate["acceptance"][field] = value
    candidate["acceptance"] = r.seal(candidate["acceptance"], "receipt_subject_sha256")
    with pytest.raises(ValueError):
        p.validate_candidate(candidate)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x["runtime_manifest"].update({"frontend/app/globals.css": "0" * 64}),
        lambda x: x["captures"][0].update(sha256="0" * 64),
        lambda x: x["captures"][0].update(page_errors=["error"]),
        lambda x: x["captures"].pop(),
    ],
)
def test_resealed_stale_render_or_capture_rejected(mutation):
    value = synthetic_candidate()
    mutation(value["rendering"])
    value["rendering"] = r.seal(value["rendering"], "rendering_subject_sha256")
    with pytest.raises(ValueError):
        p.validate_candidate(value)


def public_row(value):
    return {
        "publication_basis": "bounded_choice_review",
        "member_bioguide_id": value["semantic"]["member_id"],
        "issue_id": r.ISSUE,
        "publicly_active": True,
        "deactivated_at": None,
        "editorial_status": "human_approved",
        "benchmark_status": "not_promoted",
        "production_eligible": True,
        "payload_jsonb": value,
        "content_sha256": p.canonical_digest(value),
        "schema_version": value["schema_version"],
        "artifact_version": 1,
        "natural_key": value["artifact_id"],
        "publication_metadata_jsonb": {
            "activation_authority_sha256": "0" * 64,
            "publication_basis": "bounded_choice_review",
            "presentation_natural_key": value["artifact_id"],
            "presentation_artifact_version": 1,
            "active_artifact_sha256": p.canonical_digest(value),
        },
    }


@pytest.mark.parametrize("member", r.MEMBERS)
def test_closed_selector_only_exposes_bounded_card_after_exact_acceptance(member):
    from unittest.mock import patch

    value = synthetic_candidate(member)
    row = public_row(value)
    assert p.select_bounded_publication(row, member_id=member, scope="119") is None
    # Simulate the external governed trust seam, never a serving override.
    with patch.object(r.owner_authority, "require_trusted_decision"):
        selected = select_public_presentations(
            [row],
            legislator_id=r.MEMBERS[member][1],
            member_bioguide_id=member,
            scope="119",
        )
    health = next(x for x in selected["presentations"] if x["issue_id"] == r.ISSUE)
    assert health["presentation_branch"] == "bounded_choice_review"
    assert health["conclusion"] is health["teaser"] is None
    assert health["notable_choices"] == []  # no implicit primary/summary projection
    assert p.select_bounded_publication(row, member_id=member, scope="118") is None
    assert p.select_bounded_publication(row, member_id="wrong", scope="119") is None
    row["payload_jsonb"]["acceptance"] = load(member, "pending-receipt")
    row["content_sha256"] = p.canonical_digest(row["payload_jsonb"])
    assert p.select_bounded_publication(row, member_id=member, scope="119") is None


def test_empty_candidate_and_unrelated_gold_rows_preserve_defaults():
    args = dict(
        legislator_id="test",
        member_bioguide_id="F000477",
        scope="all",
        review_states=[],
    )
    expected = select_public_presentations([], **args)
    row = public_row(synthetic_candidate())
    row["benchmark_status"] = "gold_benchmark"
    assert select_public_presentations([row], **args) == expected


def test_auto_deployment_has_no_staged_migration_or_activation_hook():
    # This is an executable interface with no CLI entry point or startup import.
    module = (
        r.ROOT / "backend/app/editorial_presentations/bounded_choice_publication.py"
    ).read_text()
    assert "__main__" not in module
    for directory in [r.ROOT / ".github/workflows", r.ROOT / "frontend"]:
        files = (
            list(directory.glob("*.yml"))
            if directory.name == "workflows"
            else [directory / "package.json"]
        )
        for file in files:
            text = file.read_text()
            assert "db push" not in text and "supabase migration up" not in text
    assert (
        r.ROOT / "backend/migrations/0016_editorial_artifact_persistence.sql"
    ).is_file()


def test_closed_receipt_schema_matches_pending_and_synthetic_positive_subjects():
    from jsonschema import Draft7Validator

    schema = json.loads((DIRECTORY / "acceptance_receipt.schema.json").read_text())
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)
    for member in r.MEMBERS:
        validator.validate(load(member, "pending-receipt"))
        validator.validate(synthetic_candidate(member)["acceptance"])


@pytest.mark.parametrize("member", r.MEMBERS)
@pytest.mark.parametrize("reseal", [False, True])
@pytest.mark.parametrize(
    "part,path,value",
    [
        (
            "semantic",
            ["accounting_review", "frontend_state", "total_recorded_actions"],
            True,
        ),
        ("semantic", ["congress"], 119.0),
        ("semantic", ["authorizing"], 0),
        ("presentation", ["congress"], 119.0),
        ("presentation", ["authorizing"], 0),
    ],
)
def test_typed_subject_mutations_fail_constructor_and_serving(
    member, reseal, part, path, value
):
    candidate = synthetic_candidate(member)
    node = candidate[part]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    if reseal:
        candidate[part] = r.seal(candidate[part], f"{part}_subject_sha256")
    with pytest.raises(ValueError):
        p.candidate(
            candidate["semantic"],
            candidate["presentation"],
            candidate["rendering"],
            candidate["acceptance"],
            allow_test_authority=True,
        )
    with patch.object(r.owner_authority, "require_trusted_decision"):
        assert (
            p.select_bounded_publication(
                public_row(candidate), member_id=member, scope="119"
            )
            is None
        )


@pytest.mark.parametrize(
    "evidence",
    [
        None,
        {},
        r.owner_authority.TEST_EVIDENCE,
        {
            "kind": "owner_decision",
            "decision_id": "unregistered",
            "decision_sha256": "a" * 64,
        },
    ],
)
def test_self_asserted_or_stripped_synthetic_receipt_never_confers_default_authority(
    evidence,
):
    value = synthetic_candidate()
    value["acceptance"].update(
        authority_evidence=evidence, reviewer="Plausible owner name"
    )
    value["acceptance"] = r.seal(value["acceptance"], "receipt_subject_sha256")
    with pytest.raises(ValueError, match="owner decision"):
        p.validate_candidate(value)
    with pytest.raises(ValueError):
        p.graph(value)
    assert (
        p.select_bounded_publication(
            public_row(value), member_id="F000477", scope="119"
        )
        is None
    )


def test_registered_evidence_pins_bytes_decision_and_exact_full_subject(
    tmp_path, monkeypatch
):
    a = r.owner_authority
    receipt = synthetic_candidate()["acceptance"]
    decision = {
        "schema_version": "bounded_choice_owner_decision_v1",
        "decision_id": "contract-fixture",
        "provenance": {
            "kind": "direct_owner_decision",
            "source_ref": "test fixture only",
            "decision_quote": "test fixture only",
        },
        **{k: receipt[k] for k in a.DECISION_FIELDS},
    }
    raw = (json.dumps(decision) + "\n").encode()
    path = tmp_path / a.DIRECTORY / "owner_decisions/contract-fixture.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    entry = {
        "decision_id": decision["decision_id"],
        "path": path.relative_to(tmp_path).as_posix(),
        "file_sha256": r.hashlib.sha256(raw).hexdigest(),
        "decision_sha256": p.canonical_digest(decision),
    }
    registry = tmp_path / a.DIRECTORY / "owner_decision_registry.json"
    registry.write_text(
        json.dumps(
            {
                "schema_version": "bounded_choice_owner_decision_registry_v1",
                "records": [entry],
            }
        )
    )
    monkeypatch.setattr(a, "TRUST_ROOT", tmp_path)
    receipt["authority_evidence"] = {
        "kind": "owner_decision",
        "decision_id": entry["decision_id"],
        "decision_sha256": entry["decision_sha256"],
    }
    a.require_trusted_decision(receipt)
    for key in a.DECISION_FIELDS:
        wrong = copy.deepcopy(receipt)
        wrong[key] = "different"
        with pytest.raises(ValueError):
            a.require_trusted_decision(wrong)
    path.write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="bytes"):
        a.require_trusted_decision(receipt)


def test_source_reconciliation_detects_changed_content_and_preserves_typography():
    from app.editorial_presentations.bounded_choice_sources import (
        reconcile_sources,
        typography,
    )

    foundation = r.load_foundation()
    raw = {
        source: r._filesystem_path(r.ROOT / r.RAW_ROOT / name).read_bytes()
        for name, source in r.RAW.items()
    }
    reconcile_sources(raw, foundation["governed_sources.json"])
    assert typography("a  \u2018quoted\u2019 word .") == typography(
        "a ``quoted'' word."
    )
    for old, new in [
        (b"1,762,668,000", b"1,762,668,001"),
        (b"clinical building", b"hospital building"),
    ]:
        changed = copy.deepcopy(raw)
        key = "congress-text:119:s:2393:es"
        assert old in changed[key]
        changed[key] = changed[key].replace(old, new)
        with pytest.raises(ValueError, match="bill text"):
            reconcile_sources(changed, foundation["governed_sources.json"])
    for section in ["metadata", "member_records", "party_totals"]:
        governed = copy.deepcopy(foundation["governed_sources.json"])
        clerk = governed["sources"][0]
        if section == "metadata":
            clerk[section]["vote-question"] = "Different"
        elif section == "member_records":
            clerk[section]["M001184"]["official_label"] = "Yea"
        else:
            clerk[section][0]["yea-total"] = "198"
        with pytest.raises(ValueError):
            reconcile_sources(raw, governed)


def test_compiler_replay_compares_typed_outputs_not_only_file_pins():
    foundation = r.load_foundation()
    for name in [
        "compiler_input.json",
        "compiled_ir.json",
        "presentation_payload.json",
    ]:
        changed = copy.deepcopy(foundation)
        changed[name]["extra_unreviewed_field"] = True
        with pytest.raises(ValueError, match="replay differs"):
            r.replay_foundation(changed)


def test_real_api_transport_fixture_is_current():
    from health_choice_transport import transport

    path = r.ROOT / "frontend/tests/fixtures/health-choice-api.json"
    assert json.loads(path.read_text(encoding="utf-8")) == transport()
    for member in r.MEMBERS:
        axes = load(member, "accounting")["axes"]
        assert (
            axes["semantic_tier"] == "receipts_only"
            and axes["public_claim_class"] == "vote_record_only"
        )


def test_actual_backend_working_directory_validates_without_repo_pythonpath():
    import os
    import subprocess
    import sys

    code = """
import json, copy
from app.editorial_presentations import bounded_choice_review as r
directory=r.ROOT/'docs/editorial/review_packages/health_bounded_choice_v1'
for member in r.MEMBERS:
    subject=json.loads((directory/f'{member.lower()}-semantic.json').read_text(encoding='utf-8'))
    presentation=json.loads((directory/f'{member.lower()}-presentation.json').read_text(encoding='utf-8'))
    r.validate_semantic_subject(subject)
    r.validate_presentation(presentation,subject)
    wrong=copy.deepcopy(subject)
    wrong['accounting_review']['frontend_state']['total_recorded_actions']=True
    try: r.validate_semantic_subject(r.seal(wrong,'semantic_subject_sha256'))
    except ValueError: pass
    else: raise AssertionError('typed mutation accepted')
r.source_evidence()
print('backend runtime validation passed')
"""
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=r.ROOT / "backend",
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "backend runtime validation passed"


@pytest.mark.parametrize(
    "suffix",
    [
        "semantic.json",
        "accounting.json",
        "presentation.json",
        "rendering.json",
        "pending-receipt.json",
        "initial-publication-preparation.json",
        "desktop.png",
        "mobile.png",
    ],
)
@pytest.mark.parametrize("change", ["missing", "changed"])
def test_default_acceptance_and_registration_preparation_require_complete_counterpart(
    tmp_path, monkeypatch, suffix, change
):
    import shutil
    from app.editorial_presentations import bounded_choice_pair as pair
    from health_choice_registered_fixture import registered_fixture

    values = registered_fixture(tmp_path / "trust", monkeypatch)
    value = values["F000477"]
    isolated = tmp_path / "pair"
    shutil.copytree(DIRECTORY, isolated / pair.DIRECTORY)
    for path in r.RENDER_FILES:
        target = isolated / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(r.ROOT / path, target)
    monkeypatch.setattr(pair, "PAIR_ROOT", isolated)
    # Verify the unmodified isolated data first with the actual trust verifier.
    p.validate_candidate(value)
    stem = "m001184-" + suffix
    path = (
        isolated
        / pair.DIRECTORY
        / ("previews" if suffix.endswith(".png") else "")
        / stem
    )
    assert path.is_file()
    if change == "missing":
        path.unlink()
    elif suffix.endswith(".png"):
        path.write_bytes(path.read_bytes() + b"TEST ONLY changed capture")
    else:
        document = json.loads(path.read_text(encoding="utf-8"))
        document["TEST_ONLY_changed_counterpart"] = True
        path.write_text(json.dumps(document), encoding="utf-8")
    for action in [
        lambda: p.candidate(
            value["semantic"],
            value["presentation"],
            value["rendering"],
            value["acceptance"],
        ),
        lambda: p.validate_candidate(value),
        lambda: p.build_write_set(value, preparation={}, runtime={}, baseline={}),
        lambda: r.owner_authority.registration_plan(value["acceptance"]),
    ]:
        with pytest.raises((ValueError, OSError)):
            action()


def test_preparation_separately_accounts_for_exact_owner_registration():
    for member in r.MEMBERS:
        preparation = load(member, "initial-publication-preparation")
        registration = preparation["owner_evidence_registration"]
        assert registration["state"] == "pending_separate_exact_registration_approval"
        assert registration["mutation_caps"] == r.owner_authority.REGISTRATION_CAPS
        assert (
            registration["exact_row"]
            is registration["exact_row_sha256"]
            is registration["registration_approval"]
            is None
        )
        assert registration["authorizing"] is False
        assert "owner" in registration["table"]
        assert preparation["mutation_caps"]["insert_artifacts"] == 4
        assert preparation["mutation_caps"]["unauthorized_table_writes"] == 0
        assert any(
            "exactly one owner-evidence" in requirement
            for requirement in preparation["future_requirements"]
        )


@pytest.mark.parametrize(
    "assignment",
    [
        {"F000477": "F000477", "M001184": "F000477"},
        {"F000477": "M001184", "M001184": "M001184"},
        {"F000477": "M001184", "M001184": "F000477"},
    ],
    ids=["duplicate_foushee", "duplicate_massie", "swapped"],
)
def test_resealed_duplicate_or_swapped_pair_rejects_default_admission(
    tmp_path, monkeypatch, assignment
):
    import shutil
    from app.editorial_presentations import bounded_choice_pair as pair
    from health_choice_registered_fixture import registered_inputs

    isolated = tmp_path / "pair"
    shutil.copytree(DIRECTORY, isolated / pair.DIRECTORY)
    for path in r.RENDER_FILES:
        target = isolated / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(r.ROOT / path, target)
    monkeypatch.setattr(pair, "PAIR_ROOT", isolated)
    directory = isolated / pair.DIRECTORY
    bundles = {
        outer: {
            suffix: load(inner, suffix)
            for suffix in ["semantic", "accounting", "presentation", "rendering"]
        }
        for outer, inner in assignment.items()
    }
    # Every substituted bundle is independently valid. Only its outer identity
    # is false; resealing must never turn those duplicate identities into a pair.
    for bundle in bundles.values():
        r.validate_semantic_subject(bundle["semantic"])
        r.validate_presentation(bundle["presentation"], bundle["semantic"])
        r.validate_rendering(bundle["rendering"], bundle["presentation"], root=isolated)
    forged = r.seal(
        {
            "schema_version": "bounded_choice_pair_subject_v1",
            "authorizing": False,
            "members": {
                outer: {
                    "semantic_subject_sha256": b["semantic"]["semantic_subject_sha256"],
                    "accounting_sha256": p.canonical_digest(b["accounting"]),
                    "presentation_subject_sha256": b["presentation"][
                        "presentation_subject_sha256"
                    ],
                    "rendering_subject_sha256": b["rendering"][
                        "rendering_subject_sha256"
                    ],
                }
                for outer, b in bundles.items()
            },
        },
        "pair_subject_sha256",
    )
    (directory / "pair-subject.json").write_text(json.dumps(forged), encoding="utf-8")
    for outer, b in bundles.items():
        for suffix, document in b.items():
            (directory / f"{outer.lower()}-{suffix}.json").write_text(
                json.dumps(document), encoding="utf-8"
            )
        receipt = r.pending_receipt(
            b["semantic"],
            b["presentation"],
            b["rendering"]["rendering_subject_sha256"],
            forged["pair_subject_sha256"],
        )
        preparation = load(assignment[outer], "initial-publication-preparation")
        preparation.update(
            member_id=outer,
            pair_subject_sha256=forged["pair_subject_sha256"],
            pending_receipt_subject_sha256=receipt["receipt_subject_sha256"],
        )
        (directory / f"{outer.lower()}-pending-receipt.json").write_text(
            json.dumps(receipt), encoding="utf-8"
        )
        (
            directory / f"{outer.lower()}-initial-publication-preparation.json"
        ).write_text(json.dumps(preparation), encoding="utf-8")
    # Real verifier, isolated TEST ONLY registered evidence; no test authority
    # flag or verifier mock. The forged pair itself is the admission failure.
    inputs = registered_inputs(tmp_path / "trust", monkeypatch, directory=directory)
    subject, presentation, rendering, receipt = next(iter(inputs.values()))
    r.owner_authority.require_trusted_decision(receipt)
    for action in [
        lambda: pair.build_pair_subject(bundles),
        lambda: pair.validate_pair_subject(),
        lambda: r.validate_receipt(
            receipt, subject=subject, presentation=presentation, rendering=rendering
        ),
        lambda: p.candidate(subject, presentation, rendering, receipt),
    ]:
        with pytest.raises(ValueError, match="member identity"):
            action()


@pytest.mark.parametrize("part", ["accounting", "presentation", "rendering"])
def test_pair_rejects_split_member_identity_before_nested_validation(part):
    from app.editorial_presentations import bounded_choice_pair as pair

    bundles = {
        member: {
            suffix: load(member, suffix)
            for suffix in ["semantic", "accounting", "presentation", "rendering"]
        }
        for member in r.MEMBERS
    }
    target = bundles["F000477"][part]
    if part == "accounting":
        target = target["subject"]
    target["member_id"] = "M001184"
    with pytest.raises(ValueError, match="member identity"):
        pair.build_pair_subject(bundles)


def test_pending_preparation_rejects_outer_member_substitution():
    from app.editorial_presentations import bounded_choice_pair as pair

    subject, presentation, receipt = [
        load("F000477", suffix)
        for suffix in ["semantic", "presentation", "pending-receipt"]
    ]
    with pytest.raises(ValueError, match="member identity"):
        pair.pending_preparation(
            "M001184", subject, presentation, receipt, receipt["pair_subject_sha256"]
        )
