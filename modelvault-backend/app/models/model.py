import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.access_event import AccessEvent


class MLModel(Base):
    __tablename__ = "models"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    sensitivity_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MEDIUM",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_models",
    )
    access_events: Mapped[list["AccessEvent"]] = relationship(
        "AccessEvent",
        back_populates="model",
        cascade="all, delete-orphan",
    )
