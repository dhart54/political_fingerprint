import pytest

from scripts.editorial_artifact_store import StoreSafetyError
from scripts.green_production_target import GREEN_IDENTITY, production_target_info, target_identity
from app.editorial_presentations.compiler import canonical_digest

GREEN = 'postgresql://postgres.yalpfkaxkxebwolhorha:test@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require'


def test_exact_green_identity_and_disposable_compatibility():
    assert production_target_info(GREEN) == GREEN_IDENTITY
    assert target_identity(GREEN, 'production') == canonical_digest(GREEN_IDENTITY)
    assert target_identity('postgresql://postgres@127.0.0.1:55434/pf_m15b_green', 'disposable')


@pytest.mark.parametrize('url', [
    GREEN.replace('yalpfkaxkxebwolhorha', 'wfhnmuxlbfpweupisfao'),
    GREEN.replace('aws-0-', 'aws-1-'),
    GREEN.replace(':5432/', ':6543/'),
    GREEN.replace('/postgres?', '/other?'),
    GREEN.replace(':test@', '@'),
    GREEN.replace('?sslmode=require', ''),
    GREEN.replace('sslmode=require', 'sslmode=disable'),
    GREEN + '&host=127.0.0.1',
    GREEN + '&hostaddr=127.0.0.1',
    GREEN + '&user=other',
    GREEN + '&dbname=other',
    GREEN + '&options=-csearch_path=other',
    GREEN + '&sslmode=disable',
    GREEN + '#fragment',
])
def test_target_or_connection_override_refused(url):
    with pytest.raises(StoreSafetyError, match='exact approved green'):
        production_target_info(url)
