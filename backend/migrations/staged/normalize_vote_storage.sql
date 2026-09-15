-- STAGED, opt-in migration. Never part of automatic migration discovery.
-- Use on an isolated green clone only after its separate authorization.
BEGIN;
LOCK TABLE public.roll_calls, public.vote_contexts IN ACCESS EXCLUSIVE MODE;
DO $$ BEGIN
 IF EXISTS (SELECT roll_call_id FROM public.vote_contexts GROUP BY roll_call_id
 HAVING count(DISTINCT ROW(chamber_session,vote_type,final_result,vote_margin,winning_position,party_vote_totals,bipartisan_majority,sponsor_party,context_source_list,context_version))<>1) THEN
 RAISE EXCEPTION 'roll-level context ambiguity: normalization refused';
 END IF;
END $$;
ALTER TABLE public.roll_calls
 ADD COLUMN context_chamber_session INTEGER,
 ADD COLUMN context_vote_type TEXT,
 ADD COLUMN context_final_result TEXT,
 ADD COLUMN context_vote_margin INTEGER,
 ADD COLUMN context_winning_position vote_position,
 ADD COLUMN context_party_vote_totals JSONB,
 ADD COLUMN context_bipartisan_majority BOOLEAN,
 ADD COLUMN context_sponsor_party TEXT,
 ADD COLUMN context_context_source_list JSONB,
 ADD COLUMN context_context_version TEXT;
UPDATE public.roll_calls r SET context_chamber_session=c.chamber_session,context_vote_type=c.vote_type,context_final_result=c.final_result,context_vote_margin=c.vote_margin,context_winning_position=c.winning_position,context_party_vote_totals=c.party_vote_totals,context_bipartisan_majority=c.bipartisan_majority,context_sponsor_party=c.sponsor_party,context_context_source_list=c.context_source_list,context_context_version=c.context_version FROM (SELECT DISTINCT ON (roll_call_id) * FROM public.vote_contexts ORDER BY roll_call_id,legislator_id) c WHERE r.id=c.roll_call_id;
ALTER TABLE public.roll_calls ADD CONSTRAINT roll_context_complete CHECK (context_context_version IS NULL OR (context_vote_type IN ('final_passage','amendment','rule','motion','concurrence','procedural','nomination','appropriations','cra_disapproval','other') AND context_vote_type IS NOT NULL AND context_final_result IN ('passed','failed','no_yea_nay_majority') AND context_final_result IS NOT NULL AND context_vote_margin>=0 AND context_vote_margin IS NOT NULL AND context_party_vote_totals IS NOT NULL AND context_bipartisan_majority IS NOT NULL AND context_context_source_list IS NOT NULL));
CREATE TABLE public.vote_context_members (
roll_call_id BIGINT NOT NULL REFERENCES public.roll_calls(id) ON DELETE CASCADE,
legislator_id BIGINT NOT NULL REFERENCES public.legislators(id) ON DELETE CASCADE,
member_position vote_position NOT NULL,
member_party TEXT NOT NULL,
member_party_majority_position vote_position,
member_voted_with_party_majority BOOLEAN,
member_voted_with_winning_side BOOLEAN,
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 PRIMARY KEY (roll_call_id,legislator_id)
);
INSERT INTO public.vote_context_members (roll_call_id,legislator_id,member_position,member_party,member_party_majority_position,member_voted_with_party_majority,member_voted_with_winning_side,created_at,updated_at) SELECT roll_call_id,legislator_id,member_position,member_party,member_party_majority_position,member_voted_with_party_majority,member_voted_with_winning_side,created_at,updated_at FROM public.vote_contexts;
CREATE INDEX idx_vote_context_members_legislator ON public.vote_context_members(legislator_id);
CREATE INDEX idx_vote_context_members_party_result ON public.vote_context_members(member_voted_with_party_majority,member_voted_with_winning_side);
CREATE INDEX idx_roll_context_vote_type ON public.roll_calls(context_vote_type);
ALTER TABLE public.vote_contexts RENAME TO vote_contexts_legacy;
CREATE VIEW public.vote_contexts WITH (security_invoker=true) AS SELECT m.roll_call_id,m.legislator_id,r.context_chamber_session AS chamber_session,r.context_vote_type AS vote_type,m.member_position,r.context_final_result AS final_result,r.context_vote_margin AS vote_margin,r.context_winning_position AS winning_position,r.context_party_vote_totals AS party_vote_totals,m.member_party,m.member_party_majority_position,m.member_voted_with_party_majority,m.member_voted_with_winning_side,r.context_bipartisan_majority AS bipartisan_majority,r.context_sponsor_party AS sponsor_party,r.context_context_source_list AS context_source_list,r.context_context_version AS context_version,m.created_at,m.updated_at FROM public.vote_context_members m JOIN public.roll_calls r ON r.id=m.roll_call_id;
DO $$ BEGIN
 IF EXISTS ((SELECT * FROM public.vote_contexts_legacy EXCEPT ALL SELECT * FROM public.vote_contexts)
 UNION ALL (SELECT * FROM public.vote_contexts EXCEPT ALL SELECT * FROM public.vote_contexts_legacy)) THEN
 RAISE EXCEPTION 'complete context parity failed';
 END IF;
END $$;
-- The separate source/blue database is the retained rollback copy.
DROP TABLE public.vote_contexts_legacy;
CREATE FUNCTION public.guard_member_context_owner() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.roll_calls WHERE id=NEW.roll_call_id AND context_context_version IS NOT NULL) THEN
 RAISE EXCEPTION 'member context requires initialized roll context';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER member_context_owner BEFORE INSERT OR UPDATE ON public.vote_context_members FOR EACH ROW EXECUTE FUNCTION public.guard_member_context_owner();
