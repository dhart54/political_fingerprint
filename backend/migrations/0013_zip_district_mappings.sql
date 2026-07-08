BEGIN;

-- Additive candidate schema for source-backed, multi-row ZIP mappings.
-- This migration is not applied by application startup; production application
-- requires an explicit bounded migration step in a later milestone.

CREATE TABLE IF NOT EXISTS zip_district_mappings (
    id BIGSERIAL PRIMARY KEY,
    zip TEXT NOT NULL CHECK (zip ~ '^[0-9]{5}$'),
    state TEXT NOT NULL CHECK (state ~ '^[A-Z]{2}$'),
    district TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_retrieved_at DATE NOT NULL,
    source_effective_date DATE NOT NULL,
    source_version TEXT NOT NULL,
    source_currentness TEXT NOT NULL CHECK (
        source_currentness IN ('current', 'stale_or_unknown', 'fixture_sample', 'unsupported', 'expired')
    ),
    confidence TEXT NOT NULL CHECK (
        confidence IN ('source_backed', 'reviewed', 'inferred', 'low', 'unknown')
    ),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    district_type TEXT NOT NULL DEFAULT 'house' CHECK (
        district_type IN ('house', 'delegate', 'resident_commissioner', 'at_large')
    ),
    congress INTEGER,
    cycle TEXT,
    valid_from DATE,
    valid_to DATE,
    provider_record_id TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_zip_district_mappings_active_source_period_unique
    ON zip_district_mappings (
        zip,
        state,
        district,
        source_name,
        source_version,
        COALESCE(valid_from, source_effective_date),
        COALESCE(valid_to, DATE '9999-12-31')
    );

CREATE INDEX IF NOT EXISTS idx_zip_district_mappings_zip
    ON zip_district_mappings (zip);

CREATE INDEX IF NOT EXISTS idx_zip_district_mappings_zip_state_district
    ON zip_district_mappings (zip, state, district);

CREATE INDEX IF NOT EXISTS idx_zip_district_mappings_source_currentness
    ON zip_district_mappings (source_currentness);

CREATE INDEX IF NOT EXISTS idx_zip_district_mappings_source_name
    ON zip_district_mappings (source_name);

CREATE INDEX IF NOT EXISTS idx_zip_district_mappings_source_version
    ON zip_district_mappings (source_version);

COMMIT;
