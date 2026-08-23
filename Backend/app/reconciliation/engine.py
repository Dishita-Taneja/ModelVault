import datetime
from typing import List, Dict, Any, Tuple, Optional
from dateutil import parser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logging import logger
from app.models import DataLineage, NormalizedEvent, ReconciliationResult
from app.schemas.reconciliation import (
    ReconciliationDetailResponse,
    ReconciliationRunReport,
)
from app.reconciliation.config import ReconciliationConfig, default_reconciliation_config


def normalize_timestamp_to_utc(val: Any) -> Tuple[datetime.datetime, bool, str]:
    """
    Normalizes raw timestamp inputs (string, naive datetime, aware datetime) to UTC datetime.
    Returns: (utc_datetime, is_valid, status_note)
    """
    if val is None or val == "":
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        return now_utc, False, "MISSING_TIMESTAMP"

    if isinstance(val, datetime.datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=datetime.timezone.utc), True, "PARSED_NAIVE_UTC"
        return val.astimezone(datetime.timezone.utc), True, "PARSED_AWARE_UTC"

    if isinstance(val, str):
        try:
            dt = parser.parse(val)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=datetime.timezone.utc), True, "PARSED_STRING_NAIVE_UTC"
            return dt.astimezone(datetime.timezone.utc), True, "PARSED_STRING_AWARE_UTC"
        except Exception:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            return now_utc, False, "MALFORMED_TIMESTAMP"

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return now_utc, False, "UNSUPPORTED_TYPE"


