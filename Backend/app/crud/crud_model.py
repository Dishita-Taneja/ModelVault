
from app.models.model import MLModel
from app.schemas.model import MLModelCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def get_model_by_id(db: AsyncSession, model_id: str) -> MLModel | None:
    result = await db.execute(select(MLModel).where(MLModel.model_id == model_id))
    return result.scalars().first()


async def get_all_models(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[MLModel]:
    result = await db.execute(select(MLModel).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_model(db: AsyncSession, model_in: MLModelCreate) -> MLModel:
    db_model = MLModel(
        model_id=model_in.model_id,
        name=model_in.name,
        description=model_in.description,
        framework=model_in.framework,
        s3_uri=model_in.s3_uri,
        sensitivity_level=model_in.sensitivity_level,
        owner_id=model_in.owner_id,
        owner_email=model_in.owner_email
    )
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return db_model
