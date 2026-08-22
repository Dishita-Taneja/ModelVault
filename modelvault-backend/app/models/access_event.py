import uuid
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.model import MLModel
    from app.models.anomaly_result import AnomalyResult


class AccessEvent(Base):
    __tablename__ = "access_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="API_GATEWAY",
    )
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
        default=dict,
    )

    # Relationships
    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="access_events",
    )
    model: Mapped["MLModel"] = relationship(
        "MLModel",
        back_populates="access_events",
    )
    anomaly_result: Mapped["AnomalyResult | None"] = relationship(
        "AnomalyResult",
        back_populates="access_event",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_access_events_user_model", "user_id", "model_id"),
        Index("ix_access_events_timestamp_desc", timestamp.desc()),
    )
