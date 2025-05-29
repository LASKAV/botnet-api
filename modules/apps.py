from enum import StrEnum
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select, func, desc

from database import SessionDep
from models.app import App, AppCreate, AppPublic, AppUpdate
from .users import check_user_permissions, get_user_by_telegram_id


router = APIRouter(prefix="/apps", tags=["Apps"])


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class AppsPage(BaseModel):
    total: int
    apps: list[AppPublic]


@router.get("/table")
async def read_apps_table(
    telegram_id: int,
    session: SessionDep,
    skip: int = 0,
    limit: int = 5,
    order: Order = Order.ASC,
) -> AppsPage:
    user = await get_user_by_telegram_id(telegram_id, session)

    order_by = App.id if order == Order.ASC else desc(App.id)

    statement = (
        select(App)
        .where(App.user_id == user.id)
        .order_by(order_by)
        .offset(skip)
        .limit(limit)
    )

    apps = await session.exec(statement)
    total = await session.exec(select(func.count()).select_from(App))
    return AppsPage(total=total.one(), apps=apps)


@router.get("/")
async def read_apps(telegram_id: int, session: SessionDep) -> list[AppPublic]:
    user = await get_user_by_telegram_id(telegram_id, session)
    statement = select(App).where(App.user_id == user.id)
    apps = await session.exec(statement)
    return apps


@router.get("/{app_id}")
async def read_app(telegram_id: int, app_id: int, session: SessionDep) -> AppPublic:
    user = await get_user_by_telegram_id(telegram_id, session)

    statement = select(App).where(App.id == app_id, App.user_id == user.id)
    result = await session.exec(statement)
    app = result.first()

    if not app:
        raise HTTPException(status_code=404, detail="App not found or access denied")

    return app


@router.post("/")
@check_user_permissions(required_subscribing=True)
async def create_app(
    telegram_id: int, app: AppCreate, session: SessionDep
) -> AppPublic:
    user = await get_user_by_telegram_id(telegram_id, session)

    if await check_app_exists_for_user(user.id, app.api_id, app.api_hash, session):
        raise HTTPException(
            status_code=409,
            detail="App already exists for this user.",
        )

    db_app = App(**app.model_dump(), user_id=user.id)
    session.add(db_app)
    await session.commit()
    await session.refresh(db_app)

    return db_app


@router.patch("/{app_id}")
async def update_app(
    telegram_id: int,
    app_id: int,
    app: AppUpdate,
    session: SessionDep,
) -> AppPublic:
    user = await get_user_by_telegram_id(telegram_id, session)

    if await check_app_exists_for_user(user.id, app.api_id, app.api_hash, session):
        raise HTTPException(
            status_code=409,
            detail="App already exists for this user.",
        )

    db_app = await session.get(App, app_id)

    if not db_app or db_app.user_id != user.id:
        raise HTTPException(status_code=404, detail="App not found or access denied")

    app_data = app.model_dump(exclude_unset=True)
    for key, value in app_data.items():
        setattr(db_app, key, value)

    session.add(db_app)
    await session.commit()
    await session.refresh(db_app)

    return db_app


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(telegram_id: int, app_id: int, session: SessionDep):
    user = await get_user_by_telegram_id(telegram_id, session)

    db_app = await session.get(App, app_id)

    if not db_app or db_app.user_id != user.id:
        raise HTTPException(status_code=404, detail="App not found or access denied")

    await session.delete(db_app)
    await session.commit()


async def check_app_exists_for_user(
    user_id: int, api_id: int, api_hash: str, session: SessionDep
) -> bool:
    query = select(App).where(
        App.user_id == user_id,
        App.api_id == api_id,
        App.api_hash == api_hash,
    )
    existing_app = await session.exec(query)
    return existing_app.first() is not None
