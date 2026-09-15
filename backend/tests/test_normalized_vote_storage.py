import copy
import pytest
from app.etl.normalized_vote_storage import split_contexts
from app.etl.vote_context import build_vote_contexts


def records():
    return build_vote_contexts(legislators=[{'id':1,'party':'D'},{'id':2,'party':'R'}],
        roll_calls=[{'id':1,'session':1,'question':'On passage','description':'','source_url':'https://clerk.house.gov/Votes/20251'}],
        votes_cast=[{'roll_call_id':1,'legislator_id':1,'position':'yea'},{'roll_call_id':1,'legislator_id':2,'position':'nay'}])


def test_shared_context_is_once_and_member_context_is_exact():
    rows=records(); shared,members=split_contexts(rows)
    assert len(shared)==1 and len(members)==2
    assert shared[1]['party_vote_totals']==rows[0]['party_vote_totals']
    assert members[(1,1)]['member_position']=='yea'
    assert members[(1,2)]['member_position']=='nay'
    assert split_contexts(rows+rows)==(shared,members)


@pytest.mark.parametrize('field,value',[('party_vote_totals',{}),('context_source_list',[]),('chamber_session',None),('context_version','different')])
def test_meaningful_roll_conflicts_fail_closed(field,value):
    rows=records();rows[1][field]=value
    with pytest.raises(ValueError,match='roll-level context ambiguity'):split_contexts(rows)


def test_conflicting_duplicate_member_fails_closed():
    rows=records();bad=copy.deepcopy(rows[0]);bad['member_position']='nay'
    with pytest.raises(ValueError,match='member context ambiguity'):split_contexts([rows[0],bad])
