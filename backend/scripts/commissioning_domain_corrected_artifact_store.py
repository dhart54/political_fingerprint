"""Exact-batch persistence and rollback tool for the corrected corpus.

This wrapper is distinct from the original commissioning batch. Production
apply or rollback still requires the generic store's explicit target and
confirmation flags; this module grants no production authorization.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.editorial_artifacts.bundle import ARTIFACT_TYPES, semantic_hash
from backend.scripts import editorial_artifact_store as store


MANIFEST = (
    ROOT
    / "docs/editorial/commissioning_domain_v1/corrected"
    / "persistence_batch_manifest.json"
)
BATCH_KEY = "commissioning-domain-v1-environment-energy-corrected"
STARTING_COMMIT = "08e675e2039d76f16b8c9576e4b5a8254bc44d72"


def load_manifest() -> dict[str, Any]:
    bundle = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for_hash = copy.deepcopy(bundle)
    claimed = for_hash.pop("manifest_sha256", None)
    if claimed != semantic_hash(for_hash):
        raise store.StoreSafetyError("corrected commissioning manifest SHA-256 mismatch")
    if bundle.get("deterministic_batch_key") != BATCH_KEY:
        raise store.StoreSafetyError("corrected commissioning batch identity mismatch")
    if bundle.get("starting_commit") != STARTING_COMMIT:
        raise store.StoreSafetyError("corrected commissioning source commit mismatch")
    artifacts = bundle.get("artifacts", [])
    relationships = bundle.get("relationships", [])
    if {item.get("artifact_type") for item in artifacts} != set(ARTIFACT_TYPES):
        raise store.StoreSafetyError("corrected artifact taxonomy is incomplete")
    natural_keys = {item.get("natural_key") for item in artifacts}
    if len(natural_keys) != len(artifacts):
        raise store.StoreSafetyError("corrected manifest has duplicate natural keys")
    if any("commissioning-v1-corrected" not in key for key in natural_keys):
        raise store.StoreSafetyError("corrected manifest reuses an original natural key")
    for item in artifacts:
        if item.get("content_sha256") != semantic_hash(item.get("payload")):
            raise store.StoreSafetyError(
                f"content hash mismatch: {item.get('natural_key')}"
            )
        if (
            item.get("editorial_status") != "human_approval_pending"
            or item.get("benchmark_status") != "not_promoted"
            or item.get("production_eligible") is not False
        ):
            raise store.StoreSafetyError(
                "corrected artifact crosses publication boundary"
            )
    for relationship in relationships:
        if (
            relationship.get("parent_natural_key") not in natural_keys
            or relationship.get("child_natural_key") not in natural_keys
        ):
            raise store.StoreSafetyError(
                "corrected manifest has an orphan relationship"
            )
    expected = bundle.get("expected_counts", {})
    if (
        expected.get("artifacts") != len(artifacts)
        or expected.get("relationships") != len(relationships)
        or bundle.get("publication_registry_expected_rows") != 0
    ):
        raise store.StoreSafetyError(
            "corrected manifest count or publication boundary mismatch"
        )
    return bundle


def main(argv: list[str] | None = None) -> int:
    store.BATCH_KEY = BATCH_KEY
    store.STARTING_COMMIT = STARTING_COMMIT
    store.MANIFEST = MANIFEST
    store.REPORT = (
        ROOT
        / "docs/review_packets/commissioning_domain_v1_corrected_persistence.json"
    )
    store.LOCK_KEY = "political_fingerprint:commissioning_domain_v1_corrected"
    store.load_manifest = load_manifest
    return store.main(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except store.StoreSafetyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
