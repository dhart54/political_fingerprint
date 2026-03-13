import sys

from app.etl import run_all


def test_run_all_defaults_to_persistent_etl(monkeypatch, capsys) -> None:
    called = {}

    monkeypatch.setattr(sys, "argv", ["run_all.py", "--fixtures"])
    monkeypatch.setattr(
        "app.etl.run_all.run_etl_and_persist",
        lambda *, source, as_of: {"mode": "persist", "source": source, "as_of": as_of.isoformat()},
    )
    monkeypatch.setattr(
        "app.etl.run_all.run_etl",
        lambda *, source, as_of: {"mode": "compute", "source": source, "as_of": as_of.isoformat()},
    )

    run_all.main()
    output = capsys.readouterr().out

    assert "persist" in output


def test_run_all_supports_compute_only_flag(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["run_all.py", "--fixtures", "--compute-only"])
    monkeypatch.setattr(
        "app.etl.run_all.run_etl_and_persist",
        lambda *, source, as_of: {"mode": "persist", "source": source, "as_of": as_of.isoformat()},
    )
    monkeypatch.setattr(
        "app.etl.run_all.run_etl",
        lambda *, source, as_of: {"mode": "compute", "source": source, "as_of": as_of.isoformat()},
    )

    run_all.main()
    output = capsys.readouterr().out

    assert "compute" in output
