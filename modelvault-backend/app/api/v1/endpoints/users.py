from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserResponse, UserCreate
from app.schemas.investigation import InvestigationTimelineResponse
from app.correlation.engine import CrossSourceCorrelationEngine
from app.crud import crud_user
from app.core.exceptions import ResourceNotFoundError

router = APIRouter()


@router.get("", response_model=List[UserResponse], tags=["Users"])
@router.get("/", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[str] = Query(None, description="Filter by user role"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all registered IAM/Analyst users with optional role filtering and pagination."""
    users = await crud_user.get_all_users(db, skip=skip, limit=limit)
    if role:
        users = [u for u in users if u.role.lower() == role.lower()]
    return users


@router.get("/{id}/investigation", response_model=InvestigationTimelineResponse, tags=["Users"])
async def get_user_investigation_shortcut(id: str, db: AsyncSession = Depends(get_db)):
    """Reconstructs cross-source security investigation timeline for a specific User ID."""
    engine = CrossSourceCorrelationEngine(db)
    return await engine.correlate_by_user(id)


@router.get("/{id}", response_model=UserResponse, tags=["Users"])
async def get_user(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves user profile for a specific user ID."""
    user = await crud_user.get_user_by_id(db, user_id=id)
    if not user:
        raise ResourceNotFoundError(resource="User", identifier=id)
    return user


@router.post("", response_model=UserResponse, status_code=201, tags=["Users"])
@router.post("/", response_model=UserResponse, status_code=201, tags=["Users"])
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new user identity record in ModelVault."""
    return await crud_user.create_user(db, user_in=user_in)
