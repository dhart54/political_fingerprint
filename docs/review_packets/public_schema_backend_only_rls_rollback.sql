-- WARNING: This rollback restores the pre-remediation public-schema posture.
-- Use only as an emergency service-restoration measure if backend access fails.
-- Prefer a forward fix that preserves RLS. Running this rollback may reintroduce
-- anonymous/authenticated Supabase Data API access to these public tables.
BEGIN;

ALTER TABLE public.bills DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_evidence DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chamber_medians DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.drift_scores DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fingerprints DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.legislator_contacts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.legislators DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.race_candidates DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.roll_calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.senate_amendment_references DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.summaries DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.upcoming_races DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.vote_classifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.vote_contexts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.vote_interpretations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.votes_cast DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.zip_district_map DISABLE ROW LEVEL SECURITY;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

COMMIT;
