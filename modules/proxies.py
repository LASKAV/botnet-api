from enum import StrEnum
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select, func , desc

from database import SessionDep
from models.proxy import Proxy, ProxyCreate, ProxyPublic, ProxyUpdate


router = APIRouter(prefix="/proxies", tags=["Proxies"])


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ProxiesPage(BaseModel):
    total: int
    proxies: list[ProxyPublic]


@router.get("/table")
async def read_proxies_table(
    session: SessionDep, skip: int = 0, limit: int = 5, order: Order = Order.ASC
) -> ProxiesPage:
    order_by = Proxy.id if order == Order.ASC else desc(Proxy.id)
    statement = select(Proxy).order_by(order_by).offset(skip).limit(limit)
    proxies = await session.exec(statement)
    total = await session.exec(select(func.count()).select_from(Proxy))
    return ProxiesPage(total=total.one(), proxies=proxies)


@router.get("/")
async def read_proxies(session: SessionDep) -> list[ProxyPublic]:
    statement = select(Proxy)
    proxies = await session.exec(statement)
    return proxies


@router.get("/{proxy_id}")
async def read_proxy(proxy_id: int, session: SessionDep) -> ProxyPublic:
    proxy = await session.get(Proxy, proxy_id)
    return proxy


@router.post("/")
async def create_proxy(proxy: ProxyCreate, session: SessionDep) -> ProxyPublic:
    db_proxy = Proxy.model_validate(proxy)
    session.add(db_proxy)
    await session.commit()
    await session.refresh(db_proxy)

    return db_proxy


@router.patch("/{proxy_id}")
async def update_proxy(
    proxy_id: int, proxy: ProxyUpdate, session: SessionDep
) -> ProxyPublic:
    db_proxy = await session.get(Proxy, proxy_id)
    if not db_proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    proxy_data = proxy.model_dump(exclude_unset=True)
    for key, value in proxy_data.items():
        setattr(db_proxy, key, value)

    session.add(db_proxy)
    await session.commit()
    await session.refresh(db_proxy)

    return db_proxy


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(proxy_id: int, session: SessionDep):
    proxy = await session.get(Proxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    await session.delete(proxy)
    await session.commit()
