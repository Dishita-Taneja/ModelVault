from fastapi import APIRouter

from app.api.users import router as users_router
from app.api.models import router as models_router
from app.api.access_events import router as access_events_router
from app.api.anomaly_results import router as anomaly_results_router
from app.api.summary import router as summary_router

api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(models_router)
api_router.include_router(access_events_router)
api_router.include_router(anomaly_results_router)
api_router.include_router(summary_router)

__all__ = ["api_router"]
