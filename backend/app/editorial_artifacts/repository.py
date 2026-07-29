from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class EditorialArtifactRepository:
    """Internal-only reads for immutable editorial artifacts."""

    def __init__(self, connection: Any):
        self.connection = connection

    def get_by_id(self, artifact_id: int) -> dict[str, Any] | None:
        return self._one(
            "SELECT * FROM editorial_artifact_versions WHERE artifact_id = %s",
            (artifact_id,),
        )

    def get_version(self, natural_key: str, artifact_version: int) -> dict[str, Any] | None:
        return self._one(
            """SELECT * FROM editorial_artifact_versions
               WHERE natural_key = %s AND artifact_version = %s""",
            (natural_key, artifact_version),
        )

    def get_latest(self, natural_key: str) -> dict[str, Any] | None:
        return self._one(
            """SELECT * FROM editorial_artifact_versions
               WHERE natural_key = %s
               ORDER BY artifact_version DESC LIMIT 1""",
            (natural_key,),
        )

    def list_versions(self, natural_key: str) -> list[dict[str, Any]]:
        return self._all(
            """SELECT * FROM editorial_artifact_versions
               WHERE natural_key = %s ORDER BY artifact_version""",
            (natural_key,),
        )

    def load_graph(self, artifact_id: int) -> dict[str, Any] | None:
        root = self.get_by_id(artifact_id)
        if root is None:
            return None
        root["relationships"] = self._all(
            """WITH RECURSIVE graph AS (
                 SELECT r.*, 1 AS depth
                 FROM editorial_artifact_relationships r
                 WHERE r.parent_artifact_id = %s
                 UNION
                 SELECT child.*, graph.depth + 1
                 FROM editorial_artifact_relationships child
                 JOIN graph ON child.parent_artifact_id = graph.child_artifact_id
                 WHERE graph.depth < 32
               )
               SELECT graph.*, artifact.natural_key AS child_natural_key,
                      artifact.artifact_version AS child_artifact_version
               FROM graph
               JOIN editorial_artifact_versions artifact
                 ON artifact.artifact_id = graph.child_artifact_id
               ORDER BY graph.depth, graph.ordinal, artifact.natural_key""",
            (artifact_id,),
        )
        return root

    def list_pending_slices(self) -> list[dict[str, Any]]:
        return self._all(
            """SELECT * FROM editorial_artifact_versions
               WHERE artifact_type = 'issue_public_presentation'
                 AND editorial_status = 'human_approval_pending'
                 AND benchmark_status = 'not_promoted'
                 AND production_eligible = FALSE
               ORDER BY member_bioguide_id, issue_id, artifact_version""",
        )

    def get_slice_candidate(self, member_bioguide_id: str, issue_id: str) -> dict[str, Any] | None:
        return self._one(
            """SELECT * FROM editorial_artifact_versions
               WHERE artifact_type = 'issue_public_presentation'
                 AND member_bioguide_id = %s AND issue_id = %s
               ORDER BY artifact_version DESC LIMIT 1""",
            (member_bioguide_id, issue_id),
        )

    def get_shared_evidence(self, issue_id: str) -> list[dict[str, Any]]:
        return self._all(
            """SELECT * FROM editorial_artifact_versions
               WHERE issue_id = %s
                 AND member_bioguide_id IS NULL
                 AND artifact_type IN ('shared_action_dossier', 'policy_episode')
               ORDER BY artifact_type, natural_key, artifact_version""",
            (issue_id,),
        )

    def get_latest_validation(self, member_bioguide_id: str, issue_id: str) -> dict[str, Any] | None:
        return self._one(
            """SELECT * FROM editorial_artifact_versions
               WHERE artifact_type = 'standardization_validation_result'
                 AND member_bioguide_id = %s AND issue_id = %s
               ORDER BY artifact_version DESC LIMIT 1""",
            (member_bioguide_id, issue_id),
        )

    def publication_selector(self) -> list[dict[str, Any]]:
        return self._all(
            """SELECT registry.*, artifact.payload_jsonb, artifact.content_sha256,
                      artifact.editorial_status, artifact.benchmark_status,
                      artifact.production_eligible, artifact.schema_version,
                      artifact.artifact_version, artifact.natural_key
               FROM editorial_publication_registry registry
               JOIN editorial_artifact_versions artifact
                 ON artifact.artifact_id = registry.artifact_id
               WHERE registry.publicly_active = TRUE
                 AND registry.deactivated_at IS NULL
                 AND artifact.editorial_status = 'human_approved'
                 AND artifact.benchmark_status = 'gold_benchmark'
                 AND artifact.production_eligible = TRUE
                 AND artifact.natural_key =
                   registry.publication_metadata_jsonb->>'presentation_natural_key'
                 AND artifact.artifact_version = CAST(
                   registry.publication_metadata_jsonb->>'presentation_artifact_version'
                   AS INTEGER)
                 AND artifact.content_sha256 =
                   registry.publication_metadata_jsonb->>'active_artifact_sha256'
                 AND (
                   SELECT COUNT(*)
                   FROM editorial_artifact_relationships rel
                   JOIN editorial_artifact_versions child
                     ON child.artifact_id = rel.child_artifact_id
                   WHERE rel.parent_artifact_id = artifact.artifact_id
                     AND rel.relationship_type = 'has_validation'
                     AND rel.ordinal = 0
                     AND rel.metadata_jsonb =
                       registry.publication_metadata_jsonb->'relationship_metadata'
                     AND child.artifact_type =
                       'standardization_validation_result'
                     AND child.natural_key =
                       registry.publication_metadata_jsonb->>'validation_natural_key'
                     AND child.artifact_version = CAST(
                       registry.publication_metadata_jsonb->>'validation_artifact_version'
                       AS INTEGER)
                     AND child.content_sha256 =
                       registry.publication_metadata_jsonb->>'validation_content_sha256'
                 ) = 1
                 AND (
                   SELECT COUNT(*)
                   FROM editorial_artifact_relationships rel
                   WHERE rel.parent_artifact_id = artifact.artifact_id
                     AND rel.relationship_type = 'has_validation'
                 ) = 1
                 AND (
                   SELECT COUNT(*)
                   FROM editorial_artifact_relationships rel
                   JOIN editorial_artifact_versions child
                     ON child.artifact_id = rel.child_artifact_id
                   WHERE rel.parent_artifact_id = artifact.artifact_id
                     AND rel.relationship_type = 'uses_source_manifest'
                     AND rel.ordinal = 0
                     AND rel.metadata_jsonb =
                       registry.publication_metadata_jsonb->'relationship_metadata'
                     AND child.artifact_type = 'source_manifest'
                     AND child.natural_key =
                       registry.publication_metadata_jsonb->>'source_manifest_natural_key'
                     AND child.artifact_version = CAST(
                       registry.publication_metadata_jsonb->>'source_manifest_artifact_version'
                       AS INTEGER)
                     AND child.content_sha256 =
                       registry.publication_metadata_jsonb->>'source_manifest_content_sha256'
                 ) = 1
                 AND (
                   SELECT COUNT(*)
                   FROM editorial_artifact_relationships rel
                   WHERE rel.parent_artifact_id = artifact.artifact_id
                     AND rel.relationship_type = 'uses_source_manifest'
                 ) = 1
               ORDER BY registry.member_bioguide_id, registry.issue_id""",
        )

    def _one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        cursor = self.connection.execute(query, params)
        row = cursor.fetchone()
        return self._row_to_dict(cursor, row) if row is not None else None

    def _all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        cursor = self.connection.execute(query, params)
        return [self._row_to_dict(cursor, row) for row in cursor.fetchall()]

    @staticmethod
    def _row_to_dict(cursor: Any, row: Any) -> dict[str, Any]:
        """Normalize only explicit mapping and DB-API sequence row contracts."""

        if isinstance(row, Mapping):
            keys = list(row.keys())
            EditorialArtifactRepository._validate_column_names(
                keys, source="mapping row"
            )
            return dict(row)

        if isinstance(row, (str, bytes, bytearray, memoryview)) or not isinstance(
            row, Sequence
        ):
            raise TypeError(
                "database row must be a mapping or a non-string sequence"
            )
        description = getattr(cursor, "description", None)
        if description is None:
            raise TypeError("database cursor did not provide row metadata")
        if isinstance(description, (str, bytes, bytearray, memoryview)) or not isinstance(
            description, Sequence
        ):
            raise TypeError("database cursor description must be a sequence")
        columns = [
            EditorialArtifactRepository._description_column_name(column)
            for column in description
        ]
        EditorialArtifactRepository._validate_column_names(
            columns, source="cursor description"
        )
        if len(columns) != len(row):
            raise ValueError("database row width does not match its column description")
        return dict(zip(columns, row, strict=True))

    @staticmethod
    def _description_column_name(column: Any) -> Any:
        if isinstance(column, (tuple, list)):
            if not column:
                raise TypeError(
                    "database cursor returned an empty column description"
                )
            return column[0]
        try:
            return column.name
        except AttributeError as exc:
            raise TypeError(
                "database cursor column metadata must expose name or be a DB-API sequence"
            ) from exc

    @staticmethod
    def _validate_column_names(names: Sequence[Any], *, source: str) -> None:
        seen: set[str] = set()
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(f"{source} contains a non-string or blank column name")
            if name in seen:
                raise ValueError(f"{source} contains duplicate column name {name!r}")
            seen.add(name)
