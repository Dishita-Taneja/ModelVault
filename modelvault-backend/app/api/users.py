import uuid
from collections.abc import Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import user as crud_user
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserRead], summary="List all users")
async def list_users(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[UserRead]:
    users = await crud_user.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserRead, summary="Get user by ID")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await crud_user.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create a user")
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    existing_username = await crud_user.get_user_by_username(db, username=user_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' already registered",
        )
    existing_email = await crud_user.get_user_by_email(db, email=user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_in.email}' already registered",
        )
    return await crud_user.create_user(db, user_in=user_in)
