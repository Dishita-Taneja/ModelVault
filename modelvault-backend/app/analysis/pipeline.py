import time
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.analysis.config import AnalysisConfig, default_analysis_config
from app.core.logging import logger
from app.correlation.engine import CrossSourceCorrelationEngine
from app.exfiltration.detector import ExfiltrationDetector
from app.ingestion.service import IngestionService
from app.ml.model_manager import model_manager
from app.ml.training import run_training_pipeline
from app.models import (
    AnomalyResult,
    DataLineage,
    MLModel,
    NormalizedEvent,
    SuspiciousEvent,
)
from app.reconciliation.engine import ReconciliationEngine
from app.schemas.suspicious_event import (
    PipelineExecutionReport,
    SuspiciousEventResponse,
)


class AnalysisPipeline:
    def __init__(self, db: AsyncSession, data_dir: Path | None = None, config: AnalysisConfig | None = None):
        self.db = db
        self.data_dir = data_dir
        self.config = config or default_analysis_config

    async def execute_full_pipeline(self) -> PipelineExecutionReport:
        start_time = time.time()
        logger.info("Executing Complete End-to-End ModelVault Analysis Pipeline...")

        # Step 1: Data Ingestion
        ingest_service = IngestionService(data_dir=self.data_dir)
        ingest_report = await ingest_service.run(self.db)
        logger.info(f"Step 1 (Ingestion) complete: processed {ingest_report.total_files_processed} files.")

        # Step 2: Timestamp Reconciliation
        rec_engine = ReconciliationEngine(self.db)
        rec_report = await rec_engine.reconcile_all()
        logger.info(f"Step 2 (Reconciliation) complete: reconciled {rec_report.total_events_reconciled} events.")

        # Step 3: ML Anomaly Detection Pipeline
        ml_stats = await run_training_pipeline(self.db)
        detector, pipeline, artifact = model_manager.load_model()
        logger.info(f"Step 3 (ML Anomaly Detection) complete: flagged {ml_stats['flagged_anomalous_count']} anomalous events.")

        # Step 4: Fetch normalized events & metadata
        events_res = await self.db.execute(select(NormalizedEvent).order_by(NormalizedEvent.event_time_reconciled.asc()))
        events = list(events_res.scalars().all())

        models_res = await self.db.execute(select(MLModel))
        models_dict = {m.model_id: m for m in models_res.scalars().all()}

        anom_res = await self.db.execute(select(AnomalyResult))
        anom_dict = {a.event_id: a for a in anom_res.scalars().all()}

        exfil_detector = ExfiltrationDetector(self.db)
        corr_engine = CrossSourceCorrelationEngine(self.db)

        suspicious_events_out: list[SuspiciousEventResponse] = []
        exfil_count = 0

        # Step 5: Unified Suspicious Event Synthesis
        for evt in events:
            # 5a. Exfiltration Assessment
            exfil_resp = await exfil_detector.assess_event(evt.event_id)
            if exfil_resp.weight_exfiltration_suspected:
                exfil_count += 1

            # 5b. Correlation & Investigation Timeline
            if evt.user_id:
                inv_resp = await corr_engine.correlate_by_user(evt.user_id)
            elif evt.model_id:
                inv_resp = await corr_engine.correlate_by_model(evt.model_id)
            else:
                inv_resp = await corr_engine.correlate_by_event(evt.event_id)

            # 5c. Combine Multi-Signal Risk Score & Severity
            anom_obj = anom_dict.get(evt.event_id)
            anom_score = anom_obj.anomaly_score if anom_obj else (0.85 if evt.anomaly_flag else 0.10)

            model_obj = models_dict.get(evt.model_id)
            sens_score = 1.0 if model_obj and model_obj.sensitivity_level == "CRITICAL" else (0.75 if model_obj and model_obj.sensitivity_level == "HIGH" else 0.50)

            # Calculate composite risk score (0.0 to 100.0)
            risk_score = self._calculate_composite_risk(
                anomaly_score=anom_score,
                exfil_resp=exfil_resp,
                sens_score=sens_score,
                event=evt
            )

            # Assign Severity
            severity = self._assign_severity(risk_score, exfil_resp, model_obj)

            # Detect Production Usage (InvokeEndpoint or production compute)
            prod_usage = (evt.source == "MODEL" and evt.event_name == "InvokeEndpoint") or (evt.source == "EC2" and evt.event_name == "RunInstances")

            # Formulate evidence & reasoning narrative
            combined_evidence = list(exfil_resp.evidence)
            if evt.anomaly_flag or (anom_obj and anom_obj.is_anomaly):
                combined_evidence.append(f"Unsupervised Isolation Forest isolated event with anomaly score {anom_score:.2f}.")

            summary_reason = (
                f"Suspicious activity ({severity} severity, Risk Score {risk_score:.1f}/100): "
                f"{exfil_resp.reason}"
            )

            timeline_dicts = [t.model_dump(mode="json") for t in inv_resp.timeline]

            # Upsert SuspiciousEvent in DB
            existing_se = await self.db.execute(select(SuspiciousEvent).where(SuspiciousEvent.event_id == evt.event_id))
            existing = existing_se.scalars().first()

            if not existing:
                se_obj = SuspiciousEvent(
                    event_id=evt.event_id,
                    user_id=evt.user_id,
                    model_id=evt.model_id,
                    timestamp=evt.event_time_reconciled,
                    risk_score=risk_score,
                    severity=severity,
                    anomaly_score=anom_score,
                    weight_exfiltration_suspected=exfil_resp.weight_exfiltration_suspected,
                    exfiltration_confidence=exfil_resp.confidence,
                    production_usage_detected=prod_usage,
                    reason=summary_reason,
                    evidence=combined_evidence,
                    related_events=exfil_resp.related_events,
                    investigation_timeline=timeline_dicts
                )
                self.db.add(se_obj)
            else:
                existing.risk_score = risk_score
                existing.severity = severity
                existing.anomaly_score = anom_score
                existing.weight_exfiltration_suspected = exfil_resp.weight_exfiltration_suspected
                existing.exfiltration_confidence = exfil_resp.confidence
                existing.production_usage_detected = prod_usage
                existing.reason = summary_reason
                existing.evidence = combined_evidence
                existing.related_events = exfil_resp.related_events
                existing.investigation_timeline = timeline_dicts

            # Record Data Lineage
            lineage = DataLineage(
                event_id=evt.event_id,
                stage="SUSPICIOUS_ALERT",
                source_file="analysis_pipeline",
                status="COMPLETED",
                details={"risk_score": risk_score, "severity": severity, "exfiltration_suspected": exfil_resp.weight_exfiltration_suspected}
            )
            self.db.add(lineage)

            suspicious_events_out.append(
                SuspiciousEventResponse(
                    event_id=evt.event_id,
                    user_id=evt.user_id,
                    model_id=evt.model_id,
                    timestamp=evt.event_time_reconciled,
                    risk_score=risk_score,
                    severity=severity,
                    anomaly_score=anom_score,
                    weight_exfiltration_suspected=exfil_resp.weight_exfiltration_suspected,
                    exfiltration_confidence=exfil_resp.confidence,
                    production_usage_detected=prod_usage,
                    reason=summary_reason,
                    evidence=combined_evidence,
                    related_events=exfil_resp.related_events,
                    investigation_timeline=timeline_dicts,
                    detected_at=evt.event_time_reconciled
                )
            )

        await self.db.commit()
        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        # Order by risk_score desc for top events
        suspicious_events_out.sort(key=lambda x: x.risk_score, reverse=True)
        top_events = suspicious_events_out[:3]

        report = PipelineExecutionReport(
            status="COMPLETED",
            execution_time_ms=execution_time_ms,
            total_events_processed=len(events),
            reconciled_count=rec_report.total_events_reconciled,
            anomalous_count=ml_stats["flagged_anomalous_count"],
            exfiltration_suspected_count=exfil_count,
            suspicious_events_generated=len(suspicious_events_out),
            top_suspicious_events=top_events
        )
        logger.info(f"Complete Analysis Pipeline executed in {execution_time_ms}ms. Generated {len(suspicious_events_out)} suspicious event records.")
        return report

    def _calculate_composite_risk(
        self,
        anomaly_score: float,
        exfil_resp: Any,
        sens_score: float,
        event: NormalizedEvent
    ) -> float:
        # Multi-signal risk formula
        score = (
            (anomaly_score * self.config.weight_anomaly_score) +
            (exfil_resp.confidence * self.config.weight_exfiltration_confidence) +
            (sens_score * self.config.weight_model_sensitivity)
        )

        if event.bytes_transferred >= 1e9:
            score += self.config.weight_large_data_transfer

        if exfil_resp.related_events and len(exfil_resp.related_events) >= 3:
            score += self.config.weight_cross_source_correlation

        return float(min(100.0, max(0.0, score)))

    def _assign_severity(self, risk_score: float, exfil_resp: Any, model_obj: MLModel | None) -> str:
        if risk_score >= self.config.critical_severity_threshold or (exfil_resp.weight_exfiltration_suspected and model_obj and model_obj.sensitivity_level in ["CRITICAL", "HIGH"]):
            return "CRITICAL"
        elif risk_score >= self.config.high_severity_threshold or exfil_resp.weight_exfiltration_suspected:
            return "HIGH"
        elif risk_score >= self.config.medium_severity_threshold:
            return "MEDIUM"
        else:
            return "LOW"
