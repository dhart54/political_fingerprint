BEGIN;

ALTER TABLE roll_calls
    ADD COLUMN IF NOT EXISTS session INTEGER;

CREATE TABLE IF NOT EXISTS vote_contexts (
    roll_call_id BIGINT NOT NULL REFERENCES roll_calls(id) ON DELETE CASCADE,
    legislator_id BIGINT NOT NULL REFERENCES legislators(id) ON DELETE CASCADE,
    chamber_session INTEGER,
    vote_type TEXT NOT NULL CHECK (
        vote_type IN (
            'final_passage',
            'amendment',
            'rule',
            'motion',
            'concurrence',
            'procedural',
            'nomination',
            'appropriations',
            'cra_disapproval',
            'other'
        )
    ),
    member_position vote_position NOT NULL,
    final_result TEXT NOT NULL CHECK (
        final_result IN ('passed', 'failed', 'no_yea_nay_majority')
    ),
    vote_margin INTEGER NOT NULL CHECK (vote_margin >= 0),
    winning_position vote_position,
    party_vote_totals JSONB NOT NULL DEFAULT '{}'::jsonb,
    member_party TEXT NOT NULL,
    member_party_majority_position vote_position,
    member_voted_with_party_majority BOOLEAN,
    member_voted_with_winning_side BOOLEAN,
    bipartisan_majority BOOLEAN NOT NULL DEFAULT FALSE,
    sponsor_party TEXT,
    context_source_list JSONB NOT NULL DEFAULT '[]'::jsonb,
    context_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (roll_call_id, legislator_id)
);

CREATE INDEX IF NOT EXISTS idx_vote_contexts_legislator
    ON vote_contexts (legislator_id);

CREATE INDEX IF NOT EXISTS idx_vote_contexts_vote_type
    ON vote_contexts (vote_type);

CREATE INDEX IF NOT EXISTS idx_vote_contexts_party_result
    ON vote_contexts (member_voted_with_party_majority, member_voted_with_winning_side);

COMMIT;
