from enum import StrEnum
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select, func, desc

from database import SessionDep
from models.app import App, AppCreate, AppPublic, AppUpdate

router = APIRouter(prefix="/apps", tags=["Apps"])


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class AppsPage(BaseModel):
    total: int
    apps: list[AppPublic]


@router.get("/table")
async def read_apps_table(
    session: SessionDep, skip: int = 0, limit: int = 5, order: Order = Order.ASC
) -> AppsPage:
    order_by = App.id if order == Order.ASC else desc(App.id)
    statement = select(App).order_by(order_by).offset(skip).limit(limit)
    apps = await session.exec(statement)
    total = await session.exec(select(func.count()).select_from(App))
    return AppsPage(total=total.one(), apps=apps)


@router.get("/")
async def read_apps(session: SessionDep) -> list[AppPublic]:
    statement = select(App)
    apps = await session.exec(statement)
    return apps


@router.get("/{app_id}")
async def read_app(app_id: int, session: SessionDep) -> AppPublic:
    app = await session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return app


@router.post("/")
async def create_app(app: AppCreate, session: SessionDep) -> AppPublic:
    db_app = App.model_validate(app)
    session.add(db_app)
    await session.commit()
    await session.refresh(db_app)

    return db_app


@router.patch("/{app_id}")
async def update_app(app_id: int, app: AppUpdate, session: SessionDep) -> AppPublic:
    db_app = await session.get(App, app_id)
    if not db_app:
        raise HTTPException(status_code=404, detail="App not found")

    app_data = app.model_dump(exclude_unset=True)
    for key, value in app_data.items():
        setattr(db_app, key, value)

    session.add(db_app)
    await session.commit()
    await session.refresh(db_app)

    return db_app


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(app_id: int, session: SessionDep):
    app = await session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    await session.delete(app)
    await session.commit()
