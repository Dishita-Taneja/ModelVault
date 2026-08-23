from app.analysis.pipeline import AnalysisPipeline
from app.core.database import get_db
from app.core.logging import logger
from app.schemas.suspicious_event import PipelineExecutionReport
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/run", response_model=PipelineExecutionReport, status_code=200, tags=["Analysis Pipeline"])
async def run_complete_analysis_pipeline(db: AsyncSession = Depends(get_db)):
    """Triggers complete end-to-end ModelVault analysis pipeline across all ingested logs."""
    try:
        pipeline = AnalysisPipeline(db)
        return await pipeline.execute_full_pipeline()
    except Exception as e:
        logger.error(f"Analysis Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis pipeline execution error: {e!s}")
