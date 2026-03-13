from pathlib import Path


MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "0001_initial_schema.sql"


def test_initial_migration_defines_required_enums_and_tables() -> None:
    migration_sql = MIGRATION_PATH.read_text()

    required_types = [
        "create type chamber as enum",
        "create type vote_position as enum",
        "create type issue_domain as enum",
    ]
    required_tables = [
        "create table legislators",
        "create table bills",
        "create table roll_calls",
        "create table votes_cast",
        "create table vote_classifications",
        "create table fingerprints",
        "create table chamber_medians",
        "create table drift_scores",
        "create table summaries",
        "create table zip_district_map",
    ]

    lowered = migration_sql.lower()

    for sql_fragment in required_types + required_tables:
        assert sql_fragment in lowered


def test_initial_migration_captures_locked_domain_and_precompute_constraints() -> None:
    migration_sql = MIGRATION_PATH.read_text()

    for domain in [
        "ECONOMY_TAXES",
        "HEALTH_SOCIAL",
        "EDUCATION_WORKFORCE",
        "ENVIRONMENT_ENERGY",
        "NATIONAL_SECURITY_FOREIGN",
        "IMMIGRATION_BORDER",
        "JUSTICE_PUBLIC_SAFETY",
        "INFRASTRUCTURE_TECH_TRANSPORT",
    ]:
        assert domain in migration_sql

    assert "CHECK (\n        (is_eligible = TRUE AND primary_domain IS NOT NULL)" in migration_sql
    assert "vote_share DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (vote_share >= 0 AND vote_share <= 1)" in migration_sql
    assert "party TEXT NOT NULL CHECK (party IN ('ALL', 'D', 'R'))" in migration_sql
    assert "CHECK (\n        (insufficient_data = TRUE AND drift_value IS NULL)" in migration_sql
    assert "UNIQUE (legislator_id, window_end, classification_version)" in migration_sql
