from pydantic import BaseModel, Field


class AnalysisConfig(BaseModel):
    # Severity Thresholds
    critical_severity_threshold: float = 80.0
    high_severity_threshold: float = 60.0
    medium_severity_threshold: float = 40.0

    # Risk Score Signal Weights (Total Sum = 100.0)
    weight_anomaly_score: float = 30.0
    weight_exfiltration_confidence: float = 30.0
    weight_model_sensitivity: float = 20.0
    weight_large_data_transfer: float = 10.0
    weight_cross_source_correlation: float = 10.0


default_analysis_config = AnalysisConfig()
