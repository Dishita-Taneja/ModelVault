import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.exceptions import ResourceNotFoundError
from app.core.logging import logger
from app.exfiltration.config import ExfiltrationConfig, default_exfiltration_config
from app.models import (
    AnomalyResult,
    DataLineage,
    ExfiltrationAssessment,
    MLModel,
    NormalizedEvent,
)
from app.schemas.exfiltration import ExfiltrationResponse

WEIGHT_EXTENSIONS = {".bin", ".safetensors", ".pt", ".onnx", ".pth", ".h5", ".ckpt", ".bin.gz"}


class ExfiltrationDetector:
    def __init__(self, db: AsyncSession, config: ExfiltrationConfig | None = None):
        self.db = db
        self.config = config or default_exfiltration_config

    async def assess_event(self, event_id: str) -> ExfiltrationResponse:
        logger.info(f"Evaluating Model-Weight Exfiltration for Event ID: {event_id}")

        # Fetch event
        event_res = await self.db.execute(select(NormalizedEvent).where(NormalizedEvent.event_id == event_id))
        event = event_res.scalars().first()
        if not event:
            raise ResourceNotFoundError(resource="NormalizedEvent", identifier=event_id)

        # Check existing assessment in DB
        existing_res = await self.db.execute(select(ExfiltrationAssessment).where(ExfiltrationAssessment.event_id == event_id))
        existing = existing_res.scalars().first()

        # Distinguish event type: MODEL_ACCESS vs MODEL_WEIGHT_DOWNLOAD vs MODEL_INFERENCE
        event_type = self._classify_event_type(event)

        # Fetch model metadata if available
        model_obj = None
        if event.model_id:
            m_res = await self.db.execute(select(MLModel).where(MLModel.model_id == event.model_id))
            model_obj = m_res.scalars().first()

        # Fetch anomaly result
        anom_res = await self.db.execute(select(AnomalyResult).where(AnomalyResult.event_id == event_id))
        anomaly_obj = anom_res.scalars().first()

        # Fetch related user session events
        session_events = await self._fetch_user_session_events(event)
        related_event_ids = [e.event_id for e in session_events]

        # Calculate Risk Score & Gather Evidence
        risk_score, evidence, reasons = self._calculate_risk_and_evidence(
            event=event,
            event_type=event_type,
            model_obj=model_obj,
            anomaly_obj=anomaly_obj,
            session_events=session_events
        )

        suspected = (risk_score >= self.config.exfiltration_risk_threshold) and (event_type == "MODEL_WEIGHT_DOWNLOAD" or event.bytes_transferred > 1e8)
        confidence = min(1.0, max(0.10, risk_score / 100.0))

        if suspected:
            main_reason = (
                f"High-confidence model weight exfiltration suspected for event '{event_id}' ({event.source} - {event.event_name}). "
                f"Risk score {risk_score:.1f}/100. Key factors: {'; '.join(reasons)}."
            )
        elif event_type == "MODEL_INFERENCE":
            main_reason = (
                f"Event '{event_id}' represents legitimate model inference invocation (InvokeEndpoint). "
                f"No binary model weight exfiltration or raw file download detected."
            )
        elif event_type == "MODEL_ACCESS":
            main_reason = (
                f"Event '{event_id}' represents model access/metadata discovery operation. "
                f"No direct model weight binary exfiltration detected."
            )
        else:
            main_reason = (
                f"Event '{event_id}' evaluated for exfiltration risk (Score: {risk_score:.1f}/100). "
                f"Activity does not meet exfiltration threshold."
            )

        # Persist to DB
        if not existing:
            exfil_db = ExfiltrationAssessment(
                event_id=event_id,
                weight_exfiltration_suspected=suspected,
                confidence=confidence,
                risk_score=risk_score,
                reason=main_reason,
                evidence=evidence,
                related_events=related_event_ids
            )
            self.db.add(exfil_db)
        else:
            existing.weight_exfiltration_suspected = suspected
            existing.confidence = confidence
            existing.risk_score = risk_score
            existing.reason = main_reason
            existing.evidence = evidence
            existing.related_events = related_event_ids

        # Lineage update
        lineage = DataLineage(
            event_id=event_id,
            stage="SUSPICIOUS_ALERT",
            source_file="exfiltration_detector",
            status="COMPLETED",
            details={"exfiltration_suspected": suspected, "confidence": confidence, "risk_score": risk_score}
        )
        self.db.add(lineage)

        await self.db.commit()

        return ExfiltrationResponse(
            event_id=event_id,
            weight_exfiltration_suspected=suspected,
            confidence=confidence,
            risk_score=risk_score,
            evidence=evidence,
            reason=main_reason,
            related_events=related_event_ids,
            assessed_at=datetime.datetime.now(datetime.timezone.utc)
        )

    def _classify_event_type(self, event: NormalizedEvent) -> str:
        src = str(event.source).upper()
        name = str(event.event_name)
        extra = event.extra if isinstance(event.extra, dict) else {}
        key = str(extra.get("key", ""))
        resource = str(event.resource_arn or "")

        if src == "MODEL" and name == "InvokeEndpoint":
            return "MODEL_INFERENCE"

        if src == "S3" and (any(ext in key or ext in resource for ext in WEIGHT_EXTENSIONS) or event.bytes_transferred >= self.config.medium_transfer_bytes_threshold):
            return "MODEL_WEIGHT_DOWNLOAD"

        if src in ["S3", "MODEL"]:
            return "MODEL_ACCESS"

        return "CLOUD_ACTIVITY"

    async def _fetch_user_session_events(self, target_event: NormalizedEvent) -> list[NormalizedEvent]:
        query = select(NormalizedEvent).order_by(NormalizedEvent.event_time_reconciled.asc())
        if target_event.user_id:
            query = query.where(
                (NormalizedEvent.user_id == target_event.user_id) | (NormalizedEvent.ip_address == target_event.ip_address)
            )
        elif target_event.ip_address:
            query = query.where(NormalizedEvent.ip_address == target_event.ip_address)

        res = await self.db.execute(query)
        return list(res.scalars().all())

    def _calculate_risk_and_evidence(
        self,
        event: NormalizedEvent,
        event_type: str,
        model_obj: MLModel | None,
        anomaly_obj: AnomalyResult | None,
        session_events: list[NormalizedEvent]
    ) -> tuple[float, list[str], list[str]]:
        score = 0.0
        evidence = []
        reasons = []

        # 1. Byte volume assessment
        if event.bytes_transferred >= self.config.large_transfer_bytes_threshold:
            score += self.config.weight_large_transfer
            gb = event.bytes_transferred / 1e9
            evidence.append(f"Unusually large data transfer: {event.bytes_transferred:,} bytes ({gb:.2f} GB) downloaded.")
            reasons.append(f"large data transfer of {gb:.1f}GB")
        elif event.bytes_transferred >= self.config.medium_transfer_bytes_threshold:
            score += self.config.weight_medium_transfer
            mb = event.bytes_transferred / 1e6
            evidence.append(f"Medium data transfer: {event.bytes_transferred:,} bytes ({mb:.1f} MB) downloaded.")
            reasons.append(f"transfer of {mb:.1f}MB")

        # 2. Model weight file extension check
        extra = event.extra if isinstance(event.extra, dict) else {}
        key = str(extra.get("key", ""))
        if any(ext in key for ext in WEIGHT_EXTENSIONS):
            score += self.config.weight_model_weight_file
            evidence.append(f"Direct model weight binary file access detected: S3 key '{key}'.")
            reasons.append(f"model weight file access ({key})")

        # 3. Model sensitivity assessment
        if model_obj:
            sens = str(model_obj.sensitivity_level).upper()
            if sens == "CRITICAL":
                score += self.config.weight_critical_sensitivity
                evidence.append(f"Target model '{model_obj.name}' ({model_obj.model_id}) has CRITICAL sensitivity level.")
                reasons.append(f"CRITICAL sensitivity model target ({model_obj.name})")
            elif sens == "HIGH":
                score += self.config.weight_high_sensitivity
                evidence.append(f"Target model '{model_obj.name}' ({model_obj.model_id}) has HIGH sensitivity level.")
                reasons.append("HIGH sensitivity model target")

        # 4. ML Anomaly Score contribution
        if anomaly_obj and anomaly_obj.anomaly_score >= 0.60:
            added = self.config.weight_anomaly_score * anomaly_obj.anomaly_score
            score += added
            evidence.append(f"ML Anomaly Detector flagged event with high anomaly score: {anomaly_obj.anomaly_score:.2f}.")
            reasons.append(f"anomalous behavior score {anomaly_obj.anomaly_score:.2f}")

        # 5. Privileged IAM Precursor activity
        iam_precursors = [e for e in session_events if e.source == "IAM" and e.event_name in ["CreateAccessKey", "AssumeRole"]]
        if iam_precursors:
            score += self.config.weight_privileged_iam_precursor
            pr_names = [f"{e.event_id} ({e.event_name})" for e in iam_precursors]
            evidence.append(f"Session preceded by privileged IAM operations: {', '.join(pr_names)}.")
            reasons.append("preceded by privileged IAM key creation/role assumption")

        # 6. External IP address check
        if event.ip_address and not (event.ip_address.startswith("10.") or event.ip_address.startswith("192.168.")):
            score += self.config.weight_unusual_ip
            evidence.append(f"Access performed from external/unusual IP address: {event.ip_address}.")
            reasons.append(f"external IP address {event.ip_address}")

        score = min(100.0, score)
        return score, evidence, reasons