CREATE FUNCTION public.guard_shared_context_change() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF ROW(OLD.context_chamber_session,OLD.context_vote_type,OLD.context_final_result,OLD.context_vote_margin,OLD.context_winning_position,OLD.context_party_vote_totals,OLD.context_bipartisan_majority,OLD.context_sponsor_party,OLD.context_context_source_list,OLD.context_context_version) IS DISTINCT FROM ROW(NEW.context_chamber_session,NEW.context_vote_type,NEW.context_final_result,NEW.context_vote_margin,NEW.context_winning_position,NEW.context_party_vote_totals,NEW.context_bipartisan_majority,NEW.context_sponsor_party,NEW.context_context_source_list,NEW.context_context_version) AND EXISTS(SELECT 1 FROM public.vote_context_members WHERE roll_call_id=OLD.id) THEN RAISE EXCEPTION 'shared context drift: explicit reviewed rebuild required'; END IF; RETURN NEW; END $$;
CREATE TRIGGER shared_context_change BEFORE UPDATE OF context_chamber_session,context_vote_type,context_final_result,context_vote_margin,context_winning_position,context_party_vote_totals,context_bipartisan_majority,context_sponsor_party,context_context_source_list,context_context_version ON public.roll_calls FOR EACH ROW EXECUTE FUNCTION public.guard_shared_context_change();
ALTER TABLE public.vote_context_members ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.vote_context_members, public.vote_contexts FROM PUBLIC, anon, authenticated;
CREATE FUNCTION public.write_logical_vote_context() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE owner public.roll_calls%ROWTYPE;
BEGIN
 IF TG_OP='DELETE' THEN
  DELETE FROM public.vote_context_members WHERE roll_call_id=OLD.roll_call_id AND legislator_id=OLD.legislator_id;
  RETURN OLD;
 END IF;
 IF TG_OP='UPDATE' AND (NEW.roll_call_id,NEW.legislator_id) IS DISTINCT FROM (OLD.roll_call_id,OLD.legislator_id) THEN
  RAISE EXCEPTION 'context identity is immutable';
 END IF;
 SELECT * INTO owner FROM public.roll_calls WHERE id=NEW.roll_call_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'missing canonical roll call'; END IF;
 IF owner.context_context_version IS NULL THEN
UPDATE public.roll_calls SET context_chamber_session=NEW.chamber_session,context_vote_type=NEW.vote_type,context_final_result=NEW.final_result,context_vote_margin=NEW.vote_margin,context_winning_position=NEW.winning_position,context_party_vote_totals=NEW.party_vote_totals,context_bipartisan_majority=NEW.bipartisan_majority,context_sponsor_party=NEW.sponsor_party,context_context_source_list=NEW.context_source_list,context_context_version=NEW.context_version WHERE id=NEW.roll_call_id;
ELSIF ROW(owner.context_chamber_session,owner.context_vote_type,owner.context_final_result,owner.context_vote_margin,owner.context_winning_position,owner.context_party_vote_totals,owner.context_bipartisan_majority,owner.context_sponsor_party,owner.context_context_source_list,owner.context_context_version) IS DISTINCT FROM ROW(NEW.chamber_session,NEW.vote_type,NEW.final_result,NEW.vote_margin,NEW.winning_position,NEW.party_vote_totals,NEW.bipartisan_majority,NEW.sponsor_party,NEW.context_source_list,NEW.context_version) THEN RAISE EXCEPTION 'shared context drift: explicit reviewed rebuild required'; END IF;
IF TG_OP='INSERT' THEN INSERT INTO public.vote_context_members (roll_call_id,legislator_id,member_position,member_party,member_party_majority_position,member_voted_with_party_majority,member_voted_with_winning_side,created_at,updated_at) VALUES (NEW.roll_call_id,NEW.legislator_id,NEW.member_position,NEW.member_party,NEW.member_party_majority_position,NEW.member_voted_with_party_majority,NEW.member_voted_with_winning_side,NEW.created_at,NEW.updated_at);
ELSE UPDATE public.vote_context_members SET member_position=NEW.member_position,member_party=NEW.member_party,member_party_majority_position=NEW.member_party_majority_position,member_voted_with_party_majority=NEW.member_voted_with_party_majority,member_voted_with_winning_side=NEW.member_voted_with_winning_side,created_at=NEW.created_at,updated_at=NEW.updated_at WHERE roll_call_id=OLD.roll_call_id AND legislator_id=OLD.legislator_id; END IF; RETURN NEW; END $$;
CREATE TRIGGER logical_context_write INSTEAD OF INSERT OR UPDATE OR DELETE ON public.vote_contexts FOR EACH ROW EXECUTE FUNCTION public.write_logical_vote_context();
ALTER VIEW public.vote_contexts ALTER COLUMN party_vote_totals SET DEFAULT '{}'::jsonb;
ALTER VIEW public.vote_contexts ALTER COLUMN context_source_list SET DEFAULT '[]'::jsonb;
ALTER VIEW public.vote_contexts ALTER COLUMN bipartisan_majority SET DEFAULT false;
ALTER VIEW public.vote_contexts ALTER COLUMN created_at SET DEFAULT now();
ALTER VIEW public.vote_contexts ALTER COLUMN updated_at SET DEFAULT now();
COMMIT;
