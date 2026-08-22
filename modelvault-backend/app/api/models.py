import uuid
from collections.abc import Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import model as crud_model
from app.crud import user as crud_user
from app.schemas.model import MLModelCreate, MLModelRead

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=list[MLModelRead], summary="List tracked ML models")
async def list_models(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[MLModelRead]:
    models = await crud_model.get_models(db, skip=skip, limit=limit)
    return models


@router.get("/{model_id}", response_model=MLModelRead, summary="Get tracked ML model by ID")
async def get_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MLModelRead:
    model = await crud_model.get_model_by_id(db, model_id=model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id '{model_id}' not found",
        )
    return model


@router.post("", response_model=MLModelRead, status_code=status.HTTP_201_CREATED, summary="Create a tracked ML model")
async def create_model(
    model_in: MLModelCreate,
    db: AsyncSession = Depends(get_db),
) -> MLModelRead:
    owner = await crud_user.get_user_by_id(db, user_id=model_in.owner_id)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner user with id '{model_in.owner_id}' not found",
        )
    return await crud_model.create_model(db, model_in=model_in)
