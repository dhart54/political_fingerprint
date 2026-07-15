BEGIN;

-- Unapplied additive candidate. Immutable source evidence is separate from
-- versioned policy evaluation and any future runtime materialization.
CREATE TABLE IF NOT EXISTS zip_mapping_source_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    congress INTEGER NOT NULL CHECK (congress > 0),
    zcta_vintage INTEGER NOT NULL CHECK (zcta_vintage > 0),
    parser_version TEXT NOT NULL,
    source_status TEXT NOT NULL CHECK (source_status IN ('complete', 'rejected')),
    manifest_sha256 TEXT NOT NULL CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS zip_mapping_source_artifacts (
    artifact_id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES zip_mapping_source_snapshots(snapshot_id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    sha256 TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    retrieved_at TIMESTAMPTZ,
    UNIQUE (snapshot_id, artifact_id),
    UNIQUE (snapshot_id, sha256),
    UNIQUE (snapshot_id, file_name)
);

CREATE TABLE IF NOT EXISTS zip_district_relationship_evidence (
    relationship_id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES zip_mapping_source_snapshots(snapshot_id) ON DELETE CASCADE,
    artifact_id BIGINT NOT NULL,
    source_line_number INTEGER NOT NULL CHECK (source_line_number >= 2),
    zcta TEXT NOT NULL CHECK (zcta ~ '^[0-9]{5}$'),
    source_congressional_geoid TEXT NOT NULL,
    canonical_source_state TEXT NOT NULL CHECK (canonical_source_state ~ '^[A-Z]{2}$'),
    source_district TEXT NOT NULL CHECK (source_district ~ '^[0-9]{2}$'),
    arealand_zcta5_20 BIGINT NOT NULL CHECK (arealand_zcta5_20 >= 0),
    areawater_zcta5_20 BIGINT NOT NULL CHECK (areawater_zcta5_20 >= 0),
    arealand_part BIGINT NOT NULL CHECK (arealand_part >= 0),
    areawater_part BIGINT NOT NULL CHECK (areawater_part >= 0),
    land_share_numerator BIGINT,
    land_share_denominator BIGINT,
    water_share_numerator BIGINT,
    water_share_denominator BIGINT,
    total_share_numerator BIGINT,
    total_share_denominator BIGINT,
    candidate_normalization_rule TEXT,
    candidate_canonical_state TEXT,
    candidate_canonical_district TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (snapshot_id, source_line_number),
    UNIQUE (snapshot_id, zcta, source_congressional_geoid),
    UNIQUE (snapshot_id, relationship_id),
    FOREIGN KEY (snapshot_id, artifact_id)
        REFERENCES zip_mapping_source_artifacts(snapshot_id, artifact_id)
        ON DELETE CASCADE,
    CHECK ((land_share_numerator IS NULL) = (land_share_denominator IS NULL)),
    CHECK (land_share_denominator IS NULL OR land_share_denominator > 0),
    CHECK ((water_share_numerator IS NULL) = (water_share_denominator IS NULL)),
    CHECK (water_share_denominator IS NULL OR water_share_denominator > 0),
    CHECK ((total_share_numerator IS NULL) = (total_share_denominator IS NULL)),
    CHECK (total_share_denominator IS NULL OR total_share_denominator > 0),
    CHECK ((candidate_normalization_rule IS NULL) = (candidate_canonical_state IS NULL)),
    CHECK ((candidate_normalization_rule IS NULL) = (candidate_canonical_district IS NULL))
);

CREATE TABLE IF NOT EXISTS zip_mapping_policy_evaluations (
    evaluation_id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES zip_mapping_source_snapshots(snapshot_id) ON DELETE CASCADE,
    relationship_id BIGINT NOT NULL,
    policy_version TEXT NOT NULL,
    policy_definition_sha256 TEXT NOT NULL CHECK (policy_definition_sha256 ~ '^[0-9a-f]{64}$'),
    relationship_survives BOOLEAN NOT NULL,
    presentation_rank INTEGER CHECK (presentation_rank IS NULL OR presentation_rank > 0),
    low_material_overlap BOOLEAN,
    seat_snapshot_id TEXT REFERENCES house_member_metadata_snapshots(snapshot_id) ON DELETE RESTRICT,
    seat_classification TEXT NOT NULL CHECK (seat_classification IN (
        'filled_current_voting_seat',
        'filled_current_delegate',
        'current_resident_commissioner',
        'officially_vacant',
        'candidate_dc_normalization',
        'no_seeded_seat_match',
        'source_conflict',
        'unsupported_territory'
    )),
    auto_select_eligible BOOLEAN NOT NULL DEFAULT FALSE CHECK (auto_select_eligible = FALSE),
    evaluated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (snapshot_id, relationship_id, policy_version),
    FOREIGN KEY (snapshot_id, relationship_id)
        REFERENCES zip_district_relationship_evidence(snapshot_id, relationship_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_zip_mapping_source_artifacts_snapshot
    ON zip_mapping_source_artifacts (snapshot_id);

CREATE INDEX IF NOT EXISTS idx_zip_relationship_evidence_zcta
    ON zip_district_relationship_evidence (snapshot_id, zcta);

CREATE INDEX IF NOT EXISTS idx_zip_relationship_evidence_pair
    ON zip_district_relationship_evidence (snapshot_id, canonical_source_state, source_district);

CREATE INDEX IF NOT EXISTS idx_zip_policy_evaluations_policy
    ON zip_mapping_policy_evaluations (snapshot_id, policy_version, relationship_survives);

COMMIT;
