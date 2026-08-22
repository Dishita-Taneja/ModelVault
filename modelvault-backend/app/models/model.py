import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    model_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    framework: Mapped[str] = mapped_column(String(64), default="PyTorch", nullable=False)
    s3_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    sensitivity_level: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)
    owner_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.user_id"), nullable=True)
    owner_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    owner = relationship("User", back_populates="models_owned")
    events = relationship("NormalizedEvent", back_populates="model", cascade="all, delete-orphan")
