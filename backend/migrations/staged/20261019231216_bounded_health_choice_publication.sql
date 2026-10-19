-- STAGED ONLY. Neither app startup nor CI/deployment applies this to production.
-- Applies after 0016, with separate future migration/activation authorization.
BEGIN;

ALTER TABLE public.editorial_artifact_versions
    ADD COLUMN publication_basis TEXT NOT NULL DEFAULT 'legacy_gold'
        CHECK (publication_basis IN ('legacy_gold', 'bounded_choice_review')),
    ADD COLUMN bounded_acceptance_artifact_id BIGINT
        REFERENCES public.editorial_artifact_versions(artifact_id) ON DELETE RESTRICT;

-- Find exactly the original eligibility CHECK, rather than relying on an
-- implicitly assigned constraint name that may vary between installations.
DO $$
DECLARE names TEXT[];
BEGIN
    SELECT array_agg(conname) INTO names FROM pg_constraint
    WHERE conrelid = 'public.editorial_artifact_versions'::regclass
      AND contype = 'c'
      AND pg_get_constraintdef(oid) LIKE '%NOT production_eligible%gold_benchmark%';
    IF cardinality(names) IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION 'expected exactly the original gold eligibility CHECK';
    END IF;
    EXECUTE format('ALTER TABLE public.editorial_artifact_versions DROP CONSTRAINT %I', names[1]);
END $$;

ALTER TABLE public.editorial_artifact_versions ADD CONSTRAINT editorial_eligibility_by_basis CHECK (
    (publication_basis = 'legacy_gold' AND bounded_acceptance_artifact_id IS NULL
     AND (NOT production_eligible OR (editorial_status = 'human_approved' AND benchmark_status = 'gold_benchmark')))
    OR
    (publication_basis = 'bounded_choice_review' AND artifact_type = 'issue_public_presentation'
     AND member_bioguide_id IS NOT NULL AND issue_id IS NOT NULL AND congress IS NOT NULL
     AND canonical_action_id IS NOT NULL AND episode_id IS NOT NULL
     AND member_bioguide_id IN ('F000477','M001184') AND issue_id = 'HEALTH_SOCIAL'
     AND congress = 119 AND canonical_action_id = 'house:119:2:180'
     AND episode_id = 'episode:s2393:119' AND editorial_status = 'human_approved'
     AND benchmark_status = 'not_promoted' AND production_eligible
     AND bounded_acceptance_artifact_id IS NOT NULL)
);

-- Compact sorted UTF-8 JSON, matching the established Python canonical_digest
-- for these integer/string/boolean/null contracts. No extension is required.
CREATE FUNCTION public.bounded_choice_canonical_json(value JSONB) RETURNS TEXT
LANGUAGE sql IMMUTABLE STRICT SECURITY INVOKER SET search_path = pg_catalog, public AS $$
    SELECT CASE jsonb_typeof(value)
      WHEN 'object' THEN '{' || COALESCE((SELECT string_agg(to_jsonb(key)::text || ':' || public.bounded_choice_canonical_json(val), ',' ORDER BY key COLLATE "C") FROM jsonb_each(value) AS e(key,val)), '') || '}'
      WHEN 'array' THEN '[' || COALESCE((SELECT string_agg(public.bounded_choice_canonical_json(val), ',' ORDER BY ord) FROM jsonb_array_elements(value) WITH ORDINALITY AS e(val,ord)), '') || ']'
      ELSE value::text END
$$;

CREATE FUNCTION public.bounded_choice_digest(value JSONB) RETURNS TEXT
LANGUAGE sql IMMUTABLE STRICT SECURITY INVOKER SET search_path = pg_catalog, public AS $$
    SELECT encode(sha256(convert_to(public.bounded_choice_canonical_json(value), 'UTF8')), 'hex')
$$;

CREATE FUNCTION public.bounded_choice_receipt_matches(payload JSONB, member TEXT) RETURNS BOOLEAN
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = pg_catalog, public AS $$
DECLARE receipt JSONB := payload->'acceptance'; semantic JSONB := payload->'semantic';
        presentation JSONB := payload->'presentation'; rendering JSONB := payload->'rendering';
        expected_semantic TEXT; expected_presentation TEXT;
