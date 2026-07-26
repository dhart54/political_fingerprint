from __future__ import annotations

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
                 AND artifact.benchmark_status = 'promoted'
                 AND artifact.production_eligible = TRUE
               ORDER BY registry.member_bioguide_id, registry.issue_id""",
        )

    def _one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        row = self.connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def _all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(query, params).fetchall()]
