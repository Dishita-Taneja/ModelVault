from pydantic import BaseModel


class CorrelationConfig(BaseModel):
    # Temporal windows (in minutes) by source
    iam_window_minutes: int = 60
    ec2_window_minutes: int = 45
    s3_window_minutes: int = 30
    model_window_minutes: int = 15

    # Weight factors for correlation matching
    weight_user_match: float = 0.40
    weight_ip_match: float = 0.30
    weight_model_match: float = 0.30
    weight_temporal_proximity: float = 0.20

    min_correlation_threshold: float = 0.30


default_correlation_config = CorrelationConfig()
