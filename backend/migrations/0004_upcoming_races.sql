CREATE TABLE IF NOT EXISTS upcoming_races (
    id BIGSERIAL PRIMARY KEY,
    race_key TEXT NOT NULL UNIQUE,
    election_date DATE NOT NULL,
    election_label TEXT NOT NULL,
    office_level TEXT NOT NULL CHECK (office_level IN ('federal', 'state', 'local')),
    office_name TEXT NOT NULL,
    chamber chamber,
    state TEXT NOT NULL,
    district TEXT,
    status TEXT NOT NULL CHECK (status IN ('upcoming', 'active', 'past')),
    source_url TEXT,
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_retrieved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upcoming_races_lookup
    ON upcoming_races (office_level, chamber, state, district, election_date);

CREATE TABLE IF NOT EXISTS race_candidates (
    id BIGSERIAL PRIMARY KEY,
    race_id BIGINT NOT NULL REFERENCES upcoming_races(id) ON DELETE CASCADE,
    candidate_name TEXT NOT NULL,
    party TEXT,
    incumbent BOOLEAN NOT NULL DEFAULT FALSE,
    legislator_id BIGINT REFERENCES legislators(id) ON DELETE SET NULL,
    candidate_status TEXT NOT NULL CHECK (
        candidate_status IN (
            'declared_candidate',
            'filed_candidate',
            'current_official_context',
            'unknown'
        )
    ),
    evidence_tier TEXT NOT NULL CHECK (
        evidence_tier IN (
            'recorded_governing_behavior',
            'institutional_record',
            'sourced_stated_position',
            'insufficient_evidence'
        )
    ),
    evidence_note TEXT,
    source_url TEXT,
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_retrieved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_race_candidates_race_id
    ON race_candidates (race_id);