BEGIN
    IF member = 'F000477' THEN
        expected_semantic := 'a949d7df167e1d87a74e5d60d3893bd71d1d0f3373c13679566baaf49babea83';
        expected_presentation := 'b5d84225f81c50114420c270ed9f3e5292a8c660aaec2883da45c9f4a615fce3';
    ELSIF member = 'M001184' THEN
        expected_semantic := '22774879942755bbfadcffee831ef2bf98817bfe52fd0eda91869a59e2a75e2d';
        expected_presentation := 'd67e3983f5dd09fca18b51d20e599abe7050bfaef70c27215ad9d24c1f14e206';
    ELSE RETURN FALSE; END IF;
    RETURN COALESCE(
      payload->>'schema_version' = 'bounded_choice_publication_v1'
      AND payload->>'artifact_id' = presentation->>'artifact_id'
      AND payload->'blocking_findings' = '0'::jsonb
      AND semantic->>'member_id' = member AND presentation->>'member_id' = member
      AND semantic->>'issue_id' = 'HEALTH_SOCIAL'
      AND semantic->>'semantic_subject_sha256' = expected_semantic
      AND public.bounded_choice_digest(semantic - 'semantic_subject_sha256') = expected_semantic
      AND presentation->>'presentation_subject_sha256' = expected_presentation
      AND public.bounded_choice_digest(presentation - 'presentation_subject_sha256') = expected_presentation
      AND rendering->>'member_id' = member
      AND rendering->>'schema_version' = 'bounded_choice_rendering_subject_v1'
      AND rendering->>'presentation_subject_sha256' = expected_presentation
      AND public.bounded_choice_digest(rendering - 'rendering_subject_sha256') = rendering->>'rendering_subject_sha256'
      AND jsonb_array_length(rendering->'captures') = 2
      AND receipt->>'schema_version' = 'bounded_choice_acceptance_receipt_v1'
      AND receipt->>'member_id' = member AND receipt->>'issue_id' = 'HEALTH_SOCIAL'
      AND receipt->>'review_scope' = 'bounded_partial_record'
      AND receipt->>'semantic_subject_sha256' = expected_semantic
      AND receipt->>'presentation_subject_sha256' = expected_presentation
      AND receipt->>'rendering_subject_sha256' = rendering->>'rendering_subject_sha256'
      AND receipt->>'decision' = 'accept_exact_bounded_choice_and_rendering'
      AND length(trim(receipt->>'reviewer')) > 0
      AND receipt->>'reviewer_authority' = 'bounded_choice_review_authority_v1'
      AND (receipt->>'decided_at_utc')::timestamptz <= now()
      AND receipt->'authorizations' = '{"publication":false,"production_eligibility":false,"database_writes":false,"deployment":false}'::jsonb
      AND public.bounded_choice_digest(receipt - 'receipt_subject_sha256') = receipt->>'receipt_subject_sha256', FALSE);
EXCEPTION WHEN invalid_text_representation OR datetime_field_overflow THEN RETURN FALSE;
END $$;

CREATE FUNCTION public.guard_bounded_choice_insert() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public AS $$
DECLARE receipt public.editorial_artifact_versions%ROWTYPE;
BEGIN
    IF NEW.publication_basis = 'bounded_choice_review' THEN
        SELECT * INTO receipt FROM public.editorial_artifact_versions WHERE artifact_id=NEW.bounded_acceptance_artifact_id;
        IF public.bounded_choice_receipt_matches(NEW.payload_jsonb, NEW.member_bioguide_id) IS NOT TRUE
          OR public.bounded_choice_digest(NEW.payload_jsonb) IS DISTINCT FROM NEW.content_sha256
          OR NEW.schema_version IS DISTINCT FROM 'bounded_choice_publication_v1'
          OR NEW.source_manifest_sha256 IS DISTINCT FROM '7fa4ca255dd204670279e20ca2bcd69c1523d4787a28e0f15cb7991e22f0bc9a'
          OR NEW.natural_key IS DISTINCT FROM NEW.payload_jsonb->>'artifact_id'
          OR NEW.artifact_version <> 1
          OR receipt.artifact_id IS NULL OR receipt.artifact_type <> 'reference_fixture_metadata'
          OR receipt.batch_id IS DISTINCT FROM NEW.batch_id
          OR receipt.member_bioguide_id IS DISTINCT FROM NEW.member_bioguide_id
          OR receipt.issue_id IS DISTINCT FROM NEW.issue_id
          OR receipt.payload_jsonb IS DISTINCT FROM NEW.payload_jsonb->'acceptance'
          OR receipt.content_sha256 IS DISTINCT FROM public.bounded_choice_digest(receipt.payload_jsonb)
          OR receipt.editorial_status <> 'human_approved' THEN
            RAISE EXCEPTION 'bounded candidate lacks exact accepted subject evidence';
        END IF;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER editorial_bounded_choice_insert BEFORE INSERT ON public.editorial_artifact_versions
