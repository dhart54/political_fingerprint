-- Observation only. Never an activation authority or execution preflight.
-- Project: yalpfkaxkxebwolhorha. Queries contain no mutation or source acquisition.
BEGIN TRANSACTION READ ONLY;
SELECT to_jsonb(r) AS registry, to_jsonb(a) AS artifact
FROM editorial_publication_registry r
JOIN editorial_artifact_versions a USING (artifact_id)
WHERE r.member_bioguide_id = 'F000477' AND r.issue_id = 'EDUCATION_WORKFORCE';
SELECT rel.relationship_type, rel.ordinal, rel.metadata_jsonb,
       a.artifact_id, a.artifact_type, a.natural_key, a.artifact_version,
       a.content_sha256, a.payload_jsonb
FROM editorial_artifact_relationships rel
JOIN editorial_artifact_versions a ON a.artifact_id = rel.child_artifact_id
WHERE rel.parent_artifact_id = (
    SELECT artifact_id FROM editorial_publication_registry
    WHERE member_bioguide_id = 'F000477' AND issue_id = 'EDUCATION_WORKFORCE'
);
SELECT artifact_id, natural_key, artifact_version, content_sha256
FROM editorial_artifact_versions
WHERE natural_key IN (
    'public-issue-presentation:f000477:education_workforce:record-locator:v1',
    'public-issue-presentation:f000477:education_workforce:record-locator:v1:source',
    'public-issue-presentation:f000477:education_workforce:record-locator:v1:validation'
);
COMMIT;
