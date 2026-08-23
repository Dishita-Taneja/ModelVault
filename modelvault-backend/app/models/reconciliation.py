import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("normalized_events.event_id"), unique=True, index=True, nullable=False)
    log_source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    event_time_raw: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_time_normalized: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_time_reconciled: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timestamp_offset_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reconciliation_method: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_for_change: Mapped[str] = mapped_column(Text, nullable=False)
    source_events_used: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    reconciled_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    event = relationship("NormalizedEvent")
