from pathlib import Path
import sys

from app.etl import fetch_sources


class StubResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "StubResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_build_house_clerk_roll_url_uses_official_pattern() -> None:
    assert (
        fetch_sources.build_house_clerk_roll_url(year=2025, roll_number=7)
        == "https://clerk.house.gov/evs/2025/roll007.xml"
    )


def test_build_senate_vote_url_uses_official_pattern() -> None:
    assert (
        fetch_sources.build_senate_vote_url(congress=119, session=1, roll_number=7)
        == "https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00007.xml"
    )


def test_build_congress_bill_url_uses_inferred_v3_pattern() -> None:
    assert (
        fetch_sources.build_congress_bill_url(
            congress=119,
            bill_type="hr",
            bill_number=120,
            api_key="demo-key",
        )
        == "https://api.congress.gov/v3/bill/119/hr/120?format=json&api_key=demo-key"
    )


def test_download_to_path_writes_payload(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["user_agent"] = request.get_header("User-agent")
        captured["timeout"] = timeout
        return StubResponse(b"<xml>payload</xml>")

    monkeypatch.setattr(fetch_sources, "urlopen", fake_urlopen)

    destination = tmp_path / "house" / "roll001.xml"
    result = fetch_sources.download_to_path(
        "https://example.com/roll001.xml",
        destination,
    )

    assert destination.read_text() == "<xml>payload</xml>"
    assert result.skipped is False
    assert result.bytes_written == len(b"<xml>payload</xml>")
    assert captured == {
        "url": "https://example.com/roll001.xml",
        "user_agent": "political-fingerprint/0.1",
        "timeout": 30,
    }


def test_download_to_path_skips_existing_file_when_not_overwriting(tmp_path: Path) -> None:
    destination = tmp_path / "senate" / "vote_001.xml"
    destination.parent.mkdir(parents=True)
    destination.write_text("cached")

    result = fetch_sources.download_to_path(
        "https://example.com/vote_001.xml",
        destination,
        overwrite=False,
    )

    assert result.skipped is True
    assert result.bytes_written == len("cached")


def test_resolve_congress_api_key_prefers_explicit_value(monkeypatch) -> None:
    monkeypatch.setenv("CONGRESS_API_KEY", "env-key")

    assert fetch_sources.resolve_congress_api_key("explicit-key") == "explicit-key"


def test_resolve_congress_api_key_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("CONGRESS_API_KEY", "env-key")

    assert fetch_sources.resolve_congress_api_key() == "env-key"


def test_main_supports_house_subcommand(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_sources.py",
            "house",
            "--year",
            "2025",
            "--roll",
            "1",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        fetch_sources,
        "fetch_house_clerk_roll_calls",
        lambda *, year, roll_numbers, output_dir, overwrite: [
            fetch_sources.DownloadResult(
                source_url="https://clerk.house.gov/evs/2025/roll001.xml",
                destination=output_dir / "roll001.xml",
                bytes_written=128,
                skipped=False,
            )
        ],
    )

    fetch_sources.main()
    output = capsys.readouterr().out

    assert "downloaded" in output
    assert "roll001.xml" in output


def test_main_defaults_house_output_dir(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["fetch_sources.py", "house", "--year", "2025", "--roll", "1"],
    )
    monkeypatch.setattr(
        fetch_sources,
        "fetch_house_clerk_roll_calls",
        lambda *, year, roll_numbers, output_dir, overwrite: [
            fetch_sources.DownloadResult(
                source_url="https://clerk.house.gov/evs/2025/roll001.xml",
                destination=output_dir / "roll001.xml",
                bytes_written=128,
                skipped=False,
            )
        ],
    )

    fetch_sources.main()
    output = capsys.readouterr().out

    assert str(fetch_sources.HOUSE_CLERK_CACHE_DIR / "roll001.xml") in output


def test_main_supports_senate_subcommand(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_sources.py",
            "senate",
            "--congress",
            "119",
            "--session",
            "1",
            "--roll",
            "3",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        fetch_sources,
        "fetch_senate_vote_files",
        lambda *, congress, session, roll_numbers, output_dir, overwrite: [
            fetch_sources.DownloadResult(
                source_url="https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00003.xml",
                destination=output_dir / "vote_003.xml",
                bytes_written=256,
                skipped=False,
            )
        ],
    )

    fetch_sources.main()
    output = capsys.readouterr().out

    assert "downloaded" in output
    assert "vote_003.xml" in output


def test_main_supports_congress_bill_subcommand(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_sources.py",
            "congress-bill",
            "--congress",
            "119",
            "--bill-type",
            "hr",
            "--bill-number",
            "120",
            "--api-key",
            "demo-key",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        fetch_sources,
        "fetch_congress_bill_metadata",
        lambda *, congress, bill_type, bill_number, api_key, output_dir, overwrite: fetch_sources.DownloadResult(
            source_url="https://api.congress.gov/v3/bill/119/hr/120?format=json&api_key=demo-key",
            destination=output_dir / "119_hr_120.json",
            bytes_written=512,
            skipped=False,
        ),
    )

    fetch_sources.main()
    output = capsys.readouterr().out

    assert "downloaded" in output
    assert "119_hr_120.json" in output
