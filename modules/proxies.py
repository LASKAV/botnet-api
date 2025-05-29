from enum import StrEnum
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select, func, desc

from database import SessionDep
from models.proxy import Proxy, ProxyCreate, ProxyPublic, ProxyUpdate
from .users import check_user_permissions, get_user_by_telegram_id


router = APIRouter(prefix="/proxies", tags=["Proxies"])


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ProxiesPage(BaseModel):
    total: int
    proxies: list[ProxyPublic]


@router.get("/table")
async def read_proxies_table(
    telegram_id: int,
    session: SessionDep,
    skip: int = 0,
    limit: int = 5,
    order: Order = Order.ASC
) -> ProxiesPage:
    user = await get_user_by_telegram_id(telegram_id, session)
    order_by = Proxy.id if order == Order.ASC else desc(Proxy.id)

    statement = (
        select(Proxy)
        .where(Proxy.user_id == user.id)
        .order_by(order_by)
        .offset(skip)
        .limit(limit)
    )

    proxies = await session.exec(statement)
    total = await session.exec(select(func.count()).select_from(Proxy))
    return ProxiesPage(total=total.one(), proxies=proxies)


@router.get("/")
async def read_proxies(telegram_id: int, session: SessionDep) -> list[ProxyPublic]:
    user = await get_user_by_telegram_id(telegram_id, session)
    statement = select(Proxy).where(Proxy.user_id == user.id)
    proxies = await session.exec(statement)
    return proxies


@router.get("/{proxy_id}")
async def read_proxy(
    telegram_id: int, proxy_id: int, session: SessionDep
) -> ProxyPublic:
    user = await get_user_by_telegram_id(telegram_id, session)

    statement = select(Proxy).where(Proxy.id == proxy_id, Proxy.user_id == user.id)

    result = await session.exec(statement)
    proxy = result.first()

    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found or access denied")

    return proxy


@router.post("/")
@check_user_permissions(required_subscribing=True)
async def create_proxy(
    telegram_id: int, proxy: ProxyCreate, session: SessionDep
) -> ProxyPublic:
    user = await get_user_by_telegram_id(telegram_id, session)

    if await check_proxy_exists_for_user(
        user.id, proxy.protocol, proxy.address, proxy.port, session
    ):
        raise HTTPException(
            status_code=409,
            detail="Proxy already exists for this user.",
        )

    db_proxy = Proxy(**proxy.model_dump(), user_id=user.id)
    session.add(db_proxy)
    await session.commit()
    await session.refresh(db_proxy)

    return db_proxy


@router.patch("/{proxy_id}")
async def update_proxy(
    telegram_id: int, proxy_id: int, proxy: ProxyUpdate, session: SessionDep
) -> ProxyPublic:
    user = await get_user_by_telegram_id(telegram_id, session)

    if await check_proxy_exists_for_user(
        user.id, proxy.protocol, proxy.address, proxy.port, session
    ):
        raise HTTPException(
            status_code=409,
            detail="Proxy already exists for this user.",
        )

    db_proxy = await session.get(Proxy, proxy_id)

    if not db_proxy or db_proxy.user_id != user.id:
        raise HTTPException(status_code=404, detail="Proxy not found or access denied")
    proxy_data = proxy.model_dump(exclude_unset=True)
    for key, value in proxy_data.items():
        setattr(db_proxy, key, value)

    session.add(db_proxy)
    await session.commit()
    await session.refresh(db_proxy)

    return db_proxy


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(telegram_id: int, proxy_id: int, session: SessionDep):
    user = await get_user_by_telegram_id(telegram_id, session)

    db_proxy = await session.get(Proxy, proxy_id)

    if not db_proxy or db_proxy.user_id != user.id:
        raise HTTPException(status_code=404, detail="Proxy not found or access denied")

    await session.delete(db_proxy)
    await session.commit()


async def check_proxy_exists_for_user(
    user_id: int, protocol: int, address: str, port: int, session: SessionDep
) -> bool:
    query = select(Proxy).where(
        Proxy.user_id == user_id,
        Proxy.protocol == protocol,
        Proxy.address == address,
        Proxy.port == port,
    )
    existing_proxy = await session.exec(query)
    return existing_proxy.first() is not None
