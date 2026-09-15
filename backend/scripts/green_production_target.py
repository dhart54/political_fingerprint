"""Exact current production target; historical operators keep their frozen pins."""
from urllib.parse import parse_qs, unquote, urlsplit

from app.editorial_presentations.compiler import canonical_digest
from scripts.editorial_artifact_store import StoreSafetyError, target_info

GREEN_PROJECT = 'yalpfkaxkxebwolhorha'
GREEN_HOST = 'aws-0-us-east-1.pooler.supabase.com'
GREEN_IDENTITY = {
    'scheme': 'postgresql', 'host': GREEN_HOST, 'port': 5432,
    'database': 'postgres', 'project_ref': GREEN_PROJECT,
    'username': 'postgres.' + GREEN_PROJECT,
}


def production_target_info(database_url):
    try:
        parsed = urlsplit(database_url)
        actual = {
            'scheme': parsed.scheme, 'host': parsed.hostname, 'port': parsed.port,
            'database': parsed.path.lstrip('/'), 'project_ref': GREEN_PROJECT,
            'username': unquote(parsed.username or ''),
        }
        query = parse_qs(parsed.query, keep_blank_values=True)
        valid = (actual == GREEN_IDENTITY and bool(parsed.password)
                 and not parsed.fragment and set(query) == {'sslmode'}
                 and query['sslmode'] in (['require'], ['verify-full']))
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise StoreSafetyError('exact approved green production target with TLS required')
    return dict(GREEN_IDENTITY)


def target_identity(database_url, target):
    if target == 'production':
        return canonical_digest(production_target_info(database_url))
    info = target_info(database_url, target, None)
    return canonical_digest({key: info[key] for key in ('scheme', 'host', 'port', 'database')})
