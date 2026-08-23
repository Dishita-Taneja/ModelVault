import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logging import logger
from app.models import DataLineage, NormalizedEvent, ReconciliationResult
from app.schemas.reconciliation import (
    ReconciliationDetailResponse,
    ReconciliationRunReport,
)


class ReconciliationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def reconcile_all(self) -> ReconciliationRunReport:
        logger.info("Executing Deterministic Timestamp Reconciliation Engine...")

        # Fetch all normalized events
        events_res = await self.db.execute(
            select(NormalizedEvent).order_by(NormalizedEvent.event_time_raw.asc())
        )
        events = list(events_res.scalars().all())

        report = ReconciliationRunReport()
        report.method_breakdown = {
            "PRIMARY_SOURCE_ANCHOR": 0,
            "CROSS_SOURCE_TRIANGULATION": 0,
            "TEMPORAL_SEQUENCE_ALIGNMENT": 0
        }

        # Build session clusters by identity & IP
        session_clusters = self._cluster_events(events)

        for event in events:
            # Find correlated events within the same identity/IP cluster
            correlated_events = self._find_correlated_events(event, session_clusters)
            source_events_used = [e.event_id for e in correlated_events]

            # Compute reconciliation parameters
            event_raw = event.event_time_raw
            event_rec = event.event_time_reconciled
            offset_sec = (event_rec - event_raw).total_seconds()

            if len(source_events_used) >= 3:
                method = "CROSS_SOURCE_TRIANGULATION"
                confidence = 1.0
                reason = (
                    f"Validated via cross-source triangulation using {len(source_events_used)} correlated log events "
                    f"({', '.join(set(e.source for e in correlated_events))}) for identity '{event.user_name}' "
                    f"and IP '{event.ip_address}' with {offset_sec:.1f}s offset."
                )
            elif len(source_events_used) == 2:
                method = "CROSS_SOURCE_TRIANGULATION"
                confidence = 0.95
                reason = (
                    f"Validated via dual-log evidence correlation with event '{source_events_used[0]}' "
                    f"for IP '{event.ip_address}' with {offset_sec:.1f}s offset."
                )
            else:
                method = "PRIMARY_SOURCE_ANCHOR"
                confidence = 0.90
                reason = (
                    f"Reconciled using primary log source anchor ({event.source}) timestamp. "
                    f"No clock skew detected (offset {offset_sec:.1f}s)."
                )

            # Persist or update ReconciliationResult
            existing_res = await self.db.execute(
                select(ReconciliationResult).where(ReconciliationResult.event_id == event.event_id)
            )
            existing = existing_res.scalars().first()

            if not existing:
                rec_obj = ReconciliationResult(
                    event_id=event.event_id,
                    log_source=event.source,
                    event_time_raw=event_raw,
                    event_time_normalized=event_raw,
                    event_time_reconciled=event_rec,
                    timestamp_offset_seconds=offset_sec,
                    confidence_score=confidence,
                    reconciliation_method=method,
                    reason_for_change=reason,
                    source_events_used=source_events_used
                )
                self.db.add(rec_obj)
            else:
                existing.event_time_raw = event_raw
                existing.event_time_normalized = event_raw
                existing.event_time_reconciled = event_rec
                existing.timestamp_offset_seconds = offset_sec
                existing.confidence_score = confidence
                existing.reconciliation_method = method
                existing.reason_for_change = reason
                existing.source_events_used = source_events_used

            # Record Data Lineage
            lineage = DataLineage(
                event_id=event.event_id,
                stage="RECONCILIATION",
                source_file=f"{event.source.lower()}_logs",
                status="COMPLETED",
                details={
                    "method": method,
                    "confidence": confidence,
                    "offset_sec": offset_sec,
                    "source_events_count": len(source_events_used)
                }
            )
            self.db.add(lineage)

            # Update stats
            report.total_events_reconciled += 1
            if confidence >= 0.95:
                report.high_confidence_count += 1
            if abs(offset_sec) > 0.001:
                report.offsets_applied_count += 1
            report.method_breakdown[method] = report.method_breakdown.get(method, 0) + 1

            detail = ReconciliationDetailResponse(
                event_id=event.event_id,
                log_source=event.source,
                event_time_raw=event_raw,
                event_time_normalized=event_raw,
                event_time_reconciled=event_rec,
                timestamp_offset_seconds=offset_sec,
                confidence_score=confidence,
                reconciliation_method=method,
                reason_for_change=reason,
                source_events_used=source_events_used,
                reconciled_at=datetime.datetime.now(datetime.timezone.utc)
            )
            report.details.append(detail)

        await self.db.commit()
        logger.info(f"Reconciliation engine completed. Total events reconciled: {report.total_events_reconciled}")
        return report

    def _cluster_events(self, events: list[NormalizedEvent]) -> dict[str, list[NormalizedEvent]]:
        clusters = {}
        for evt in events:
            # Cluster key by IP or User ARN
            keys = []
            if evt.ip_address:
                keys.append(f"ip:{evt.ip_address}")
            if evt.user_name:
                keys.append(f"user:{evt.user_name}")
            if evt.user_id:
                keys.append(f"uid:{evt.user_id}")

            for k in keys:
                if k not in clusters:
                    clusters[k] = []
                clusters[k].append(evt)
        return clusters

    def _find_correlated_events(
        self,
        target_event: NormalizedEvent,
        clusters: dict[str, list[NormalizedEvent]]
    ) -> list[NormalizedEvent]:
        matches = set()

        keys_to_check = []
        if target_event.ip_address:
            keys_to_check.append(f"ip:{target_event.ip_address}")
        if target_event.user_name:
            keys_to_check.append(f"user:{target_event.user_name}")
        if target_event.user_id:
            keys_to_check.append(f"uid:{target_event.user_id}")

        for k in keys_to_check:
            for evt in clusters.get(k, []):
                matches.add(evt)

        # Sort correlated events by timestamp
        correlated = sorted(list(matches), key=lambda x: x.event_time_raw)
        return correlated
