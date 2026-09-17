from backend.scripts.build_cross_issue_editorial_generality_selection import (
    ROOT,
    STARTING_COMMIT,
    build,
    outputs,
)


def candidates():
    return {item["domain_id"]: item for item in build()["candidate_domains"]}


def test_selection_fails_closed_when_no_domain_meets_every_gate():
    result = build()
    assert result["starting_commit"] == STARTING_COMMIT
    assert result["selected_domain"] is None
    assert result["selection_state"] == "blocked_no_eligible_domain"
    assert result["stop_condition_triggered"] is True
    assert result["next_stage_authorized"] is False
    assert result["deterministic_selection_lock"]["locked"] is True
    assert len(result["deterministic_selection_lock"]["sha256"]) == 64
    assert not any(item["eligible"] for item in result["candidate_domains"])
    assert all((ROOT / path).is_file() for path in result["source_inventory"])


def test_justice_and_economy_are_never_candidates():
    result = build()
    ids = {item["domain_id"] for item in result["candidate_domains"]}
    assert "JUSTICE_PUBLIC_SAFETY" not in ids
    assert "ECONOMY_TAXES" not in ids
    assert result["excluded_domains"] == ["JUSTICE_PUBLIC_SAFETY", "ECONOMY_TAXES"]


def test_national_security_actions_do_not_overcount_repeated_stages():
    item = candidates()["NATIONAL_SECURITY_FOREIGN"]
    assert item["native_substantive_house_action_count"] >= 5
    assert item["native_independent_episode_count"] == 2
    assert item["episodes"] == ["hr3838-ndaa-fy2026", "s1071-cota-disinterment"]
    assert "five_or_six_action_subset_cannot_span_three_independent_episodes" in item["exclusion_reasons"]


def test_health_benchmark_stratum_does_not_override_stored_domain_identity():
    item = candidates()["HEALTH_SOCIAL"]
    assert item["native_substantive_house_action_count"] == 2
    assert len(item["benchmark_cross_domain_rows"]) == 5
    assert {row["stored_primary_domain"] for row in item["benchmark_cross_domain_rows"]} == {
        "JUSTICE_PUBLIC_SAFETY",
        "ECONOMY_TAXES",
        "NATIONAL_SECURITY_FOREIGN",
    }
    assert "benchmark_stratum_rows_cannot_replace_native_domain_identity" in item["exclusion_reasons"]


def test_remaining_domains_are_below_the_action_floor():
    values = candidates()
    assert values["EDUCATION_WORKFORCE"]["native_substantive_house_action_count"] == 3
    assert values["ENVIRONMENT_ENERGY"]["native_substantive_house_action_count"] == 1
    assert values["IMMIGRATION_BORDER"]["native_substantive_house_action_count"] == 1
    assert values["INFRASTRUCTURE_TECH_TRANSPORT"]["native_substantive_house_action_count"] == 0


def test_publication_and_registry_boundaries_remain_closed():
    result = build()
    assert result["publication"] == {
        "editorial_status": "human_approval_pending",
        "benchmark_status": "not_promoted",
        "productionEligible": False,
    }
    assert result["production_registry_entries"] == []


def test_generated_artifacts_have_no_drift():
    for path, expected in outputs().items():
        assert path.read_text(encoding="utf-8") == expected
