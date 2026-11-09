"""Execute the production lookup SQL against an isolated relational fixture."""
import sqlite3
from types import SimpleNamespace

import pytest

from app.api import precomputed
from app.api.public_data import PublicDataUnavailable


@pytest.fixture
def seat_database(monkeypatch):
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript("""
        CREATE TABLE legislators (
            id INTEGER PRIMARY KEY, bioguide_id TEXT, name_display TEXT,
            chamber TEXT, state TEXT, district TEXT, party TEXT, in_office BOOLEAN
        );
        CREATE TABLE zip_district_map (zip TEXT, state TEXT, district TEXT);
        INSERT INTO zip_district_map VALUES ('30236', 'GA', '13');
        INSERT INTO legislators VALUES
            (1, 'S001157', 'David Scott', 'house', 'GA', '13', 'D', FALSE),
            (2, 'B001328', 'Everton Blair Jr.', 'house', 'GA', '13', 'D', TRUE),
            (3, 'S001193', 'Eric Swalwell', 'house', 'CA', '14', 'D', FALSE),
            (4, 'W000832', 'Aisha Wahab', 'house', 'CA', '14', 'D', TRUE),
            (5, 'OLD001', 'Former Senator', 'senate', 'GA', NULL, 'R', FALSE),
            (6, 'NEW001', 'Current Senator A', 'senate', 'GA', NULL, 'D', TRUE),
            (7, 'NEW002', 'Current Senator B', 'senate', 'GA', NULL, 'R', TRUE),
            (8, 'UNK001', 'Unknown Status', 'house', 'GA', '13', 'I', NULL);
    """)

    def query_all(query, params=()):
        return [dict(row) for row in connection.execute(query.replace('%s', '?'), params)]

    monkeypatch.setattr(precomputed, '_query_all_dicts', query_all)
    monkeypatch.delenv('ENABLE_FIXTURE_FALLBACK', raising=False)
    yield connection
    connection.close()


@pytest.mark.parametrize(('state', 'district', 'expected'), [
    ('GA', '13', 'B001328'), ('CA', '14', 'W000832'),
])
def test_current_house_lookup_excludes_earlier_predecessor(seat_database, state, district, expected):
    assert precomputed._get_db_house_rep(state=state, district=district)['bioguide_id'] == expected


def test_zip_lookup_returns_current_house_and_senators(seat_database):
    payload = precomputed.get_zip_lookup_response(zip_code='30236')
    assert payload['house_rep']['bioguide_id'] == 'B001328'
    assert [row['bioguide_id'] for row in payload['senators']] == ['NEW001', 'NEW002']
    assert payload['data_source'] == 'database'


@pytest.mark.parametrize('active', [False, True])
def test_vacant_or_conflicting_house_does_not_select_a_predecessor(seat_database, active):
    if active:
        seat_database.execute("UPDATE legislators SET in_office = TRUE WHERE id = 1")
    else:
        seat_database.execute("UPDATE legislators SET in_office = FALSE WHERE id = 2")
    payload = precomputed.get_zip_lookup_response(zip_code='30236')
    assert payload['house_rep'] is None
    assert payload['data_source'] == 'database'


def test_current_lookup_does_not_hide_historical_name_or_profile(seat_database):
    matches = precomputed._search_db_legislators(query='David Scott')
    assert [row['bioguide_id'] for row in matches] == ['S001157']
    profile = precomputed._get_db_legislator_by_external_id('leg_david_scott')
    assert profile['bioguide_id'] == 'S001157'


def test_missing_seat_and_state_remain_empty(seat_database):
    assert precomputed._get_db_house_rep(state='GA', district='99') is None
    assert precomputed._get_db_senators(state='ZZ') == []


def test_house_query_failure_is_not_a_vacancy(monkeypatch):
    def unavailable(*args, **kwargs):
        raise PublicDataUnavailable()
    monkeypatch.setattr(precomputed, '_query_all_dicts', unavailable)
    with pytest.raises(PublicDataUnavailable):
        precomputed._get_db_house_rep(state='GA', district='13')


@pytest.mark.parametrize('duplicate', [False, True])
def test_demo_lookup_preserves_current_seat_rules(monkeypatch, fixture_mode, duplicate):
    def member(id, chamber, active):
        return dict(id=id, bioguide_id=id, name_display=id, chamber=chamber,
                    state='NC', district='04', party='D', in_office=active)
    members = [member('former', 'house', False), member('current', 'house', True),
               member('old_senator', 'senate', False), member('new_senator', 'senate', True)]
    if duplicate:
        members.append(member('conflicting', 'house', True))
    monkeypatch.setattr(precomputed, 'FALLBACK_FIXTURE_DATA', SimpleNamespace(
        legislators=members, zip_district_map=[dict(zip='27701', state='NC', district='04')]))
    monkeypatch.setattr(precomputed, '_get_db_zip_lookup_response', lambda **kwargs: None)
    payload = precomputed.get_zip_lookup_response(zip_code='27701')
    assert (payload['house_rep']['bioguide_id'] if payload['house_rep'] else None) == (None if duplicate else 'current')
    assert [row['bioguide_id'] for row in payload['senators']] == ['new_senator']


def test_demo_race_current_official_uses_same_status_filter(monkeypatch, fixture_mode):
    members = [dict(id=name, bioguide_id=name, name_display=name, chamber=chamber,
                    state='NC', district='04', party='D', in_office=active)
               for name, chamber, active in [('former', 'house', False), ('current', 'house', True),
                                             ('old_senator', 'senate', False), ('new_senator', 'senate', True)]]
    monkeypatch.setattr(precomputed, 'FALLBACK_FIXTURE_DATA', SimpleNamespace(
        legislators=members, zip_district_map=[dict(zip='27701', state='NC', district='04')]))
    monkeypatch.setattr(precomputed, '_get_db_zip_race_response', lambda **kwargs: None)
    monkeypatch.setattr(precomputed, '_build_fixture_zip_races', lambda **kwargs: kwargs)
    payload = precomputed.get_zip_race_response(zip_code='27701')
    assert payload['house_rep']['bioguide_id'] == 'current'
    assert [row['bioguide_id'] for row in payload['senators']] == ['new_senator']
