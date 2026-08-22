import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, BigInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class NormalizedEvent(Base):
    __tablename__ = "normalized_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # IAM, EC2, S3, MODEL
    event_time_raw: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_time_reconciled: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.user_id"), nullable=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)  # user_arn / username
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)  # source_ip
    event_name: Mapped[str] = mapped_column(String(128), nullable=False)  # action
    model_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("ml_models.model_id"), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(32), default="us-east-1", nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)
    bytes_transferred: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    extra: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # source-specific extra fields

    # Aliases / Compatibility Properties
    @property
    def timestamp(self) -> datetime.datetime:
        return self.event_time_raw

    @property
    def reconciled_timestamp(self) -> datetime.datetime:
        return self.event_time_reconciled

    @property
    def log_source(self) -> str:
        return self.source

    @property
    def user_arn(self) -> Optional[str]:
        return self.user_name

    @property
    def source_ip(self) -> Optional[str]:
        return self.ip_address

    @property
    def action(self) -> str:
        return self.event_name

    @property
    def resource_arn(self) -> Optional[str]:
        return self.extra.get("resource_arn") if isinstance(self.extra, dict) else None

    model = relationship("MLModel", back_populates="events")
    alerts = relationship("Alert", back_populates="event", cascade="all, delete-orphan")
    lineage_records = relationship("DataLineage", back_populates="event", cascade="all, delete-orphan")
