from pydantic import BaseModel


class ExfiltrationConfig(BaseModel):
    # Byte size thresholds
    large_transfer_bytes_threshold: int = 1_000_000_000  # 1 GB
    medium_transfer_bytes_threshold: int = 100_000_000   # 100 MB

    # Scoring weights
    weight_large_transfer: float = 30.0
    weight_medium_transfer: float = 15.0
    weight_model_weight_file: float = 25.0
    weight_critical_sensitivity: float = 25.0
    weight_high_sensitivity: float = 15.0
    weight_anomaly_score: float = 20.0
    weight_privileged_iam_precursor: float = 20.0
    weight_unusual_ip: float = 15.0
    weight_off_hours: float = 10.0

    # Decision threshold
    exfiltration_risk_threshold: float = 55.0


default_exfiltration_config = ExfiltrationConfig()
