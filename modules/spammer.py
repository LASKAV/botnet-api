from database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from models.tasks.spammer_task import SpammerTask, SpammerTaskCreate
from pydantic import ValidationError
from models.message_templates import MessageTemplates
from models.account import Account
from models.limit import Limit
from random import sample


router = APIRouter(prefix="/spammer", tags=["Spammer Tasks"])


@router.get("/{account_id}")
async def read_spammer(account_id: int, session: SessionDep):
    tasks = select(SpammerTask).where(SpammerTask.account_id == account_id)
    result = await session.exec(tasks)
    answer = result.all()
    if not answer:
        raise HTTPException(status_code=404, detail="Spammer tasks not found")

    return answer


@router.post("")
async def create_spammer(data: SpammerTaskCreate, session: SessionDep):
    try:
        if data.day_limit is not None and data.time_limit is not None:
            for account_id in data.account_id:
                limit_stmt = select(Limit).where(
                    Limit.account_id == account_id, Limit.action_type == "mailing"
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

        templates_stmt = select(MessageTemplates).where(
            MessageTemplates.id.in_(data.message_template_id)
        )
        templates = (await session.exec(templates_stmt)).all()

        # Create spam tasks for each account
        for account_id in data.account_id:
            stmt = select(Account).where(Account.id == account_id)
            result = await session.exec(stmt)
            account = result.one_or_none()
            account.mail = True
            session.add(account)

            # Random selection of templates
            random_templates = sample(templates, len(templates))
            for template in random_templates:
                spam_task = SpammerTask(
                    account_id=account_id,
                    message_template_id=template.id,
                )
                session.add(spam_task)

        await session.commit()

    except ValidationError as e:
        print(f"Create spammer: {e}")
