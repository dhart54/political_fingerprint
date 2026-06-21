import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.house_comparable_policy_question_audit import (  # noqa: E402
    FAMILY_RULES,
    assign_family,
    extract_amendment_identity,
    has_both_congresses,
    share,
)


def test_specific_family_match_uses_governing_question_not_domain_only() -> None:
    rules = [rule for rule in FAMILY_RULES if rule.domain == "NATIONAL_SECURITY_FOREIGN"]

    matched = assign_family(
        {
            "domain": "NATIONAL_SECURITY_FOREIGN",
            "question": "On Agreeing to the Resolution",
            "description": "",
            "bill_title": "Directing the President pursuant to section 5(c) of the War Powers Resolution to remove United States Armed Forces",
            "issue_facet": "national_security_foreign",
            "plain_english_summary": "This was a direct vote on a War Powers Resolution removal measure.",
            "policy_effect": None,
        },
        rules,
    )

    assert matched is not None
    assert matched.family_id == "nsf_war_powers_removal_resolutions"


def test_broad_domain_text_alone_does_not_assign_family() -> None:
    rules = [rule for rule in FAMILY_RULES if rule.domain == "ECONOMY_TAXES"]

    matched = assign_family(
        {
            "domain": "ECONOMY_TAXES",
            "question": "On Passage",
            "description": "",
            "bill_title": "A generic economic policy bill",
            "issue_facet": "economy_taxes",
            "plain_english_summary": "This was a direct vote on an economy taxes measure.",
            "policy_effect": None,
        },
        rules,
    )

    assert matched is None


def test_amendment_identity_signal_is_text_derived_and_limited() -> None:
    assert (
        extract_amendment_identity(
            {
                "question": "On Agreeing to the Amendment",
                "description": "",
                "bill_title": "Lower Energy Costs Act",
                "issue_facet": "House amendment vote",
                "plain_english_summary": "This vote was on whether to agree to an amendment to H.R. 1 about permits.",
            }
        )
        == "amendment to h.r. 1"
    )


def test_has_both_congresses_respects_minimum_cast_votes() -> None:
    congresses = {118: {"cast_votes": 3}, 119: {"cast_votes": 2}}

    assert has_both_congresses(congresses, 1) is True
    assert has_both_congresses(congresses, 3) is False


def test_share_handles_zero_denominator() -> None:
    assert share(1, 0) == 0.0
    assert share(1, 4) == 0.25
