import uuid
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[User]:
    stmt = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    user_in: UserCreate,
) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        role=user_in.role,
        department=user_in.department,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
