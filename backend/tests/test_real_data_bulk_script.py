import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_real_data_bulk.py"
SPEC = importlib.util.spec_from_file_location("run_real_data_bulk", SCRIPT_PATH)
run_real_data_bulk = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(run_real_data_bulk)


def test_expand_rolls_merges_explicit_and_ranges() -> None:
    assert run_real_data_bulk.expand_rolls(
        explicit_rolls=[5, 7],
        range_pairs=[(1, 3), (7, 8)],
    ) == [1, 2, 3, 5, 7, 8]


def test_parse_range_accepts_start_end_shape() -> None:
    assert run_real_data_bulk.parse_range("10:25") == (10, 25)
