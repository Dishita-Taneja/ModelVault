"""ModelVault Cross-Source Security Correlation Engine Package"""
from app.correlation.engine import CrossSourceCorrelationEngine
from app.correlation.config import CorrelationConfig, default_correlation_config

__all__ = [
    "CrossSourceCorrelationEngine",
    "CorrelationConfig",
    "default_correlation_config"
]
