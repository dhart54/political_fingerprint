BEGIN;

CREATE TABLE IF NOT EXISTS legislator_contacts (
    legislator_id BIGINT PRIMARY KEY REFERENCES legislators(id) ON DELETE CASCADE,
    official_website_url TEXT,
    contact_form_url TEXT,
    phone TEXT,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_retrieved_at DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        official_website_url IS NOT NULL
        OR contact_form_url IS NOT NULL
        OR phone IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_legislator_contacts_source
    ON legislator_contacts (source_type, source_retrieved_at);

COMMIT;
