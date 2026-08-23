"""ModelVault Cross-Source Security Correlation Engine Package"""
from app.correlation.config import CorrelationConfig, default_correlation_config
from app.correlation.engine import CrossSourceCorrelationEngine

__all__ = [
    "CorrelationConfig",
    "CrossSourceCorrelationEngine",
    "default_correlation_config"
]
