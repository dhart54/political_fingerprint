"""Validate the detached, publication-inactive M13M integration package."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.editorial_presentations.education_workforce_integration_candidate import (  # noqa: E402
    validate_education_workforce_site_integration_candidate,
)
from backend.scripts.build_m13m_education_workforce_site_integration import (  # noqa: E402
    OUTPUT,
    build,
)


def main() -> None:
    result = build(check=True)
    candidate = result["candidate"]
    validate_education_workforce_site_integration_candidate(candidate)
    presentation = candidate["subject"]["presentation"]
    items = [
        presentation["overview"],
        *presentation["repeated_patterns"],
        *presentation["notable_choices"],
    ]
    if (
        len(items) != 3
        or presentation["syntheses"]
        or presentation["policy_trajectories"]
        or [item["direction_label"] for item in items] != [None, None, "Mixed"]
    ):
        raise ValueError("M13M exact three-surface projection differs")
    evidence = candidate["subject"]["preview_data"]["evidence_119"]
    if (
        len(evidence) != 17
        or len({row["governed_receipt_projection"]["episode_id"] for row in evidence})
        != 16
    ):
        raise ValueError("M13M governed action/episode accounting differs")
    manifest = json.loads(
        (OUTPUT / "screenshot_manifest.json").read_text(encoding="utf-8")
    )
    if len(manifest["captures"]) != 5:
        raise ValueError("M13M responsive render evidence differs")
    if any(
        candidate["subject"]["controls"][key]
        for key in (
            "public",
            "production_selectable",
            "publication_active",
            "publication_eligibility",
            "production_persistence",
            "database_writes",
            "production_writes",
            "deployment",
        )
    ):
        raise ValueError("M13M downstream authority leaked")
    print(
        json.dumps(
            {
                "status": "pass",
                "artifact_id": candidate["artifact_id"],
                "candidate_file_sha256": result["review_packet"]["candidate_binding"][
                    "file_sha256"
                ],
                "candidate_subject_sha256": candidate["candidate_subject_sha256"],
                "wording_items": 3,
                "semantic_lineage_actions": 4,
                "governed_actions": 17,
                "governed_episodes": 16,
                "screenshots": 5,
                "all_later_authorities_false": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
