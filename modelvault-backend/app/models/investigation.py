import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InvestigationIncident(Base):
    __tablename__ = "investigation_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # USER, MODEL, EVENT
    target_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="HIGH", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    total_events_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    anomalous_events_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_anomaly_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    timeline: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )
