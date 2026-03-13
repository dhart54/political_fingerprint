BEGIN;

CREATE TYPE chamber AS ENUM ('house', 'senate');

CREATE TYPE vote_position AS ENUM ('yea', 'nay', 'present', 'not_voting');

CREATE TYPE issue_domain AS ENUM (
    'ECONOMY_TAXES',
    'HEALTH_SOCIAL',
    'EDUCATION_WORKFORCE',
    'ENVIRONMENT_ENERGY',
    'NATIONAL_SECURITY_FOREIGN',
    'IMMIGRATION_BORDER',
    'JUSTICE_PUBLIC_SAFETY',
    'INFRASTRUCTURE_TECH_TRANSPORT'
);

CREATE TABLE legislators (
    id BIGSERIAL PRIMARY KEY,
    bioguide_id TEXT NOT NULL UNIQUE,
    name_display TEXT NOT NULL,
    chamber chamber NOT NULL,
    state TEXT NOT NULL,
    district TEXT,
    party TEXT NOT NULL,
    in_office BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE bills (
    id BIGSERIAL PRIMARY KEY,
    congress INTEGER NOT NULL,
    bill_type TEXT NOT NULL,
    bill_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    committee TEXT,
    subjects JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (congress, bill_type, bill_number)
);

CREATE TABLE roll_calls (
    id BIGSERIAL PRIMARY KEY,
    chamber chamber NOT NULL,
    congress INTEGER NOT NULL,
    rollcall_number INTEGER NOT NULL,
    vote_date TIMESTAMPTZ NOT NULL,
    question TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    bill_id BIGINT REFERENCES bills(id) ON DELETE SET NULL,
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chamber, congress, rollcall_number)
);

CREATE TABLE votes_cast (
    id BIGSERIAL PRIMARY KEY,
    roll_call_id BIGINT NOT NULL REFERENCES roll_calls(id) ON DELETE CASCADE,
    legislator_id BIGINT NOT NULL REFERENCES legislators(id) ON DELETE CASCADE,
    position vote_position NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (roll_call_id, legislator_id)
);

CREATE TABLE vote_classifications (
    roll_call_id BIGINT PRIMARY KEY REFERENCES roll_calls(id) ON DELETE CASCADE,
    is_eligible BOOLEAN NOT NULL,
    eligibility_reason TEXT NOT NULL,
    primary_domain issue_domain,
    score_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    classification_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (is_eligible = TRUE AND primary_domain IS NOT NULL)
        OR (is_eligible = FALSE AND primary_domain IS NULL)
    )
);

CREATE TABLE fingerprints (
    id BIGSERIAL PRIMARY KEY,
    legislator_id BIGINT NOT NULL REFERENCES legislators(id) ON DELETE CASCADE,
    window_start DATE NOT NULL,
    window_end DATE NOT NULL,
    classification_version TEXT NOT NULL,
    domain issue_domain NOT NULL,
    vote_count INTEGER NOT NULL DEFAULT 0 CHECK (vote_count >= 0),
    total_votes INTEGER NOT NULL DEFAULT 0 CHECK (total_votes >= 0),
    vote_share DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (vote_share >= 0 AND vote_share <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (legislator_id, window_start, window_end, classification_version, domain)
);

CREATE TABLE chamber_medians (
    id BIGSERIAL PRIMARY KEY,
    chamber chamber NOT NULL,
    party TEXT NOT NULL CHECK (party IN ('ALL', 'D', 'R')),
    window_start DATE NOT NULL,
    window_end DATE NOT NULL,
    classification_version TEXT NOT NULL,
    domain issue_domain NOT NULL,
    legislator_count INTEGER NOT NULL DEFAULT 0 CHECK (legislator_count >= 0),
    median_share DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (median_share >= 0 AND median_share <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chamber, party, window_start, window_end, classification_version, domain)
);

CREATE TABLE drift_scores (
    id BIGSERIAL PRIMARY KEY,
    legislator_id BIGINT NOT NULL REFERENCES legislators(id) ON DELETE CASCADE,
    window_start DATE NOT NULL,
    window_end DATE NOT NULL,
    early_window_start DATE NOT NULL,
    early_window_end DATE NOT NULL,
    recent_window_start DATE NOT NULL,
    recent_window_end DATE NOT NULL,
    classification_version TEXT NOT NULL,
    total_votes INTEGER NOT NULL DEFAULT 0 CHECK (total_votes >= 0),
    early_total_votes INTEGER NOT NULL DEFAULT 0 CHECK (early_total_votes >= 0),
    recent_total_votes INTEGER NOT NULL DEFAULT 0 CHECK (recent_total_votes >= 0),
    insufficient_data BOOLEAN NOT NULL DEFAULT FALSE,
    drift_value DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (drift_value IS NULL OR (drift_value >= 0 AND drift_value <= 1)),
    CHECK (
        (insufficient_data = TRUE AND drift_value IS NULL)
        OR (insufficient_data = FALSE AND drift_value IS NOT NULL)
    ),
    UNIQUE (legislator_id, window_start, window_end, classification_version)
);

CREATE TABLE summaries (
    id BIGSERIAL PRIMARY KEY,
    legislator_id BIGINT NOT NULL REFERENCES legislators(id) ON DELETE CASCADE,
    window_end DATE NOT NULL,
    classification_version TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    generation_method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (legislator_id, window_end, classification_version)
);

CREATE TABLE zip_district_map (
    zip TEXT PRIMARY KEY CHECK (zip ~ '^[0-9]{5}$'),
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_roll_calls_vote_date ON roll_calls (vote_date);
CREATE INDEX idx_votes_cast_legislator_id ON votes_cast (legislator_id);
CREATE INDEX idx_vote_classifications_primary_domain ON vote_classifications (primary_domain);
CREATE INDEX idx_fingerprints_lookup
    ON fingerprints (legislator_id, window_end, classification_version, domain);
CREATE INDEX idx_chamber_medians_lookup
    ON chamber_medians (chamber, party, window_end, classification_version, domain);
CREATE INDEX idx_drift_scores_lookup
    ON drift_scores (legislator_id, window_end, classification_version);
CREATE INDEX idx_summaries_lookup
    ON summaries (legislator_id, window_end, classification_version);
CREATE INDEX idx_legislators_state_chamber ON legislators (state, chamber);

COMMIT;
