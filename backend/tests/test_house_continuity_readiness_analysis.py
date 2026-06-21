import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.house_continuity_readiness_analysis import (  # noqa: E402
    classify_domain,
    has_material_topic_overlap,
    share,
)


def test_broad_domain_facet_is_not_material_topic_overlap() -> None:
    assert has_material_topic_overlap("ECONOMY_TAXES", ["economy_taxes"]) is False
    assert has_material_topic_overlap("ECONOMY_TAXES", ["economy_taxes", "tax credits"]) is True


def test_domain_classification_does_not_use_shared_domain_alone() -> None:
    row_118 = {"substantive_rows": 100}
    row_119 = {"substantive_rows": 100}
    classification = classify_domain(
        "HEALTH_SOCIAL",
        row_118,
        row_119,
        ["health_social"],
        False,
        set(range(100)),
        ["final_passage"],
        {"has_support_and_oppose_both_congresses": True},
    )

    assert classification == "not currently comparable"


def test_share_handles_zero_denominator() -> None:
    assert share(1, 0) == 0.0
    assert share(1, 4) == 0.25
