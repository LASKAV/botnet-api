from database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from models.tasks.invitation_task import InvitationTask, InvitationTaskCreate
from pydantic import ValidationError
from models.limit import Limit
from models.account import Account


router = APIRouter(prefix="/invitations", tags=["Invitation Tasks"])


@router.get("/{account_id}")
async def read_invitation(account_id: int, session: SessionDep):
    tasks = select(InvitationTask).where(InvitationTask.account_id == account_id)
    result = await session.exec(tasks)
    answer = result.all()
    if not answer:
        raise HTTPException(status_code=404, detail="Invitation tasks not found")

    return answer


@router.post("")
async def create_invitation(data: InvitationTaskCreate, session: SessionDep):
    try:
        if data.day_limit is not None and data.time_limit is not None:
            for account_id in data.account_id:
                limit_stmt = select(Limit).where(
                    Limit.account_id == account_id, Limit.action_type == "invitation"
                )
                limit_result = await session.exec(limit_stmt)
                limit_record = limit_result.one_or_none()

                if limit_record is not None:
                    old_day_limit = limit_record.day_limit
                    limit_record.day_limit = data.day_limit
                    limit_record.fact_limit = (
                        limit_record.fact_limit - old_day_limit + data.day_limit
                    )
                    limit_record.time_limit = data.time_limit
                    session.add(limit_record)

        # Create invitation tasks for each account
        for account_id in data.account_id:
            stmt = select(Account).where(Account.id == account_id)
            result = await session.exec(stmt)
            account = result.one_or_none()
            account.invite = True
            session.add(account)

            invitation_task = InvitationTask(
                account_id=account_id,
                target_link=data.target_link,
            )
            session.add(invitation_task)

        await session.commit()

    except ValidationError as e:
        print(f"Create spammer: {e}")
