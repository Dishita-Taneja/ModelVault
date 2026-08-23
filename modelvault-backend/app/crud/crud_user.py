import uuid

from app.models.user import User
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    # Check if user with same email exists
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        return existing

    user_id = user_in.user_id
    if not user_id:
        clean_name = "".join(c for c in user_in.username.lower() if c.isalnum()) or "user"
        user_id = f"usr-{clean_name}"

    # Ensure user_id uniqueness
    existing_id = await get_user_by_id(db, user_id)
    if existing_id:
        user_id = f"{user_id}-{uuid.uuid4().hex[:4]}"

    db_user = User(
        user_id=user_id,
        username=user_in.username,
        email=user_in.email,
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
