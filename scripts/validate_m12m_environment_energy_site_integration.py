"""Validate the detached, publication-inactive M12M integration package."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.editorial_presentations.environment_integration_candidate import (  # noqa: E402
    validate_environment_site_integration_candidate,
)
from backend.scripts.build_m12m_environment_energy_site_integration import (  # noqa: E402
    OUTPUT,
    build,
)


def main() -> None:
    result = build(check=True)
    candidate = result["candidate"]
    validate_environment_site_integration_candidate(candidate)
    presentation = candidate["subject"]["presentation"]
    items = [
        presentation["overview"],
        *presentation["syntheses"],
        *presentation["repeated_patterns"],
    ]
    if len(items) != 5 or any(item["show_direction"] for item in items):
        raise ValueError("M12M exact directionless five-item projection differs")
    if len(candidate["subject"]["preview_data"]["evidence_119"]) != 63:
        raise ValueError("M12M governed receipt universe differs")
    manifest = json.loads(
        (OUTPUT / "screenshot_manifest.json").read_text(encoding="utf-8")
    )
    if len(manifest["captures"]) != 5:
        raise ValueError("M12M responsive render evidence differs")
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
        raise ValueError("M12M downstream authority leaked")
    print(
        json.dumps(
            {
                "status": "pass",
                "artifact_id": candidate["artifact_id"],
                "candidate_subject_sha256": candidate["candidate_subject_sha256"],
                "wording_items": 5,
                "semantic_lineage_actions": 13,
                "governed_receipts": 63,
                "screenshots": 5,
                "all_later_authorities_false": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
