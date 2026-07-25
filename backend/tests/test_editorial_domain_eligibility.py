from backend.app.summaries.editorial_domain_eligibility import (
    evaluate_primary_domain_eligibility,
)


def decision(
    *,
    exact,
    parent=None,
    measure=None,
    divisions=None,
    title=None,
    earlier=None,
    later=None,
    boundary="Synthetic exact-stage boundary.",
):
    return evaluate_primary_domain_eligibility(
        primary_domain="ENVIRONMENT_ENERGY",
        exact_action_material_domains=exact,
        parent_measure_domains=parent or [],
        measure_wide_domains=measure or [],
        other_division_domains=divisions or [],
        title_domains=title or [],
        earlier_stage_domains=earlier or [],
        later_stage_domains=later or [],
        exact_action_boundary=boundary,
    )


def test_exact_action_material_domain_is_eligible() -> None:
    result = decision(exact=["ENVIRONMENT_ENERGY"])
    assert result["eligible"] is True
    assert result["reason"] == "exact_action_materially_in_primary_domain"


def test_unrelated_division_cannot_inherit_domain_from_another_division() -> None:
    result = decision(
        exact=["JUSTICE_PUBLIC_SAFETY", "ECONOMY"],
        divisions=["ENVIRONMENT_ENERGY"],
    )
    assert result["eligible"] is False


def test_package_cannot_transfer_domain_to_every_component_vote() -> None:
    result = decision(
        exact=["JUSTICE_PUBLIC_SAFETY", "ECONOMY"],
        parent=["ENVIRONMENT_ENERGY"],
        measure=["ENVIRONMENT_ENERGY"],
    )
    assert result["eligible"] is False


def test_title_and_other_stage_context_cannot_rescue_ineligible_action() -> None:
    result = decision(
        exact=["JUSTICE_PUBLIC_SAFETY", "ECONOMY"],
        title=["ENVIRONMENT_ENERGY"],
        earlier=["ENVIRONMENT_ENERGY"],
        later=["ENVIRONMENT_ENERGY"],
    )
    assert result["eligible"] is False
    assert result["reason"] == "exact_action_not_materially_environment_energy"
    assert result["context_cannot_override_exact_action"] is True


def test_cross_domain_exact_action_can_remain_eligible_with_boundary() -> None:
    result = decision(
        exact=["ENVIRONMENT_ENERGY", "JUSTICE_PUBLIC_SAFETY"],
        parent=["ENVIRONMENT_ENERGY", "JUSTICE_PUBLIC_SAFETY"],
    )
    assert result["eligible"] is True
    assert result["exact_action_material_domains"] == [
        "ENVIRONMENT_ENERGY",
        "JUSTICE_PUBLIC_SAFETY",
    ]


def test_action_stage_eligibility_is_invariant_to_title_changes() -> None:
    first = decision(exact=["ENVIRONMENT_ENERGY"], title=["ECONOMY"])
    second = decision(
        exact=["ENVIRONMENT_ENERGY"],
        title=["NATIONAL_SECURITY_FOREIGN", "JUSTICE_PUBLIC_SAFETY"],
    )
    assert first["eligible"] == second["eligible"] is True
    assert first["reason"] == second["reason"]


def test_changing_other_divisions_does_not_change_exact_action_domain() -> None:
    first = decision(exact=["ENVIRONMENT_ENERGY"], divisions=["ECONOMY"])
    second = decision(
        exact=["ENVIRONMENT_ENERGY"],
        divisions=["HEALTH_SOCIAL", "JUSTICE_PUBLIC_SAFETY"],
    )
    assert first["eligible"] == second["eligible"] is True


def test_domain_mismatch_is_rejection_not_caveat() -> None:
    result = decision(
        exact=["ECONOMY"],
        boundary="The mismatch remains explicit but cannot be cured by a caveat.",
    )
    assert result["decision"] == "rejected"
    assert result["eligible"] is False
