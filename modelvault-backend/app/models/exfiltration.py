import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExfiltrationAssessment(Base):
    __tablename__ = "exfiltration_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("normalized_events.event_id"), unique=True, index=True, nullable=False)
    weight_exfiltration_suspected: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    related_events: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    assessed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    event = relationship("NormalizedEvent")
