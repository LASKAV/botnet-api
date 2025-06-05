from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from database import SessionDep
from models.user import User, UserCreate, UserPublic

from functools import wraps
from typing import Callable


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def read_users(session: SessionDep) -> list[UserPublic]:
    statement = select(User)
    users = await session.exec(statement)
    return users.all()


@router.get("/{user_id}")
async def read_user(user_id: int, session: SessionDep) -> UserPublic:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/")
async def create_user(user: UserCreate, session: SessionDep) -> UserPublic:
    existing_user = await session.exec(
        select(User).where(User.telegram_id == user.telegram_id)
    )
    user_obj = existing_user.first()
    if user_obj:
        return user_obj

    user = User.model_validate(user)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: SessionDep):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()


def check_user_permissions(
    required_admin: bool = False, required_subscribing: bool = False
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(telegram_id: int, *args, session: SessionDep, **kwargs):
            user = (
                await session.exec(select(User).where(User.telegram_id == telegram_id))
            ).first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if required_admin and not user.admin:
                raise HTTPException(status_code=403, detail="Admin rights required")

            if required_subscribing and not user.subscribing and not user.admin:
                raise HTTPException(
                    status_code=403, detail="Active subscription required"
                )

            return await func(telegram_id=telegram_id, *args, session=session, **kwargs)

        return wrapper

    return decorator


async def get_user_by_telegram_id(telegram_id: int, session: SessionDep) -> User:
    user = (
        await session.exec(select(User).where(User.telegram_id == telegram_id))
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
