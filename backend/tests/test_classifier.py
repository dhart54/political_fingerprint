from app.classification.classifier import classify_vote


def test_classify_vote_uses_committee_keyword_and_subject_signals() -> None:
    result = classify_vote(
        committee="Committee on Transportation and Infrastructure",
        title="A bill to expand rural broadband access",
        summary="This bill improves broadband deployment and bridge repair grants.",
        subject_tags=["Infrastructure", "Technology"],
        classification_version="fixture-v1",
    )

    assert result.is_eligible is True
    assert result.primary_domain == "INFRASTRUCTURE_TECH_TRANSPORT"
    assert result.classification_version == "fixture-v1"
    assert result.score_breakdown["INFRASTRUCTURE_TECH_TRANSPORT"] == {
        "committee_match": 3,
        "keyword_match": 4,
        "subject_match": 4,
    }


def test_classify_vote_prefers_highest_deterministic_score() -> None:
    result = classify_vote(
        committee="Committee on Homeland Security",
        title="A bill to strengthen border screening and visa enforcement",
        summary="The legislation adds border technology and deportation capacity.",
        subject_tags=["Immigration", "Border Security"],
    )

    assert result.is_eligible is True
    assert result.primary_domain == "IMMIGRATION_BORDER"
    assert result.score_breakdown["IMMIGRATION_BORDER"]["committee_match"] == 3


def test_classify_vote_marks_low_confidence_votes_ineligible() -> None:
    result = classify_vote(
        committee="Committee on House Administration",
        title="A bill to designate commemorative week",
        summary="This bill designates a commemorative week.",
        subject_tags=["Commemorations"],
    )

    assert result.is_eligible is False
    assert result.primary_domain is None
    assert result.eligibility_reason == "low_classification_confidence"


def test_classify_vote_returns_only_scored_domains_in_breakdown() -> None:
    result = classify_vote(
        committee="Committee on Education and Workforce",
        title="A bill to support teacher apprenticeships",
        summary="The bill expands teacher training and school workforce grants.",
        subject_tags=["Education"],
    )

    assert set(result.score_breakdown) == {"EDUCATION_WORKFORCE"}
    assert result.score_breakdown["EDUCATION_WORKFORCE"] == {
        "committee_match": 3,
        "keyword_match": 8,
        "subject_match": 2,
    }
