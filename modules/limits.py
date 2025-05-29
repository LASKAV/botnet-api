from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from database import SessionDep
from models.limit import Limit, LimitCreate, LimitPublic, LimitUpdate


router = APIRouter(prefix="/limits", tags=["Limits"])


@router.get("/")
async def read_limits(session: SessionDep) -> list[LimitPublic]:
    statement = select(Limit)
    limits = await session.exec(statement)
    return limits.all()


@router.get("/{limit_id}")
async def read_limit(limit_id: int, session: SessionDep) -> LimitPublic:
    limit = await session.get(Limit, limit_id)
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    return limit


@router.post("/")
async def create_limit(limit: LimitCreate, session: SessionDep) -> LimitPublic:
    db_limit = Limit.model_validate(limit)
    session.add(db_limit)
    await session.commit()
    await session.refresh(db_limit)
    return db_limit


@router.patch("/{limit_id}")
async def update_limit(limit_id: int, limit: LimitUpdate, session: SessionDep) -> LimitPublic:
    db_limit = await session.get(Limit, limit_id)
    if not db_limit:
        raise HTTPException(status_code=404, detail="Limit not found")

    limit_data = limit.model_dump(exclude_unset=True)
    for key, value in limit_data.items():
        setattr(db_limit, key, value)

    session.add(db_limit)
    await session.commit()
    await session.refresh(db_limit)
    return db_limit


@router.delete("/{limit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_limit(limit_id: int, session: SessionDep):
    limit = await session.get(Limit, limit_id)
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")

    await session.delete(limit)
    await session.commit()


@router.get("/{account_id}/{action_type}", response_model=LimitPublic)
async def read_limit_by_account_action(account_id: int, action_type: str, session: SessionDep) -> LimitPublic:
    """
    Получает лимит по account_id и action_type, передаваемым в URL.
    """
    statement = select(Limit).where(Limit.account_id == account_id, Limit.action_type == action_type)
    result = await session.exec(statement)
    limit = result.one_or_none()
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    return limit


@router.patch("/{account_id}/{action_type}", response_model=LimitPublic)
async def update_limit_by_account_action(
        account_id: int,
        action_type: str,
        limit_update: LimitUpdate,
        session: SessionDep
) -> LimitPublic:
    """
    Обновляет лимит по account_id и action_type, передаваемым в URL.
    """
    statement = select(Limit).where(Limit.account_id == account_id, Limit.action_type == action_type)
    result = await session.exec(statement)
    db_limit = result.one_or_none()
    if not db_limit:
        raise HTTPException(status_code=404, detail="Limit not found")

    update_data = limit_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_limit, key, value)

    session.add(db_limit)
    await session.commit()
    await session.refresh(db_limit)
    return db_limit
