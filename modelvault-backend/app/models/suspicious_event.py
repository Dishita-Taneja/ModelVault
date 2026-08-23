import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SuspiciousEvent(Base):
    __tablename__ = "suspicious_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("normalized_events.event_id"), unique=True, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.user_id"), index=True, nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("ml_models.model_id"), index=True, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), index=True, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    weight_exfiltration_suspected: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    exfiltration_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    production_usage_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    related_events: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    investigation_timeline: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    detected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    event = relationship("NormalizedEvent")
