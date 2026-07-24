BEGIN;

CREATE TABLE public.editorial_artifact_batches (
    batch_id BIGSERIAL PRIMARY KEY,
    deterministic_batch_key TEXT NOT NULL UNIQUE,
    source_commit_sha TEXT NOT NULL CHECK (source_commit_sha ~ '^[0-9a-f]{40}$'),
    manifest_sha256 TEXT NOT NULL CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    status TEXT NOT NULL CHECK (status IN ('pending_review', 'applied', 'rolled_back')),
    artifact_count INTEGER NOT NULL CHECK (artifact_count >= 0),
    relationship_count INTEGER NOT NULL CHECK (relationship_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    applied_at TIMESTAMPTZ
);

CREATE TABLE public.editorial_artifact_versions (
    artifact_id BIGSERIAL PRIMARY KEY,
    artifact_type TEXT NOT NULL CHECK (artifact_type IN (
        'shared_action_dossier',
        'source_manifest',
        'claim_source_map',
        'policy_episode',
        'policy_family',
        'issue_ontology',
        'policy_trait_contract',
        'trait_relationship_contract',
        'member_action_overlay',
        'member_episode_trajectory',
        'issue_conclusion_propositions',
        'issue_public_presentation',
        'standardization_validation_result',
        'reference_fixture_metadata',
        'review_routing_result'
    )),
    natural_key TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    artifact_version INTEGER NOT NULL CHECK (artifact_version > 0),
    payload_jsonb JSONB NOT NULL CHECK (jsonb_typeof(payload_jsonb) = 'object'),
    content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    source_manifest_sha256 TEXT CHECK (source_manifest_sha256 IS NULL OR source_manifest_sha256 ~ '^[0-9a-f]{64}$'),
    source_commit_sha TEXT NOT NULL CHECK (source_commit_sha ~ '^[0-9a-f]{40}$'),
    batch_id BIGINT NOT NULL REFERENCES public.editorial_artifact_batches(batch_id) ON DELETE RESTRICT,
    supersedes_artifact_id BIGINT REFERENCES public.editorial_artifact_versions(artifact_id) ON DELETE RESTRICT,
    member_bioguide_id TEXT REFERENCES public.legislators(bioguide_id) ON DELETE RESTRICT,
    issue_id TEXT,
    congress INTEGER CHECK (congress IS NULL OR congress > 0),
    chamber chamber,
    canonical_roll_call_id BIGINT REFERENCES public.roll_calls(id) ON DELETE RESTRICT,
    canonical_action_id TEXT,
    episode_id TEXT,
    policy_family_id TEXT,
    editorial_status TEXT NOT NULL CHECK (editorial_status IN (
        'agent_source_checked',
        'human_approval_pending',
        'human_approved',
        'insufficient_evidence'
    )),
    benchmark_status TEXT NOT NULL CHECK (benchmark_status IN ('not_promoted', 'gold_benchmark')),
    production_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    review_route TEXT NOT NULL CHECK (review_route IN (
        'standard_generation',
        'sampled_audit',
        'human_exception',
        'blocked'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (natural_key, artifact_version),
    UNIQUE (artifact_id, content_sha256),
    CHECK (supersedes_artifact_id IS NULL OR supersedes_artifact_id <> artifact_id),
    CHECK (NOT production_eligible OR (
        editorial_status = 'human_approved'
        AND benchmark_status = 'gold_benchmark'
    ))
);

CREATE TABLE public.editorial_artifact_relationships (
    parent_artifact_id BIGINT NOT NULL REFERENCES public.editorial_artifact_versions(artifact_id) ON DELETE CASCADE,
    child_artifact_id BIGINT NOT NULL REFERENCES public.editorial_artifact_versions(artifact_id) ON DELETE RESTRICT,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        'uses_source_manifest',
        'maps_claims_to_sources',
        'contains_action',
        'groups_episode',
        'uses_policy_family',
        'uses_trait_contract',
        'uses_trait_relationship_contract',
        'has_member_overlay',
        'has_trajectory',
        'has_conclusion_propositions',
        'has_public_presentation',
        'has_validation',
        'has_reference_metadata',
        'has_review_route',
        'supersedes'
    )),
    ordinal INTEGER NOT NULL DEFAULT 0 CHECK (ordinal >= 0),
    metadata_jsonb JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata_jsonb) = 'object'),
    PRIMARY KEY (parent_artifact_id, child_artifact_id, relationship_type)
);

CREATE TABLE public.editorial_publication_registry (
    member_bioguide_id TEXT NOT NULL REFERENCES public.legislators(bioguide_id) ON DELETE RESTRICT,
    issue_id TEXT NOT NULL,
    artifact_id BIGINT NOT NULL UNIQUE REFERENCES public.editorial_artifact_versions(artifact_id) ON DELETE RESTRICT,
    publicly_active BOOLEAN NOT NULL CHECK (publicly_active = TRUE),
    activated_at TIMESTAMPTZ NOT NULL,
    deactivated_at TIMESTAMPTZ,
    publication_metadata_jsonb JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(publication_metadata_jsonb) = 'object'),
    PRIMARY KEY (member_bioguide_id, issue_id),
    CHECK (deactivated_at IS NULL OR deactivated_at >= activated_at)
);

