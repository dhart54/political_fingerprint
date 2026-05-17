CREATE TABLE IF NOT EXISTS candidate_evidence (
    id BIGSERIAL PRIMARY KEY,
    race_candidate_id BIGINT NOT NULL REFERENCES race_candidates(id) ON DELETE CASCADE,
    evidence_tier TEXT NOT NULL CHECK (
        evidence_tier IN (
            'institutional_record',
            'sourced_stated_position',
            'insufficient_evidence'
        )
    ),
    issue_domain issue_domain,
    statement_text TEXT,
    neutral_summary TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('low', 'medium', 'high')),
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_retrieved_at TIMESTAMPTZ,
    external_evidence_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_candidate_evidence_candidate
    ON candidate_evidence (race_candidate_id, evidence_tier, issue_domain);

CREATE UNIQUE INDEX IF NOT EXISTS idx_candidate_evidence_external_source
    ON candidate_evidence (race_candidate_id, source_type, external_evidence_id)
    WHERE external_evidence_id IS NOT NULL;
