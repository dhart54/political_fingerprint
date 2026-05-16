BEGIN;

ALTER TABLE vote_interpretations
    ADD COLUMN plain_english_summary TEXT,
    ADD COLUMN yea_meaning TEXT,
    ADD COLUMN nay_meaning TEXT,
    ADD COLUMN policy_effect TEXT,
    ADD COLUMN issue_facet TEXT,
    ADD COLUMN confidence TEXT CHECK (confidence IS NULL OR confidence IN ('low', 'medium', 'high')),
    ADD COLUMN source_basis JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN uncertainty_note TEXT,
    ADD COLUMN reviewed_by TEXT,
    ADD COLUMN reviewed_at TIMESTAMPTZ;

CREATE INDEX idx_vote_interpretations_issue_facet
    ON vote_interpretations (issue_facet);

CREATE INDEX idx_vote_interpretations_confidence
    ON vote_interpretations (confidence);

COMMIT;
