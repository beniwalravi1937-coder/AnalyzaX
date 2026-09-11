from backend.app.core.config import settings


def test_settings_defaults():
    assert settings.APP_NAME == "AnalyzaX"
    assert settings.BACKEND_PORT == 8000
    assert len(settings.ALLOWED_CORS_ORIGINS) > 0
    assert settings.DUCKDB_DATABASE_PATH == ":memory:"
    assert "data/uploads" in settings.DATA_UPLOADS_DIR.replace("\\", "/")
