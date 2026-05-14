BEGIN;

CREATE TYPE vote_interpretation_status AS ENUM (
    'interpreted',
    'ambiguous',
    'insufficient_evidence'
);

CREATE TABLE vote_interpretations (
    roll_call_id BIGINT PRIMARY KEY REFERENCES roll_calls(id) ON DELETE CASCADE,
    interpretation_status vote_interpretation_status NOT NULL,
    support_position vote_position,
    oppose_position vote_position,
    interpretation_reason TEXT NOT NULL,
    source_url TEXT,
    interpretation_version TEXT NOT NULL,
    classification_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (
            interpretation_status = 'interpreted'
            AND support_position IS NOT NULL
            AND oppose_position IS NOT NULL
            AND support_position <> oppose_position
        )
        OR (
            interpretation_status IN ('ambiguous', 'insufficient_evidence')
            AND support_position IS NULL
            AND oppose_position IS NULL
        )
    )
);

CREATE INDEX idx_vote_interpretations_status
    ON vote_interpretations (interpretation_status);

CREATE INDEX idx_vote_interpretations_version
    ON vote_interpretations (interpretation_version, classification_version);

COMMIT;
