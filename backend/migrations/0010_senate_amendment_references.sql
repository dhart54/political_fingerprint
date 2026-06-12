BEGIN;

CREATE TABLE IF NOT EXISTS senate_amendment_references (
    roll_call_id BIGINT PRIMARY KEY REFERENCES roll_calls(id) ON DELETE CASCADE,
    amendment_number TEXT NOT NULL,
    amendment_type TEXT NOT NULL DEFAULT 'S.Amdt.',
    amendment_to_amendment_number TEXT,
    parent_bill_type TEXT NOT NULL,
    parent_bill_number INTEGER NOT NULL,
    parent_bill_display TEXT NOT NULL,
    amendment_purpose TEXT,
    source_url TEXT NOT NULL,
    source_xml_path TEXT,
    fact_status TEXT NOT NULL DEFAULT 'fact_only_uninterpreted' CHECK (
        fact_status IN ('fact_only_uninterpreted')
    ),
    source_version TEXT NOT NULL DEFAULT 'senate_xml_119_2025_v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (amendment_number <> ''),
    CHECK (parent_bill_type <> ''),
    CHECK (parent_bill_number > 0),
    CHECK (parent_bill_display <> '')
);

CREATE INDEX IF NOT EXISTS idx_senate_amendment_references_parent_bill
    ON senate_amendment_references (parent_bill_type, parent_bill_number);

CREATE INDEX IF NOT EXISTS idx_senate_amendment_references_fact_status
    ON senate_amendment_references (fact_status);

COMMIT;
