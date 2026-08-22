"""ModelVault Data Ingestion Pipeline Package"""
from app.ingestion.service import IngestionService, run_ingestion_pipeline

__all__ = ["IngestionService", "run_ingestion_pipeline"]
