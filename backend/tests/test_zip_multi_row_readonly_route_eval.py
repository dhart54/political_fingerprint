from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LOOKUP_PATH = REPO_ROOT / "backend/app/api/lookup.py"
PRECOMPUTED_PATH = REPO_ROOT / "backend/app/api/precomputed.py"
API_ROOT = REPO_ROOT / "backend/app/api"


def test_zip_lookup_routes_still_delegate_to_compatibility_read_layer() -> None:
    lookup_tree = ast.parse(LOOKUP_PATH.read_text(encoding="utf-8"))
    calls_by_function = {
        node.name: {
            call.func.id
            for call in ast.walk(node)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        }
        for node in lookup_tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "get_zip_lookup_response" in calls_by_function["lookup_zip"]
    assert "get_zip_race_response" in calls_by_function["lookup_zip_races"]


def test_public_zip_database_paths_read_old_zip_district_map_only() -> None:
    precomputed = PRECOMPUTED_PATH.read_text(encoding="utf-8")
    lowered = precomputed.lower()

    assert re.search(r"\bfrom\s+zip_district_map\b", lowered)
    assert not re.search(r"\bfrom\s+zip_district_mappings\b", lowered)
    assert not re.search(r"\bjoin\s+zip_district_mappings\b", lowered)

    assert "_get_db_zip_record(zip_code=zip_code)" in precomputed
    assert 'source_name="zip_district_map"' in precomputed
    assert 'source_currentness="stale_or_unknown"' in precomputed
    assert "stale_or_unknown_source=True" in precomputed
    assert "can_represent_multiple_districts=False" in precomputed
    assert 'ambiguity_detection_level="single_row"' in precomputed


def test_new_zip_district_mappings_table_is_not_wired_into_public_api_queries() -> None:
    query_sources = [
        path
        for path in API_ROOT.glob("*.py")
        if path.name not in {"__init__.py"} and path.is_file()
    ]
    query_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in query_sources)

    assert not re.search(r"\bfrom\s+zip_district_mappings\b", query_text)
    assert not re.search(r"\bjoin\s+zip_district_mappings\b", query_text)
