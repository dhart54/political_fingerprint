from app.main import get_cors_origins


def test_get_cors_origins_includes_local_defaults(monkeypatch) -> None:
    monkeypatch.delenv("FRONTEND_ORIGINS", raising=False)

    assert get_cors_origins() == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_get_cors_origins_adds_configured_frontend_origins(monkeypatch) -> None:
    monkeypatch.setenv(
        "FRONTEND_ORIGINS",
        "https://political-fingerprint.vercel.app, https://preview.example.com ",
    )

    assert get_cors_origins() == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://political-fingerprint.vercel.app",
        "https://preview.example.com",
    ]
