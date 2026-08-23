import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import Base
from app.core.logging import logger
from app.ingestion.loaders import load_csv_file, load_json_file
from app.ingestion.normalizer import (
    normalize_ec2_log,
    normalize_iam_log,
    normalize_model_access_log,
    normalize_s3_log,
    parse_datetime,
)
from app.ingestion.schemas import (
    EC2LogItem,
    IAMLogItem,
    ModelAccessLogItem,
    ModelItem,
    S3LogItem,
    UserItem,
)
from app.models import Alert, DataLineage, MLModel, NormalizedEvent, RawLog, User
from app.schemas.event import IngestionReport


class IngestionService:
    def __init__(self, data_dir: Path | None = None):
        if data_dir is None:
            self.data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)

    async def run(self, db: AsyncSession) -> IngestionReport:
        report = IngestionReport()
        logger.info(f"Starting ingestion pipeline from data directory: {self.data_dir}")

        # 1. Ingest Users
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            report.total_files_processed += 1
            await self._ingest_users(db, users_file, report)

        # 2. Ingest ML Models
        models_file = self.data_dir / "models.json"
        if models_file.exists():
            report.total_files_processed += 1
            await self._ingest_models(db, models_file, report)

        # Build correlation maps
        user_map = await self._build_user_map(db)
        ip_user_map = await self._build_ip_user_map(db)
        s3_model_map = await self._build_s3_model_map(db)

        # 3. Ingest IAM Logs
        iam_file = self.data_dir / "iam_logs.json"
        if iam_file.exists():
            report.total_files_processed += 1
            await self._ingest_iam_logs(db, iam_file, user_map, report)

        # 4. Ingest EC2 Logs
        ec2_file = self.data_dir / "ec2_logs.json"
        if ec2_file.exists():
            report.total_files_processed += 1
            await self._ingest_ec2_logs(db, ec2_file, ip_user_map, report)

        # 5. Ingest S3 Logs
        s3_file = self.data_dir / "s3_logs.json"
        if s3_file.exists():
            report.total_files_processed += 1
            await self._ingest_s3_logs(db, s3_file, user_map, s3_model_map, report)

        # 6. Ingest Model Access Logs
        model_access_file = self.data_dir / "model_access_logs.json"
        if model_access_file.exists():
            report.total_files_processed += 1
            await self._ingest_model_access_logs(db, model_access_file, user_map, report)

        # 7. Sync & Ingest Reference Normalized CSV Dataset
        csv_file = self.data_dir / "normalized_events.csv"
        if csv_file.exists():
            report.total_files_processed += 1
            await self._ingest_normalized_csv(db, csv_file, report)

        logger.info(f"Ingestion pipeline completed: {report}")
        return report

    async def _ingest_users(self, db: AsyncSession, file_path: Path, report: IngestionReport):
        raw_users = load_json_file(file_path)
        source_key = "users.json"
        report.records_processed[source_key] = len(raw_users)
        report.records_inserted[source_key] = 0
        report.duplicates_skipped[source_key] = 0
        report.invalid_records[source_key] = 0

        for item in raw_users:
            try:
                validated = UserItem(**item)
            except Exception as e:
                report.invalid_records[source_key] += 1
                report.errors.append(f"Invalid User record {item}: {e}")
                continue

            existing = await db.get(User, validated.user_id)
            if existing:
                report.duplicates_skipped[source_key] += 1
                continue

            user_obj = User(
                user_id=validated.user_id,
                username=validated.username,
                email=validated.email,
                role=validated.role,
                is_active=validated.is_active,
                created_at=parse_datetime(validated.created_at)
            )
            db.add(user_obj)
            report.records_inserted[source_key] += 1

        await db.commit()

    async def _ingest_models(self, db: AsyncSession, file_path: Path, report: IngestionReport):
        raw_models = load_json_file(file_path)
        source_key = "models.json"
        report.records_processed[source_key] = len(raw_models)
        report.records_inserted[source_key] = 0
        report.duplicates_skipped[source_key] = 0
        report.invalid_records[source_key] = 0

        for item in raw_models:
            try:
                validated = ModelItem(**item)
            except Exception as e:
                report.invalid_records[source_key] += 1
                report.errors.append(f"Invalid Model record {item}: {e}")
                continue

            existing = await db.get(MLModel, validated.model_id)
            if existing:
                report.duplicates_skipped[source_key] += 1
                continue

            model_obj = MLModel(
                model_id=validated.model_id,
                name=validated.name,
                description=validated.description,
                framework=validated.framework,
                s3_uri=validated.s3_uri,
                sensitivity_level=validated.sensitivity_level,
                owner_email=validated.owner_email,
                created_at=parse_datetime(validated.created_at)
            )
            db.add(model_obj)
            report.records_inserted[source_key] += 1

        await db.commit()

    async def _ingest_iam_logs(self, db: AsyncSession, file_path: Path, user_map: dict[str, str], report: IngestionReport):
        raw_logs = load_json_file(file_path)
        source_key = "iam_logs.json"
        report.records_processed[source_key] = len(raw_logs)
        report.records_inserted[source_key] = 0
        report.duplicates_skipped[source_key] = 0
        report.invalid_records[source_key] = 0

        for item in raw_logs:
            try:
                validated = IAMLogItem(**item)
            except Exception as e:
                report.invalid_records[source_key] += 1
                report.errors.append(f"Invalid IAM log {item}: {e}")
                continue

            event_id = validated.event_id
            existing = await db.get(NormalizedEvent, event_id)
            if existing:
                report.duplicates_skipped[source_key] += 1
                continue

            raw_entry = RawLog(event_id=event_id, log_source="IAM", raw_payload=item)
            db.add(raw_entry)

            norm_event = normalize_iam_log(item, user_map)
            event_obj = NormalizedEvent(
                event_id=norm_event.event_id,
                source=norm_event.source,
                event_time_raw=norm_event.event_time_raw,
                event_time_reconciled=norm_event.event_time_reconciled,
                user_id=norm_event.user_id,
                user_name=norm_event.user_name,
                ip_address=norm_event.ip_address,
                event_name=norm_event.event_name,
                model_id=norm_event.model_id,
                region=norm_event.region,
                status=norm_event.status,
                bytes_transferred=norm_event.bytes_transferred,
                risk_score=norm_event.risk_score,
                anomaly_flag=norm_event.anomaly_flag,
                extra=norm_event.extra
            )
            db.add(event_obj)

            self._add_lineage(db, event_id, "iam_logs.json", "RAW_INGESTION")
            self._add_lineage(db, event_id, "iam_logs.json", "NORMALIZATION")
            self._add_lineage(db, event_id, "iam_logs.json", "RECONCILIATION")

            report.records_inserted[source_key] += 1

        await db.commit()

    async def _ingest_ec2_logs(self, db: AsyncSession, file_path: Path, ip_user_map: dict[str, str], report: IngestionReport):
        raw_logs = load_json_file(file_path)
        source_key = "ec2_logs.json"
        report.records_processed[source_key] = len(raw_logs)
        report.records_inserted[source_key] = 0
        report.duplicates_skipped[source_key] = 0
        report.invalid_records[source_key] = 0

        for item in raw_logs:
            try:
                validated = EC2LogItem(**item)
            except Exception as e:
                report.invalid_records[source_key] += 1
                report.errors.append(f"Invalid EC2 log {item}: {e}")
                continue

            event_id = validated.event_id
            existing = await db.get(NormalizedEvent, event_id)
            if existing:
                report.duplicates_skipped[source_key] += 1
                continue

            raw_entry = RawLog(event_id=event_id, log_source="EC2", raw_payload=item)
            db.add(raw_entry)

            norm_event = normalize_ec2_log(item, ip_user_map)
            event_obj = NormalizedEvent(
                event_id=norm_event.event_id,
                source=norm_event.source,
                event_time_raw=norm_event.event_time_raw,
                event_time_reconciled=norm_event.event_time_reconciled,
                user_id=norm_event.user_id,
                user_name=norm_event.user_name,
                ip_address=norm_event.ip_address,
                event_name=norm_event.event_name,
                model_id=norm_event.model_id,
                region=norm_event.region,
                status=norm_event.status,
                bytes_transferred=norm_event.bytes_transferred,
                risk_score=norm_event.risk_score,
                anomaly_flag=norm_event.anomaly_flag,
                extra=norm_event.extra
            )
            db.add(event_obj)

            self._add_lineage(db, event_id, "ec2_logs.json", "RAW_INGESTION")
            self._add_lineage(db, event_id, "ec2_logs.json", "NORMALIZATION")
            self._add_lineage(db, event_id, "ec2_logs.json", "RECONCILIATION")

            report.records_inserted[source_key] += 1

        await db.commit()

    async def _ingest_s3_logs(
        self,
        db: AsyncSession,
        file_path: Path,
        user_map: dict[str, str],
        s3_model_map: dict[str, str],
        report: IngestionReport
    ):
        raw_logs = load_json_file(file_path)
        source_key = "s3_logs.json"
        report.records_processed[source_key] = len(raw_logs)
        report.records_inserted[source_key] = 0
        report.duplicates_skipped[source_key] = 0
        report.invalid_records[source_key] = 0

        for item in raw_logs:
            try:
                validated = S3LogItem(**item)
            except Exception as e:
                report.invalid_records[source_key] += 1
                report.errors.append(f"Invalid S3 log {item}: {e}")
                continue

            event_id = validated.event_id
            existing = await db.get(NormalizedEvent, event_id)
            if existing:
                report.duplicates_skipped[source_key] += 1
                continue

            raw_entry = RawLog(event_id=event_id, log_source="S3", raw_payload=item)
            db.add(raw_entry)

            norm_event = normalize_s3_log(item, user_map, s3_model_map)
            event_obj = NormalizedEvent(
                event_id=norm_event.event_id,
                source=norm_event.source,
                event_time_raw=norm_event.event_time_raw,
                event_time_reconciled=norm_event.event_time_reconciled,
                user_id=norm_event.user_id,
                user_name=norm_event.user_name,
                ip_address=norm_event.ip_address,
                event_name=norm_event.event_name,
                model_id=norm_event.model_id,
                region=norm_event.region,
                status=norm_event.status,
                bytes_transferred=norm_event.bytes_transferred,
                risk_score=norm_event.risk_score,
                anomaly_flag=norm_event.anomaly_flag,
                extra=norm_event.extra
            )
            db.add(event_obj)

            self._add_lineage(db, event_id, "s3_logs.json", "RAW_INGESTION")
            self._add_lineage(db, event_id, "s3_logs.json", "NORMALIZATION")
            self._add_lineage(db, event_id, "s3_logs.json", "RECONCILIATION")

            report.records_inserted[source_key] += 1

        await db.commit()

    async def _ingest_model_access_logs(self, db: AsyncSession, file_path: Path, user_map: dict[str, str], report: IngestionReport):
        raw_logs = load_json_file(file_path)
        source_key = "model_access_logs.json"
        report.records_processed[source_key] = len(raw_logs)
        report.records_inserted[source_key] = 0
        report.duplicates_skipped[source_key] = 0
        report.invalid_records[source_key] = 0

        for item in raw_logs:
            try:
                validated = ModelAccessLogItem(**item)
            except Exception as e:
                report.invalid_records[source_key] += 1
                report.errors.append(f"Invalid Model Access log {item}: {e}")
                continue

            event_id = validated.event_id
            existing = await db.get(NormalizedEvent, event_id)
            if existing:
                report.duplicates_skipped[source_key] += 1
                continue

            raw_entry = RawLog(event_id=event_id, log_source="MODEL", raw_payload=item)
            db.add(raw_entry)

            norm_event = normalize_model_access_log(item, user_map)
            event_obj = NormalizedEvent(
                event_id=norm_event.event_id,
                source=norm_event.source,
                event_time_raw=norm_event.event_time_raw,
                event_time_reconciled=norm_event.event_time_reconciled,
                user_id=norm_event.user_id,
                user_name=norm_event.user_name,
                ip_address=norm_event.ip_address,
                event_name=norm_event.event_name,
                model_id=norm_event.model_id,
                region=norm_event.region,
                status=norm_event.status,
                bytes_transferred=norm_event.bytes_transferred,
                risk_score=norm_event.risk_score,
                anomaly_flag=norm_event.anomaly_flag,
                extra=norm_event.extra
            )
            db.add(event_obj)

            self._add_lineage(db, event_id, "model_access_logs.json", "RAW_INGESTION")
            self._add_lineage(db, event_id, "model_access_logs.json", "NORMALIZATION")
            self._add_lineage(db, event_id, "model_access_logs.json", "RECONCILIATION")

            report.records_inserted[source_key] += 1

        await db.commit()

    async def _ingest_normalized_csv(self, db: AsyncSession, file_path: Path, report: IngestionReport):
        df = load_csv_file(file_path)
        source_key = "normalized_events.csv"
        report.records_processed[source_key] = len(df)
        report.records_inserted[source_key] = 0
        report.duplicates_skipped[source_key] = 0
        report.invalid_records[source_key] = 0

        for _, row in df.iterrows():
            event_id = str(row["event_id"])
            existing = await db.get(NormalizedEvent, event_id)
            if existing:
                existing.risk_score = float(row["risk_score"]) if "risk_score" in row and not pd.isna(row["risk_score"]) else existing.risk_score
                existing.anomaly_flag = bool(row["anomaly_flag"]) if "anomaly_flag" in row and not pd.isna(row["anomaly_flag"]) else existing.anomaly_flag
                
                if existing.anomaly_flag:
                    alert_id = f"alt-{event_id}"
                    alert_existing = await db.get(Alert, alert_id)
                    if not alert_existing:
                        alert_obj = Alert(
                            alert_id=alert_id,
                            event_id=event_id,
                            model_id=existing.model_id,
                            user_arn=existing.user_name,
                            risk_score=existing.risk_score,
                            severity="CRITICAL" if existing.risk_score > 0.9 else "HIGH",
                            title=f"Suspicious {existing.source} Activity Detected",
                            description=f"Anomalous action '{existing.event_name}' performed by {existing.user_name} from IP {existing.ip_address}.",
                            status="OPEN"
                        )
                        db.add(alert_obj)
                        self._add_lineage(db, event_id, "normalized_events.csv", "SUSPICIOUS_ALERT")

                report.duplicates_skipped[source_key] += 1
                continue

            ts = parse_datetime(str(row["timestamp"]))
            rec_ts = parse_datetime(str(row["reconciled_timestamp"]))
            
            model_id_val = str(row["model_id"]) if not pd.isna(row.get("model_id")) else None
            user_id_val = str(row["user_id"]) if not pd.isna(row.get("user_id")) else None
            user_arn_val = str(row["user_arn"]) if not pd.isna(row.get("user_arn")) else None
            ip_val = str(row["source_ip"]) if not pd.isna(row.get("source_ip")) else None

            event_obj = NormalizedEvent(
                event_id=event_id,
                source=str(row["log_source"]),
                event_time_raw=ts,
                event_time_reconciled=rec_ts,
                user_id=user_id_val,
                user_name=user_arn_val,
                ip_address=ip_val,
                event_name=str(row["action"]),
                model_id=model_id_val,
                region="us-east-1",
                status=str(row.get("status", "SUCCESS")),
                bytes_transferred=int(row["bytes_transferred"]) if not pd.isna(row.get("bytes_transferred")) else 0,
                risk_score=float(row["risk_score"]) if not pd.isna(row.get("risk_score")) else 0.0,
                anomaly_flag=bool(row["anomaly_flag"]) if not pd.isna(row.get("anomaly_flag")) else False,
                extra={"resource_arn": str(row.get("resource_arn")) if not pd.isna(row.get("resource_arn")) else None}
            )
            db.add(event_obj)

            self._add_lineage(db, event_id, "normalized_events.csv", "RAW_INGESTION")
            self._add_lineage(db, event_id, "normalized_events.csv", "NORMALIZATION")

            if event_obj.anomaly_flag:
                alert_id = f"alt-{event_id}"
                alert_obj = Alert(
                    alert_id=alert_id,
                    event_id=event_id,
                    model_id=model_id_val,
                    user_arn=user_arn_val,
                    risk_score=event_obj.risk_score,
                    severity="CRITICAL" if event_obj.risk_score > 0.9 else "HIGH",
                    title=f"Suspicious {event_obj.source} Activity Detected",
                    description=f"Anomalous action '{event_obj.event_name}' performed by {user_arn_val} from IP {ip_val}.",
                    status="OPEN"
                )
                db.add(alert_obj)
                self._add_lineage(db, event_id, "normalized_events.csv", "SUSPICIOUS_ALERT")

            report.records_inserted[source_key] += 1

        await db.commit()

    def _add_lineage(self, db: AsyncSession, event_id: str, source_file: str, stage: str):
        lineage = DataLineage(
            event_id=event_id,
            stage=stage,
            source_file=source_file,
            status="COMPLETED",
            details={"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        )
        db.add(lineage)

    async def _build_user_map(self, db: AsyncSession) -> dict[str, str]:
        res = await db.execute(select(User))
        users = res.scalars().all()
        user_map = {}
        for u in users:
            user_map[u.username] = u.user_id
            user_map[u.email] = u.user_id
        return user_map

    async def _build_ip_user_map(self, db: AsyncSession) -> dict[str, str]:
        res = await db.execute(select(NormalizedEvent).where(NormalizedEvent.source == "IAM"))
        iam_events = res.scalars().all()
        ip_map = {}
        for evt in iam_events:
            if evt.ip_address and evt.user_id:
                ip_map[evt.ip_address] = evt.user_id
        return ip_map

    async def _build_s3_model_map(self, db: AsyncSession) -> dict[str, str]:
        res = await db.execute(select(MLModel))
        models = res.scalars().all()
        s3_map = {}
        for m in models:
            s3_map[m.s3_uri] = m.model_id
            if "/" in m.s3_uri:
                key = m.s3_uri.split("/")[-1]
                s3_map[key] = m.model_id
        return s3_map


async def run_ingestion_pipeline(data_dir: Path | None = None) -> IngestionReport:
    db_url = settings.async_database_url
    try:
        engine_inst = create_async_engine(db_url, echo=False, future=True)
        async with engine_inst.connect() as conn:
            pass
    except Exception as e:
        logger.warning(f"PostgreSQL connection fallback ({e}). Using local SQLite database 'modelvault_dev.db'...")
        db_url = "sqlite+aiosqlite:///./modelvault_dev.db"
        engine_inst = create_async_engine(db_url, echo=False, future=True)

    async with engine_inst.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(bind=engine_inst, expire_on_commit=False)

    service = IngestionService(data_dir=data_dir)
    async with SessionLocal() as session:
        report = await service.run(session)

    await engine_inst.dispose()
    return report