CREATE INDEX idx_editorial_artifact_versions_type_key
    ON public.editorial_artifact_versions (artifact_type, natural_key, artifact_version DESC);
CREATE INDEX idx_editorial_artifact_versions_member_issue
    ON public.editorial_artifact_versions (member_bioguide_id, issue_id, artifact_type);
CREATE INDEX idx_editorial_artifact_versions_action
    ON public.editorial_artifact_versions (canonical_action_id) WHERE canonical_action_id IS NOT NULL;
CREATE INDEX idx_editorial_artifact_versions_episode
    ON public.editorial_artifact_versions (episode_id) WHERE episode_id IS NOT NULL;
CREATE INDEX idx_editorial_artifact_versions_family
    ON public.editorial_artifact_versions (policy_family_id) WHERE policy_family_id IS NOT NULL;
CREATE INDEX idx_editorial_artifact_versions_status
    ON public.editorial_artifact_versions (editorial_status, benchmark_status, production_eligible, review_route);
CREATE INDEX idx_editorial_artifact_versions_hash
    ON public.editorial_artifact_versions (content_sha256);
CREATE INDEX idx_editorial_artifact_versions_batch
    ON public.editorial_artifact_versions (batch_id);
CREATE INDEX idx_editorial_artifact_relationships_child
    ON public.editorial_artifact_relationships (child_artifact_id);

CREATE FUNCTION public.guard_editorial_artifact_immutability()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    allowed_batch_key TEXT;
    row_batch_key TEXT;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'editorial artifact versions are append-only';
    END IF;
    allowed_batch_key := current_setting('app.editorial_artifact_rollback_batch', TRUE);
    SELECT deterministic_batch_key INTO row_batch_key
    FROM public.editorial_artifact_batches
    WHERE batch_id = OLD.batch_id;
    IF allowed_batch_key IS NULL OR allowed_batch_key = '' OR allowed_batch_key <> row_batch_key THEN
        RAISE EXCEPTION 'editorial artifact deletion requires the exact rollback batch';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.editorial_publication_registry
        WHERE artifact_id = OLD.artifact_id
    ) THEN
        RAISE EXCEPTION 'published editorial artifact versions cannot be deleted';
    END IF;
    RETURN OLD;
END;
$$;

CREATE TRIGGER editorial_artifact_versions_immutable
BEFORE UPDATE OR DELETE ON public.editorial_artifact_versions
FOR EACH ROW EXECUTE FUNCTION public.guard_editorial_artifact_immutability();

CREATE FUNCTION public.guard_editorial_publication_activation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    candidate public.editorial_artifact_versions%ROWTYPE;
BEGIN
    SELECT * INTO candidate
    FROM public.editorial_artifact_versions
    WHERE artifact_id = NEW.artifact_id;
    IF candidate.artifact_type <> 'issue_public_presentation'
       OR candidate.member_bioguide_id IS DISTINCT FROM NEW.member_bioguide_id
       OR candidate.issue_id IS DISTINCT FROM NEW.issue_id
       OR candidate.editorial_status <> 'human_approved'
       OR candidate.benchmark_status <> 'gold_benchmark'
       OR candidate.production_eligible IS NOT TRUE THEN
        RAISE EXCEPTION 'publication candidate fails approval, benchmark, eligibility, or identity gates';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.editorial_artifact_relationships rel
        JOIN public.editorial_artifact_versions validation ON validation.artifact_id = rel.child_artifact_id
        WHERE rel.parent_artifact_id = candidate.artifact_id
          AND rel.relationship_type = 'has_validation'
          AND validation.artifact_type = 'standardization_validation_result'
          AND validation.payload_jsonb @> '{"successful":true,"current":true,"blocking_findings":0}'::jsonb
    ) THEN
        RAISE EXCEPTION 'publication candidate lacks successful current validation';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.editorial_artifact_relationships rel
        JOIN public.editorial_artifact_versions source_manifest ON source_manifest.artifact_id = rel.child_artifact_id
        WHERE rel.parent_artifact_id = candidate.artifact_id
          AND rel.relationship_type = 'uses_source_manifest'
          AND source_manifest.artifact_type = 'source_manifest'
          AND source_manifest.payload_jsonb @> '{"complete_required_sources":true}'::jsonb
    ) THEN
        RAISE EXCEPTION 'publication candidate lacks complete required source references';
    END IF;
    IF COALESCE((candidate.payload_jsonb ->> 'blocking_findings')::integer, 0) <> 0 THEN
        RAISE EXCEPTION 'publication candidate has blocking findings';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER editorial_publication_registry_fail_closed
BEFORE INSERT OR UPDATE ON public.editorial_publication_registry
FOR EACH ROW EXECUTE FUNCTION public.guard_editorial_publication_activation();

ALTER TABLE public.editorial_artifact_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_artifact_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_artifact_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_publication_registry ENABLE ROW LEVEL SECURITY;

REVOKE ALL PRIVILEGES ON TABLE public.editorial_artifact_batches FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.editorial_artifact_versions FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.editorial_artifact_relationships FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.editorial_publication_registry FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON SEQUENCE public.editorial_artifact_batches_batch_id_seq FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON SEQUENCE public.editorial_artifact_versions_artifact_id_seq FROM anon, authenticated;

COMMIT;
