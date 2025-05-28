from enum import StrEnum

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import col, desc, func, insert, literal, select
from typing import List

from database import SessionDep
from models.account import (
    Account,
    AccountCreate,
    AccountEmojiResponse,
    AccountEmojiUpdate,
    AccountPublic,
    AccountUpdate,
)
from models.limit import Limit
from models.tasks.contact_task import ContactTask

router = APIRouter(prefix="/accounts", tags=["Accounts"])


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class AccountsPage(BaseModel):
    total: int
    accounts: list[AccountPublic]


class WarmupCreate(BaseModel):
    account_ids: List[int]
    emoji: List[str]
    time_limit: int


@router.get("/{account_id}/emoji", response_model=AccountEmojiResponse)
async def get_emoji(account_id: int, session: SessionDep):
    account = await session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountEmojiResponse(id=account.id, emoji=account.emoji)


@router.patch("/{account_id}/emoji", response_model=AccountEmojiResponse)
async def update_emoji(
    account_id: int, update_data: AccountEmojiUpdate, session: SessionDep
):
    account = await session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.emoji = update_data.emoji
    session.add(account)
    await session.commit()
    await session.refresh(account)

    return AccountEmojiResponse(id=account.id, emoji=account.emoji)


@router.get("/")
async def read_accounts(
    session: SessionDep, skip: int = 0, limit: int = 5, order: Order = Order.ASC
) -> AccountsPage:
    order_by = Account.id if order == Order.ASC else desc(Account.id)
    statement = select(Account).order_by(order_by).offset(skip).limit(limit)
    accounts = await session.exec(statement)
    total = await session.exec(select(func.count()).select_from(Account))
    return AccountsPage(total=total.one(), accounts=accounts)


@router.get("/{type}/{status}")
async def read_accounts_status(
    type: str,
    status: bool,
    session: SessionDep,
    skip: int = 0,
    limit: int = 5,
    order: Order = Order.ASC,
) -> AccountsPage:
    order_by = Account.id if order == Order.ASC else desc(Account.id)

    status_filters = {
        "warm_up": Account.warm_up == status,
        "join": Account.join == status,
        "mail": Account.mail == status,
        "invite": Account.invite == status,
    }

    statement = (
        select(Account)
        .where(status_filters[type])
        .order_by(order_by)
        .offset(skip)
        .limit(limit)
    )

    accounts = await session.exec(statement)
    total = await session.exec(
        select(func.count(func.distinct(Account.id)))
        .select_from(Account)
        .where(status_filters[type])
    )

    return AccountsPage(total=total.one(), accounts=accounts)


@router.get("/{account_id}")
async def read_account(account_id: int, session: SessionDep) -> AccountPublic:
    account = await session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/")
async def create_account(account: AccountCreate, session: SessionDep) -> AccountPublic:
    db_account = Account.model_validate(account)

    session.add(db_account)
    await session.flush()

    new_account_id = db_account.id

    limits = [
        Limit(account_id=new_account_id, action_type="join_group", day_limit=30),
        Limit(account_id=new_account_id, action_type="invitation", day_limit=300),
        Limit(
            account_id=new_account_id,
            action_type="mailing",
            day_limit=10,
            time_limit=150,
        ),
        Limit(account_id=new_account_id, action_type="warmup"),
    ]

    session.add_all(limits)

    insert_tasks_for_existing = insert(ContactTask).from_select(
        ["account_id", "contact_id"],
        select(
            col(Account.id).label("account_id"),
            literal(new_account_id).label("contact_id"),
        ).where(Account.id != new_account_id),
    )

    await session.exec(insert_tasks_for_existing)

    insert_tasks_for_new = insert(ContactTask).from_select(
        ["account_id", "contact_id"],
        select(
            literal(new_account_id).label("account_id"),
            col(Account.id).label("contact_id"),
        ).where(Account.id != new_account_id),
    )

    await session.exec(insert_tasks_for_new)

    await session.commit()
    await session.refresh(db_account)

    return db_account


@router.patch("/{account_id}")
async def update_account(
    account_id: int, account: AccountUpdate, session: SessionDep
) -> AccountPublic:
    db_account = await session.get(Account, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    account_data = account.model_dump(exclude_unset=True)
    for key, value in account_data.items():
        setattr(db_account, key, value)

    session.add(db_account)
    await session.commit()
    await session.refresh(db_account)

    return db_account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, session: SessionDep):
    account = await session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await session.delete(account)
    await session.commit()


@router.patch("/{account_id}/warmup")
async def update_warmup(account_id: int, data: WarmupCreate, session: SessionDep):
    try:
        limit_stmt = select(Limit).where(
            Limit.account_id == account_id, Limit.action_type == "warmup"
        )
        limit_record = (await session.exec(limit_stmt)).first()

        limit_record.time_limit = data.time_limit
        session.add(limit_record)

        account_stmt = select(Account).where(Account.id == account_id)
        account = (await session.exec(account_stmt)).first()

        account.emoji = data.emoji
        session.add(account)

        await session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
