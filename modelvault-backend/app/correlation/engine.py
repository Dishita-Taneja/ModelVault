import datetime
import uuid
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import (
    NormalizedEvent, User, MLModel, AnomalyResult, ReconciliationResult, InvestigationIncident, DataLineage
)
from app.schemas.investigation import TimelineEvent, InvestigationTimelineResponse
from app.correlation.config import CorrelationConfig, default_correlation_config
from app.core.logging import logger
from app.core.exceptions import ResourceNotFoundError


class CrossSourceCorrelationEngine:
    def __init__(self, db: AsyncSession, config: Optional[CorrelationConfig] = None):
        self.db = db
        self.config = config or default_correlation_config

    async def correlate_by_model(self, model_id: str) -> InvestigationTimelineResponse:
        logger.info(f"Running Cross-Source Correlation for Model ID: {model_id}")

        # Fetch model details
        model_res = await self.db.execute(select(MLModel).where(MLModel.model_id == model_id))
        model_obj = model_res.scalars().first()
        if not model_obj:
            raise ResourceNotFoundError(resource="MLModel", identifier=model_id)

        # Fetch all events
        all_events = await self._fetch_all_events()
        anomaly_map = await self._fetch_anomaly_map()
        reconcile_map = await self._fetch_reconcile_map()
        exfiltration_map = await self._fetch_exfiltration_map()

        # Find direct & indirect model events
        correlated: Set[NormalizedEvent] = set()
        matched_users: Set[str] = set()
        matched_ips: Set[str] = set()

        for evt in all_events:
            # Check direct model_id match
            if evt.model_id == model_id:
                correlated.add(evt)
                if evt.user_id: matched_users.add(evt.user_id)
                if evt.user_name: matched_users.add(evt.user_name)
                if evt.ip_address: matched_ips.add(evt.ip_address)

            # Check S3 URI key match
            extra = evt.extra if isinstance(evt.extra, dict) else {}
            s3_key = str(extra.get("key", ""))
            if model_obj.s3_uri and any(part in s3_key for part in model_obj.s3_uri.split("/") if part.endswith((".bin", ".safetensors", ".pt", ".json"))):
                correlated.add(evt)
                if evt.user_id: matched_users.add(evt.user_id)
                if evt.user_name: matched_users.add(evt.user_name)
                if evt.ip_address: matched_ips.add(evt.ip_address)

        # Expand correlation to user and IP session events
        for evt in all_events:
            if evt.user_id in matched_users or evt.user_name in matched_users or evt.ip_address in matched_ips:
                correlated.add(evt)

        timeline = self._build_timeline(
            events=list(correlated),
            anomaly_map=anomaly_map,
            reconcile_map=reconcile_map,
            primary_target=f"model:{model_id}",
            exfiltration_map=exfiltration_map
        )

        return await self._persist_and_respond(
            target_type="MODEL",
            target_id=model_id,
            timeline=timeline,
            summary=f"Reconstructed incident timeline for ML Model '{model_obj.name}' ({model_id}) across {len(timeline)} correlated events."
        )

    async def correlate_by_user(self, user_id: str) -> InvestigationTimelineResponse:
        logger.info(f"Running Cross-Source Correlation for User ID: {user_id}")

        user_res = await self.db.execute(select(User).where(User.user_id == user_id))
        user_obj = user_res.scalars().first()

        username = user_obj.username if user_obj else user_id

        all_events = await self._fetch_all_events()
        anomaly_map = await self._fetch_anomaly_map()
        reconcile_map = await self._fetch_reconcile_map()
        exfiltration_map = await self._fetch_exfiltration_map()

        correlated: Set[NormalizedEvent] = set()
        user_ips: Set[str] = set()

        for evt in all_events:
            if evt.user_id == user_id or (evt.user_name and username in evt.user_name):
                correlated.add(evt)
                if evt.ip_address:
                    user_ips.add(evt.ip_address)

        for evt in all_events:
            if evt.ip_address in user_ips:
                correlated.add(evt)

        timeline = self._build_timeline(
            events=list(correlated),
            anomaly_map=anomaly_map,
            reconcile_map=reconcile_map,
            primary_target=f"user:{user_id}",
            exfiltration_map=exfiltration_map
        )

        return await self._persist_and_respond(
            target_type="USER",
            target_id=user_id,
            timeline=timeline,
            summary=f"Reconstructed incident timeline for User '{username}' ({user_id}) across {len(timeline)} correlated multi-source events."
        )

    async def correlate_by_event(self, event_id: str) -> InvestigationTimelineResponse:
        logger.info(f"Running Cross-Source Correlation for Event ID: {event_id}")

        event_res = await self.db.execute(select(NormalizedEvent).where(NormalizedEvent.event_id == event_id))
        target_evt = event_res.scalars().first()
        if not target_evt:
            raise ResourceNotFoundError(resource="NormalizedEvent", identifier=event_id)

        all_events = await self._fetch_all_events()
        anomaly_map = await self._fetch_anomaly_map()
        reconcile_map = await self._fetch_reconcile_map()
        exfiltration_map = await self._fetch_exfiltration_map()

        correlated: Set[NormalizedEvent] = {target_evt}
        target_time = target_evt.event_time_reconciled

        for evt in all_events:
            time_diff_min = abs((evt.event_time_reconciled - target_time).total_seconds()) / 60.0

            # Get source window
            max_window = getattr(self.config, f"{evt.source.lower()}_window_minutes", 30)

            if time_diff_min <= max_window:
                is_match = False
                if target_evt.user_id and evt.user_id == target_evt.user_id:
                    is_match = True
                if target_evt.user_name and evt.user_name and target_evt.user_name in evt.user_name:
                    is_match = True
                if target_evt.ip_address and evt.ip_address == target_evt.ip_address:
                    is_match = True
                if target_evt.model_id and evt.model_id == target_evt.model_id:
                    is_match = True

                if is_match:
                    correlated.add(evt)

        timeline = self._build_timeline(
            events=list(correlated),
            anomaly_map=anomaly_map,
            reconcile_map=reconcile_map,
            primary_target=f"event:{event_id}",
            exfiltration_map=exfiltration_map
        )

        return await self._persist_and_respond(
            target_type="EVENT",
            target_id=event_id,
            timeline=timeline,
            summary=f"Reconstructed incident timeline centered on suspicious event '{event_id}' ({target_evt.source} - {target_evt.event_name}) across {len(timeline)} correlated events."
        )

    async def _fetch_all_events(self) -> List[NormalizedEvent]:
        res = await self.db.execute(select(NormalizedEvent).order_by(NormalizedEvent.event_time_reconciled.asc()))
        return list(res.scalars().all())

    async def _fetch_anomaly_map(self) -> Dict[str, AnomalyResult]:
        res = await self.db.execute(select(AnomalyResult))
        return {a.event_id: a for a in res.scalars().all()}

    async def _fetch_reconcile_map(self) -> Dict[str, ReconciliationResult]:
        res = await self.db.execute(select(ReconciliationResult))
        return {r.event_id: r for r in res.scalars().all()}

    async def _fetch_exfiltration_map(self) -> Dict[str, Any]:
        from app.models.exfiltration import ExfiltrationAssessment
        res = await self.db.execute(select(ExfiltrationAssessment))
        return {e.event_id: e for e in res.scalars().all()}

    def _build_timeline(
        self,
        events: List[NormalizedEvent],
        anomaly_map: Dict[str, AnomalyResult],
        reconcile_map: Dict[str, ReconciliationResult],
        primary_target: str,
        exfiltration_map: Optional[Dict[str, Any]] = None
    ) -> List[TimelineEvent]:
        sorted_events = sorted(events, key=lambda x: x.event_time_reconciled)
        timeline = []
        exfil_map = exfiltration_map or {}

        for evt in sorted_events:
            anom = anomaly_map.get(evt.event_id)
            rec = reconcile_map.get(evt.event_id)
            exfil = exfil_map.get(evt.event_id)

            score = anom.anomaly_score if anom else (0.85 if evt.anomaly_flag else 0.10)
            is_anom = anom.is_anomaly if anom else bool(evt.anomaly_flag)
            offset = rec.timestamp_offset_seconds if rec else 0.0

            is_exfil = exfil.weight_exfiltration_suspected if exfil else (evt.bytes_transferred > 1e9)
            exfil_conf = exfil.confidence if exfil else (0.95 if evt.bytes_transferred > 1e9 else 0.0)

            reasons = []
            if evt.user_id: reasons.append(f"matched user_id '{evt.user_id}'")
            if evt.ip_address: reasons.append(f"matched IP '{evt.ip_address}'")
            if evt.model_id: reasons.append(f"matched model_id '{evt.model_id}'")
            if is_anom: reasons.append(f"ML anomaly score {score:.2f}")
            if is_exfil: reasons.append("exfiltration suspected (large model download)")

            reason_str = f"Correlated with {primary_target} via {', '.join(reasons) if reasons else 'temporal proximity'}."

            extra_evid = evt.extra if isinstance(evt.extra, dict) else {}
            extra_evid["raw_status"] = evt.status
            extra_evid["bytes_transferred"] = evt.bytes_transferred

            tl_entry = TimelineEvent(
                event_id=evt.event_id,
                source=evt.source,
                timestamp=evt.event_time_reconciled,
                user_id=evt.user_id,
                user_name=evt.user_name,
                model_id=evt.model_id,
                event_name=evt.event_name,
                ip_address=evt.ip_address,
                evidence=extra_evid,
                anomaly_score=score,
                is_anomaly=is_anom,
                reconciled_offset_seconds=offset,
                exfiltration_suspected=is_exfil,
                exfiltration_confidence=exfil_conf,
                correlation_reason=reason_str
            )
            timeline.append(tl_entry)

        return timeline

    async def _persist_and_respond(
        self,
        target_type: str,
        target_id: str,
        timeline: List[TimelineEvent],
        summary: str
    ) -> InvestigationTimelineResponse:
        total_count = len(timeline)
        anom_count = sum(1 for t in timeline if t.is_anomaly)
        max_score = max((t.anomaly_score for t in timeline if t.anomaly_score is not None), default=0.0)

        if max_score >= 0.75 or any(t.evidence.get("bytes_transferred", 0) > 1e9 for t in timeline):
            severity = "CRITICAL"
        elif max_score >= 0.50 or anom_count > 0:
            severity = "HIGH"
        else:
            severity = "LOW"

        incident_id = f"INC-{target_type}-{target_id}-{uuid.uuid4().hex[:6]}"

        inc_obj = InvestigationIncident(
            incident_id=incident_id,
            target_type=target_type,
            target_id=target_id,
            severity=severity,
            summary=summary,
            total_events_count=total_count,
            anomalous_events_count=anom_count,
            max_anomaly_score=max_score,
            timeline=[t.model_dump(mode="json") for t in timeline]
        )
        self.db.add(inc_obj)

        for t in timeline:
            lineage = DataLineage(
                event_id=t.event_id,
                stage="SUSPICIOUS_ALERT",
                source_file="correlation_engine",
                status="COMPLETED",
                details={"incident_id": incident_id, "severity": severity}
            )
            self.db.add(lineage)

        await self.db.commit()

        return InvestigationTimelineResponse(
            incident_id=incident_id,
            target_type=target_type,
            target_id=target_id,
            severity=severity,
            summary=summary,
            total_events_count=total_count,
            anomalous_events_count=anom_count,
            max_anomaly_score=max_score,
            timeline=timeline,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
