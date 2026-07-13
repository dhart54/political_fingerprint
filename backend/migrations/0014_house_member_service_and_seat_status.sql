BEGIN;

-- Additive candidate schema only. This milestone does not apply this migration.
CREATE TABLE IF NOT EXISTS house_member_metadata_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    congress INTEGER NOT NULL CHECK (congress > 0),
    retrieval_started_at TIMESTAMPTZ NOT NULL,
    retrieval_completed_at TIMESTAMPTZ NOT NULL,
    parser_version TEXT NOT NULL,
    snapshot_status TEXT NOT NULL CHECK (snapshot_status IN ('complete', 'stale', 'source_conflict', 'rejected')),
    manifest_checksum TEXT NOT NULL CHECK (manifest_checksum ~ '^[0-9a-f]{64}$'),
    source_decision TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS house_member_metadata_snapshot_artifacts (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES house_member_metadata_snapshots(snapshot_id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    http_status INTEGER NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    sha256 TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    UNIQUE (snapshot_id, artifact_path)
);

CREATE TABLE IF NOT EXISTS house_member_service_evidence (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES house_member_metadata_snapshots(snapshot_id) ON DELETE CASCADE,
    legislator_id BIGINT REFERENCES legislators(id) ON DELETE SET NULL,
    bioguide_id TEXT NOT NULL,
    congress INTEGER NOT NULL CHECK (congress > 0),
    chamber TEXT NOT NULL CHECK (chamber = 'house'),
    canonical_state TEXT NOT NULL CHECK (canonical_state ~ '^[A-Z]{2}$'),
    canonical_district TEXT NOT NULL CHECK (canonical_district ~ '^[0-9]{2}$'),
    source_state TEXT NOT NULL,
    source_district TEXT NOT NULL,
    normalization_rule TEXT NOT NULL,
    member_type TEXT NOT NULL CHECK (member_type IN ('voting_representative', 'delegate', 'resident_commissioner')),
    current_member BOOLEAN NOT NULL,
    service_start_year INTEGER,
    service_end_year INTEGER,
    service_date_precision TEXT NOT NULL CHECK (service_date_precision = 'year'),
    party TEXT,
    official_url TEXT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_update_date TIMESTAMPTZ,
    source_retrieved_at TIMESTAMPTZ NOT NULL,
    source_checksum TEXT NOT NULL CHECK (source_checksum ~ '^[0-9a-f]{64}$'),
    parser_version TEXT NOT NULL,
    metadata_currentness TEXT NOT NULL CHECK (metadata_currentness IN ('current_cross_source_confirmed', 'current_primary_source_only', 'vacant_officially_confirmed', 'source_conflict', 'stale_snapshot', 'unknown', 'parser_or_layout_unverified')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (snapshot_id, bioguide_id, congress, canonical_state, canonical_district),
    CHECK (service_end_year IS NULL OR service_start_year IS NULL OR service_end_year >= service_start_year)
);

CREATE TABLE IF NOT EXISTS house_seat_status_evidence (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES house_member_metadata_snapshots(snapshot_id) ON DELETE CASCADE,
    congress INTEGER NOT NULL CHECK (congress > 0),
    canonical_state TEXT NOT NULL CHECK (canonical_state ~ '^[A-Z]{2}$'),
    canonical_district TEXT NOT NULL CHECK (canonical_district ~ '^[0-9]{2}$'),
    source_state TEXT NOT NULL,
    source_district TEXT NOT NULL,
    normalization_rule TEXT NOT NULL,
    seat_type TEXT NOT NULL CHECK (seat_type IN ('voting_district', 'voting_at_large', 'delegate', 'resident_commissioner')),
    seat_status TEXT NOT NULL CHECK (seat_status IN ('filled', 'vacant', 'source_conflict', 'unknown')),
    current_legislator_id BIGINT REFERENCES legislators(id) ON DELETE SET NULL,
    current_bioguide_id TEXT,
    vacancy_reason TEXT,
    vacancy_effective_date DATE,
    successor_election_date DATE,
    oath_date DATE,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_retrieved_at TIMESTAMPTZ NOT NULL,
    source_checksum TEXT NOT NULL CHECK (source_checksum ~ '^[0-9a-f]{64}$'),
    parser_version TEXT NOT NULL,
    metadata_currentness TEXT NOT NULL CHECK (metadata_currentness IN ('current_cross_source_confirmed', 'current_primary_source_only', 'vacant_officially_confirmed', 'source_conflict', 'stale_snapshot', 'unknown', 'parser_or_layout_unverified')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (snapshot_id, congress, canonical_state, canonical_district),
    CHECK ((seat_status <> 'vacant') OR (current_legislator_id IS NULL AND current_bioguide_id IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_house_member_service_seat
    ON house_member_service_evidence (congress, canonical_state, canonical_district);

COMMIT;
