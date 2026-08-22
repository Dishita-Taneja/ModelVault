import datetime
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RawLog(Base):
    __tablename__ = "raw_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    log_source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # IAM, EC2, S3, MODEL, CSV
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc)
    )
