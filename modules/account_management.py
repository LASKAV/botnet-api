from fastapi import APIRouter, HTTPException
from sqlmodel import select
from database import SessionDep
from models.account import Account
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/accounts", tags=["Account Management"])


class AccountFlagsUpdate(BaseModel):
    account_ids: list[int]
    warm_up: Optional[bool] = None
    join: Optional[bool] = None
    mail: Optional[bool] = None
    invite: Optional[bool] = None


@router.post("/update-flags")
async def update_account_flags(data: AccountFlagsUpdate, session: SessionDep):
    accounts = await session.exec(
        select(Account).where(Account.id.in_(data.account_ids))
    )

    accounts_list = list(accounts)
    if not accounts_list:
        raise HTTPException(
            status_code=404, detail="No accounts found with the specified IDs"
        )

    for account in accounts_list:
        # Only update fields that are not None
        if data.warm_up is not None:
            account.warm_up = data.warm_up
        if data.join is not None:
            account.join = data.join
        if data.mail is not None:
            account.mail = data.mail
        if data.invite is not None:
            account.invite = data.invite

    await session.commit()


@router.post("/waiting-code/{account_id}")
async def update_waiting_code(account_id: int, session: SessionDep):
    account = await session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.waiting_code = True
    await session.commit()