FOR EACH ROW EXECUTE FUNCTION public.guard_bounded_choice_insert();

CREATE FUNCTION public.bounded_choice_graph_valid(candidate_id BIGINT) RETURNS BOOLEAN
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = pg_catalog, public AS $$
DECLARE candidate public.editorial_artifact_versions%ROWTYPE; matches INTEGER;
BEGIN
    SELECT * INTO candidate FROM public.editorial_artifact_versions WHERE artifact_id=candidate_id;
    IF candidate.publication_basis IS DISTINCT FROM 'bounded_choice_review'
      OR candidate.editorial_status IS DISTINCT FROM 'human_approved'
      OR candidate.benchmark_status IS DISTINCT FROM 'not_promoted'
      OR candidate.production_eligible IS NOT TRUE
      OR public.bounded_choice_receipt_matches(candidate.payload_jsonb, candidate.member_bioguide_id) IS NOT TRUE
      OR public.bounded_choice_digest(candidate.payload_jsonb) IS DISTINCT FROM candidate.content_sha256 THEN RETURN FALSE; END IF;
    SELECT count(*) INTO matches FROM public.editorial_artifact_relationships r
    JOIN public.editorial_artifact_versions c ON c.artifact_id=r.child_artifact_id
    WHERE r.parent_artifact_id=candidate_id AND r.ordinal=0 AND r.metadata_jsonb='{}'::jsonb
      AND c.batch_id=candidate.batch_id AND c.member_bioguide_id=candidate.member_bioguide_id
      AND c.issue_id=candidate.issue_id AND c.congress=119
      AND c.payload_jsonb->>'member_id'=candidate.member_bioguide_id
      AND c.editorial_status='human_approved' AND c.benchmark_status='not_promoted'
      AND c.production_eligible=FALSE AND c.source_commit_sha=candidate.source_commit_sha
      AND public.bounded_choice_digest(c.payload_jsonb)=c.content_sha256
      AND ((r.relationship_type='has_validation' AND c.artifact_type='standardization_validation_result'
            AND c.payload_jsonb @> '{"successful":true,"current":true,"blocking_findings":0}'::jsonb
            AND c.payload_jsonb->>'candidate_sha256'=candidate.content_sha256
            AND c.payload_jsonb->>'runtime_manifest_sha256'=public.bounded_choice_digest(candidate.payload_jsonb->'rendering'->'runtime_manifest'))
        OR (r.relationship_type='uses_source_manifest' AND c.artifact_type='source_manifest'
            AND c.payload_jsonb @> '{"complete_required_sources":true,"normalized_source_sha256":"7fa4ca255dd204670279e20ca2bcd69c1523d4787a28e0f15cb7991e22f0bc9a"}'::jsonb
            AND c.payload_jsonb->'additional_raw_evidence'=candidate.payload_jsonb->'semantic'->'additional_raw_evidence')
        OR (r.relationship_type='has_reference_metadata' AND c.artifact_type='reference_fixture_metadata'
            AND c.artifact_id=candidate.bounded_acceptance_artifact_id
            AND c.payload_jsonb=candidate.payload_jsonb->'acceptance'));
    RETURN matches=3 AND (SELECT count(*) FROM public.editorial_artifact_relationships WHERE parent_artifact_id=candidate_id)=3
      AND (SELECT count(DISTINCT relationship_type) FROM public.editorial_artifact_relationships WHERE parent_artifact_id=candidate_id)=3;
END $$;

