from fastapi import APIRouter, HTTPException
from sqlmodel import select

from database import SessionDep
from models.user import User, UserCreate, UserPublic


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
    user = User.model_validate(user)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
