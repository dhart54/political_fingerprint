from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "backend/migrations/0016_editorial_artifact_persistence.sql"
TABLES = {
    "editorial_artifact_batches",
    "editorial_artifact_versions",
    "editorial_artifact_relationships",
    "editorial_publication_registry",
}
FUNCTIONS = {
    "guard_editorial_artifact_immutability",
    "guard_editorial_publication_activation",
}
MIGRATION_SHA256 = hashlib.sha256(MIGRATION.read_bytes()).hexdigest()


class MigrationSafetyError(RuntimeError):
    pass


def strip_transaction_wrappers(sql: str) -> str:
    lines = sql.strip().splitlines()
    if not lines or lines[0].strip().upper() != "BEGIN;" or lines[-1].strip().upper() != "COMMIT;":
        raise MigrationSafetyError("migration requires exact BEGIN/COMMIT wrappers")
    return "\n".join(lines[1:-1])


def validate_migration(expected_sha256: str = MIGRATION_SHA256) -> dict[str, Any]:
    actual = hashlib.sha256(MIGRATION.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise MigrationSafetyError(f"migration SHA-256 mismatch: expected {expected_sha256}, got {actual}")
    sql = MIGRATION.read_text(encoding="utf-8")
    body = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.M | re.S).lower()
    if re.search(
        r"\bdrop\s+(?:table|function|index|schema|type)\b"
        r"|\btruncate\b"
        r"|\bupdate\s+[\w.]+\s+set\b"
        r"|\bdelete\s+from\b"
        r"|create\s+extension",
        body,
    ):
        raise MigrationSafetyError("migration contains a forbidden statement class")
    created_tables = set(re.findall(r"create\s+table\s+(?:public\.)?(\w+)", body))
    created_functions = set(re.findall(r"create\s+function\s+(?:public\.)?(\w+)", body))
    if created_tables != TABLES or created_functions != FUNCTIONS:
        raise MigrationSafetyError("migration creates objects outside the approved contract")
    altered = set(re.findall(r"alter\s+table\s+(?:public\.)?(\w+)", body))
    if not altered <= TABLES:
        raise MigrationSafetyError("migration alters an unrelated table")
    if re.search(r"\bgrant\b", body) or "disable row level security" in body:
        raise MigrationSafetyError("migration grants access or disables RLS")
    for required in (
        "editorial_artifact_versions_immutable",
        "editorial_publication_registry_fail_closed",
        "enable row level security",
        "revoke all privileges",
        "unique (natural_key, artifact_version)",
        "content_sha256",
        "supersedes_artifact_id",
    ):
        if required not in body:
            raise MigrationSafetyError(f"migration lacks required contract: {required}")
    if re.search(r"\b(frontend|route|api)\b", body):
        raise MigrationSafetyError("migration references a runtime surface")
    strip_transaction_wrappers(sql)
    return {
        "identifier": "0016",
        "path": MIGRATION.relative_to(ROOT).as_posix(),
        "sha256": actual,
        "tables": sorted(TABLES),
        "functions": sorted(FUNCTIONS),
        "additive": True,
    }
