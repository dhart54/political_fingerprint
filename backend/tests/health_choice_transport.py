"""Non-authorizing API transport fixtures, generated through the real API.

No receipt, owner evidence, accepted graph or serving override is exported.
The trusted-decision seam is mocked only inside this test module because no
real owner decision exists. All projection/indexing code remains real.
"""

from unittest.mock import patch

from app.api import editorial_presentations as api
from app.editorial_presentations import bounded_choice_review as r
from test_health_bounded_choice import synthetic_candidate, public_row
from test_api_editorial_presentations import _row, _approved_artifact


def transport():
    legacy = _row(_approved_artifact())
    result = {
        "test_only": True,
        "authority": "none; transport contract simulation only",
        "responses": [],
        "baselines": [],
    }
    for member in r.MEMBERS:
        row = public_row(synthetic_candidate(member))
        slug = r.MEMBERS[member][1]
        with patch.object(
            api, "get_legislator_profile", return_value={"bioguide_id": member}
        ):
            for scope in ["119", "all", "118"]:
                with patch.object(api, "_load_publication_rows", return_value=[legacy]):
                    baseline = api.get_editorial_presentations(
                        slug, scope=scope, candidate=None
                    )
                # Simulate already admitted trusted data without changing any
                # production selector signature or accepting a test receipt.
                with (
                    patch.object(
                        api, "_load_publication_rows", return_value=[legacy, row]
                    ),
                    patch.object(r.owner_authority, "require_trusted_decision"),
                ):
                    payload = api.get_editorial_presentations(
                        slug, scope=scope, candidate=None
                    )
                result["responses"].append(payload)
                result["baselines"].append(baseline)
    return result
