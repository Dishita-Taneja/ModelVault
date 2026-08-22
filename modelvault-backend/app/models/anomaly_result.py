import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.access_event import AccessEvent


class AnomalyResult(Base):
    __tablename__ = "anomaly_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    access_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("access_events.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    anomaly_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    reviewed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    flagged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    access_event: Mapped["AccessEvent"] = relationship(
        "AccessEvent",
        back_populates="anomaly_result",
    )

    __table_args__ = (
        Index("ix_anomaly_results_score_desc", anomaly_score.desc()),
    )
