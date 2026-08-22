from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, users, models, events, alerts, ingestion, reconciliation, ml, investigations, exfiltration, analysis, suspicious_events, dashboard, anomalies
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Ingestion"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["Reconciliation"])
api_router.include_router(ml.router, prefix="/ml", tags=["ML Anomaly Detection"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])
api_router.include_router(investigations.router, prefix="/investigations", tags=["Investigations & Correlation"])
api_router.include_router(exfiltration.router, prefix="/exfiltration", tags=["Exfiltration Detection"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis Pipeline"])
api_router.include_router(suspicious_events.router, prefix="/suspicious-events", tags=["Suspicious Events"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