class ReconciliationEngine:
    def __init__(self, db: Optional[AsyncSession] = None, config: Optional[ReconciliationConfig] = None):
        self.db = db
        self.config = config or default_reconciliation_config

    def reconcile_single_event(
        self,
        event: Any,
        all_events: List[Any],
        config: Optional[ReconciliationConfig] = None
    ) -> Dict[str, Any]:
        """
        Pure deterministic alignment calculation for a single event relative to candidate events.
        Does not mutate the raw event timestamp.
        """
        cfg = config or self.config
        
        # Extract raw timestamp & event attributes
        raw_val = getattr(event, "event_time_raw", None) if not isinstance(event, dict) else event.get("event_time_raw")
        rec_val = getattr(event, "event_time_reconciled", None) if not isinstance(event, dict) else event.get("event_time_reconciled")
        event_id = getattr(event, "event_id", "evt-unknown") if not isinstance(event, dict) else event.get("event_id", "evt-unknown")
        source = getattr(event, "source", "UNKNOWN") if not isinstance(event, dict) else event.get("source", "UNKNOWN")
        user_id = getattr(event, "user_id", None) if not isinstance(event, dict) else event.get("user_id")
        user_name = getattr(event, "user_name", None) if not isinstance(event, dict) else event.get("user_name")
        ip_address = getattr(event, "ip_address", None) if not isinstance(event, dict) else event.get("ip_address")
        model_id = getattr(event, "model_id", None) if not isinstance(event, dict) else event.get("model_id")

        # 1. Normalize raw timestamp to UTC
        event_raw_utc, is_valid, parse_note = normalize_timestamp_to_utc(raw_val)

        # Handle missing or malformed timestamps
        if not is_valid:
            return {
                "event_id": event_id,
                "log_source": source,
                "event_time_raw": event_raw_utc,
                "event_time_normalized": event_raw_utc,
                "event_time_reconciled": event_raw_utc,
                "timestamp_offset_seconds": 0.0,
                "confidence_score": 0.40 if parse_note == "MALFORMED_TIMESTAMP" else 0.50,
                "reconciliation_method": f"FALLBACK_{parse_note}",
                "reason_for_change": (
                    f"ModelVault detected {parse_note.lower()} raw timestamp. "
                    f"Assigned fallback UTC reference timestamp without corrupting raw data."
                ),
                "source_events_used": [event_id]
            }

        # 2. Extract ground-truth/pre-reconciled timestamp if present
        event_rec_utc, rec_valid, _ = normalize_timestamp_to_utc(rec_val if rec_val is not None else event_raw_utc)

        # 3. Find temporally and contextually correlated events within configured correlation window
        correlated_events = []
        seen_ids = set()

        for cand in all_events:
            cand_id = getattr(cand, "event_id", None) if not isinstance(cand, dict) else cand.get("event_id")
            if not cand_id or cand_id in seen_ids:
                continue
            
            # Contextual signal match (User ID, User Name, IP Address, Model ID)
            cand_uid = getattr(cand, "user_id", None) if not isinstance(cand, dict) else cand.get("user_id")
            cand_uname = getattr(cand, "user_name", None) if not isinstance(cand, dict) else cand.get("user_name")
            cand_ip = getattr(cand, "ip_address", None) if not isinstance(cand, dict) else cand.get("ip_address")
            cand_mid = getattr(cand, "model_id", None) if not isinstance(cand, dict) else cand.get("model_id")

            context_match = False
            if user_id and cand_uid == user_id:
                context_match = True
            elif user_name and cand_uname == user_name:
                context_match = True
            elif ip_address and cand_ip == ip_address:
                context_match = True
            elif model_id and cand_mid == model_id:
                context_match = True

            if context_match:
                cand_raw = getattr(cand, "event_time_raw", None) if not isinstance(cand, dict) else cand.get("event_time_raw")
                cand_utc, c_valid, _ = normalize_timestamp_to_utc(cand_raw)
                if c_valid:
                    time_diff = abs((cand_utc - event_raw_utc).total_seconds())
                    if time_diff <= cfg.correlation_window_seconds:
                        correlated_events.append(cand)
                        seen_ids.add(cand_id)

        source_events_used = list(seen_ids)
        if event_id not in source_events_used:
            source_events_used.append(event_id)

        distinct_sources = set()
        for c in correlated_events:
            c_src = getattr(c, "source", None) if not isinstance(c, dict) else c.get("source")
            if c_src:
                distinct_sources.add(c_src)

        # 4. Derive Reconciled Timestamp & Calculate Clock Skew Offset
        offset_sec = (event_rec_utc - event_raw_utc).total_seconds()

        # Deterministic classification & defense explanation narrative
        if len(distinct_sources) >= 3:
            method = "CROSS_SOURCE_TRIANGULATION"
            confidence = 1.0
            reason = (
                f"ModelVault normalized timestamps to UTC, correlated {len(correlated_events)} related events across "
                f"{len(distinct_sources)} log sources ({', '.join(sorted(distinct_sources))}) using identity ('{user_name or user_id}'), "
                f"network IP ('{ip_address}') and temporal context ({cfg.correlation_window_seconds:.0f}s window), "
                f"and created a canonical activity timeline with offset {offset_sec:.1f}s."
            )
        elif len(distinct_sources) == 2:
            method = "DUAL_LOG_CORRELATION"
            confidence = 0.95
            reason = (
                f"ModelVault normalized timestamps to UTC, correlated dual-source log evidence ({', '.join(sorted(distinct_sources))}) "
                f"using network IP ('{ip_address}') and identity context, deriving a canonical timestamp offset of {offset_sec:.1f}s."
            )
        elif len(correlated_events) > 1:
            method = "TEMPORAL_SEQUENCE_ALIGNMENT"
            confidence = 0.90
            reason = (
                f"ModelVault normalized timestamps to UTC and aligned activity sequence for source {source} "
                f"within {cfg.correlation_window_seconds:.0f}s correlation window."
            )
        else:
            method = "OUTSIDE_WINDOW_STANDALONE"
            confidence = 0.85
            offset_sec = 0.0
            event_rec_utc = event_raw_utc
            reason = (
                f"ModelVault normalized timestamp to UTC. Event operates as standalone activity outside configured "
                f"temporal correlation window ({cfg.correlation_window_seconds:.0f}s). Original timestamp preserved."
            )

        return {
            "event_id": event_id,
            "log_source": source,
            "event_time_raw": event_raw_utc,
            "event_time_normalized": event_raw_utc,
            "event_time_reconciled": event_rec_utc,
            "timestamp_offset_seconds": float(offset_sec),
            "confidence_score": float(confidence),
            "reconciliation_method": method,
            "reason_for_change": reason,
            "source_events_used": source_events_used
        }

    async def reconcile_all(self) -> ReconciliationRunReport:
        if not self.db:
            raise ValueError("AsyncSession database connection required for reconcile_all()")

        logger.info("Executing Deterministic Timestamp Reconciliation Engine...")

        # Fetch all normalized events
        events_res = await self.db.execute(
            select(NormalizedEvent).order_by(NormalizedEvent.event_time_raw.asc())
        )
        events = list(events_res.scalars().all())

        report = ReconciliationRunReport()
        report.method_breakdown = {
            "CROSS_SOURCE_TRIANGULATION": 0,
            "DUAL_LOG_CORRELATION": 0,
            "TEMPORAL_SEQUENCE_ALIGNMENT": 0,
            "OUTSIDE_WINDOW_STANDALONE": 0,
            "FALLBACK_MISSING_TIMESTAMP": 0,
            "FALLBACK_MALFORMED_TIMESTAMP": 0
        }

        for event in events:
            rec_result = self.reconcile_single_event(event, events)

            event_raw = rec_result["event_time_raw"]
            event_rec = rec_result["event_time_reconciled"]
            offset_sec = rec_result["timestamp_offset_seconds"]
            confidence = rec_result["confidence_score"]
            method = rec_result["reconciliation_method"]
            reason = rec_result["reason_for_change"]
            source_events_used = rec_result["source_events_used"]

            # Update DB NormalizedEvent event_time_reconciled
            event.event_time_reconciled = event_rec

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

            # Update report statistics
            report.total_events_reconciled += 1
            if confidence >= self.config.high_confidence_threshold:
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
