import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AnomalyResult(Base):
    __tablename__ = "anomaly_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("normalized_events.event_id"), unique=True, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.user_id"), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("ml_models.model_id"), nullable=True)
    source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    feature_values: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), default="v1.0.0", nullable=False)
    detected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    event = relationship("NormalizedEvent")
