-- Explicit future schema rollback only; never run by startup or CI deployment.
-- First roll back bounded data batches in reverse order. Preserve legacy rows.
BEGIN;
DO $$ BEGIN
  IF EXISTS (SELECT FROM public.editorial_artifact_versions WHERE publication_basis='bounded_choice_review') THEN
    RAISE EXCEPTION 'roll back all bounded data before schema rollback';
  END IF;
END $$;
DROP VIEW public.editorial_bounded_choice_publications;
DROP TRIGGER editorial_bounded_choice_insert ON public.editorial_artifact_versions;
CREATE OR REPLACE FUNCTION public.guard_editorial_publication_activation()
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


DROP FUNCTION public.guard_bounded_choice_insert();
DROP FUNCTION public.bounded_choice_graph_valid(BIGINT);
DROP FUNCTION public.bounded_choice_receipt_matches(JSONB,TEXT);
DROP FUNCTION public.bounded_choice_digest(JSONB);
DROP FUNCTION public.bounded_choice_canonical_json(JSONB);
ALTER TABLE public.editorial_artifact_versions
  DROP CONSTRAINT editorial_eligibility_by_basis,
  DROP COLUMN bounded_acceptance_artifact_id,
  DROP COLUMN publication_basis;
ALTER TABLE public.editorial_artifact_versions ADD CONSTRAINT editorial_legacy_gold_eligibility
  CHECK (NOT production_eligible OR (editorial_status='human_approved' AND benchmark_status='gold_benchmark'));
COMMIT;
