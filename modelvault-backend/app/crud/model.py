import uuid
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import MLModel
from app.schemas.model import MLModelCreate


async def get_models(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[MLModel]:
    stmt = select(MLModel).offset(skip).limit(limit).order_by(MLModel.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_model_by_id(
    db: AsyncSession,
    model_id: uuid.UUID,
) -> MLModel | None:
    stmt = select(MLModel).where(MLModel.id == model_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_model(
    db: AsyncSession,
    model_in: MLModelCreate,
) -> MLModel:
    model = MLModel(
        name=model_in.name,
        description=model_in.description,
        owner_id=model_in.owner_id,
        sensitivity_level=model_in.sensitivity_level,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return model
