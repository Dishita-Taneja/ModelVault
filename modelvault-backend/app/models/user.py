import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.model import MLModel
    from app.models.access_event import AccessEvent


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Data Scientist",
    )
    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="ML Engineering",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owned_models: Mapped[list["MLModel"]] = relationship(
        "MLModel",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    access_events: Mapped[list["AccessEvent"]] = relationship(
        "AccessEvent",
        back_populates="user",
    )
