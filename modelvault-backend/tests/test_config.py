from app.core.config import settings


def test_settings_load():
    assert settings.PROJECT_NAME == "ModelVault"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0
    assert "postgresql" in settings.async_database_url