-- The legacy body below retains its original gates and meaning. Only the
-- explicitly selected bounded basis returns through the new closed branch.
CREATE OR REPLACE FUNCTION public.guard_editorial_publication_activation()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public AS $$
DECLARE candidate public.editorial_artifact_versions%ROWTYPE;
BEGIN
    SELECT * INTO candidate FROM public.editorial_artifact_versions WHERE artifact_id = NEW.artifact_id;
    IF candidate.publication_basis = 'bounded_choice_review' THEN
        IF candidate.member_bioguide_id IS DISTINCT FROM NEW.member_bioguide_id
          OR candidate.issue_id IS DISTINCT FROM NEW.issue_id
          OR public.bounded_choice_graph_valid(candidate.artifact_id) IS NOT TRUE
          OR NEW.publication_metadata_jsonb->>'publication_basis' IS DISTINCT FROM 'bounded_choice_review'
          OR NEW.publication_metadata_jsonb->>'presentation_natural_key' IS DISTINCT FROM candidate.natural_key
          OR NEW.publication_metadata_jsonb->'presentation_artifact_version' IS DISTINCT FROM to_jsonb(candidate.artifact_version)
          OR NEW.publication_metadata_jsonb->>'active_artifact_sha256' IS DISTINCT FROM candidate.content_sha256
          OR COALESCE(NEW.publication_metadata_jsonb->>'activation_authority_sha256','') !~ '^[0-9a-f]{64}$' THEN
            RAISE EXCEPTION 'bounded activation fails acceptance, current validation, source or identity gates';
        END IF;
        RETURN NEW;
    END IF;
    IF candidate.artifact_type <> 'issue_public_presentation'
       OR candidate.member_bioguide_id IS DISTINCT FROM NEW.member_bioguide_id
       OR candidate.issue_id IS DISTINCT FROM NEW.issue_id
       OR candidate.editorial_status <> 'human_approved'
       OR candidate.benchmark_status <> 'gold_benchmark'
       OR candidate.production_eligible IS NOT TRUE THEN
        RAISE EXCEPTION 'publication candidate fails approval, benchmark, eligibility, or identity gates';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.editorial_artifact_relationships rel
        JOIN public.editorial_artifact_versions validation ON validation.artifact_id = rel.child_artifact_id
        WHERE rel.parent_artifact_id = candidate.artifact_id AND rel.relationship_type = 'has_validation'
          AND validation.artifact_type = 'standardization_validation_result'
          AND validation.payload_jsonb @> '{"successful":true,"current":true,"blocking_findings":0}'::jsonb
    ) THEN RAISE EXCEPTION 'publication candidate lacks successful current validation'; END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.editorial_artifact_relationships rel
        JOIN public.editorial_artifact_versions source_manifest ON source_manifest.artifact_id = rel.child_artifact_id
        WHERE rel.parent_artifact_id = candidate.artifact_id AND rel.relationship_type = 'uses_source_manifest'
          AND source_manifest.artifact_type = 'source_manifest'
          AND source_manifest.payload_jsonb @> '{"complete_required_sources":true}'::jsonb
    ) THEN RAISE EXCEPTION 'publication candidate lacks complete required source references'; END IF;
    IF COALESCE((candidate.payload_jsonb ->> 'blocking_findings')::integer, 0) <> 0 THEN
        RAISE EXCEPTION 'publication candidate has blocking findings';
    END IF;
    RETURN NEW;
END $$;

CREATE VIEW public.editorial_bounded_choice_publications WITH (security_invoker=true) AS
SELECT r.*, a.payload_jsonb, a.content_sha256, a.editorial_status, a.benchmark_status,
       a.production_eligible, a.schema_version, a.artifact_version, a.natural_key, a.publication_basis
FROM public.editorial_publication_registry r JOIN public.editorial_artifact_versions a USING (artifact_id)
WHERE r.publicly_active AND r.deactivated_at IS NULL
  AND a.member_bioguide_id=r.member_bioguide_id AND a.issue_id=r.issue_id
  AND public.bounded_choice_graph_valid(a.artifact_id)
  AND r.publication_metadata_jsonb->>'publication_basis'='bounded_choice_review'
  AND r.publication_metadata_jsonb->>'active_artifact_sha256'=a.content_sha256
  AND r.publication_metadata_jsonb->>'presentation_natural_key'=a.natural_key
  AND r.publication_metadata_jsonb->'presentation_artifact_version'=to_jsonb(a.artifact_version)
  AND r.publication_metadata_jsonb->>'activation_authority_sha256' ~ '^[0-9a-f]{64}$';

REVOKE ALL ON public.editorial_bounded_choice_publications FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.bounded_choice_canonical_json(JSONB), public.bounded_choice_digest(JSONB),
 public.bounded_choice_receipt_matches(JSONB,TEXT), public.guard_bounded_choice_insert(),
 public.bounded_choice_graph_valid(BIGINT) FROM PUBLIC, anon, authenticated;
-- Existing backend DB owner/service access stays in force. No role gets a new
-- grant, definer function, RLS bypass, public policy or browser database access.
COMMIT;
