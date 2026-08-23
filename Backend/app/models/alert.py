import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("normalized_events.event_id"), nullable=False)
    model_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("ml_models.model_id"), nullable=True)
    user_arn: Mapped[str | None] = mapped_column(String(255), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="CRITICAL", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    event = relationship("NormalizedEvent", back_populates="alerts")
