from pydantic_settings import BaseSettings, SettingsConfigDict


class ReconciliationConfig(BaseSettings):
    correlation_window_seconds: float = 300.0  # 5 minute correlation window
    max_clock_skew_seconds: float = 3600.0      # 1 hour max allowable skew
    high_confidence_threshold: float = 0.90
    medium_confidence_threshold: float = 0.70

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


default_reconciliation_config = ReconciliationConfig()
