from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from database import SessionDep
from models.account import Account
from models.tasks.contact_task import ContactTask
from models.group_link import GroupLink
from models.tasks.join_group_task import JoinGroupTask
from models.message_templates import MessageTemplates
from models.tasks.spammer_task import SpammerTask
from models.tasks.invitation_task import InvitationTask
from modules.tasks.contact import patch_contact
from modules.tasks.group import patch_join_group
from modules.tasks.invitation import patch_invitation

from .model.patch_ops import (
    PatchContact,
    PatchJoinGroup,
    PatchWaitingCode,
    PatchWarmUp,
    PatchInvite,
    PatchJoin,
    PatchMail,
    PatchSpam,
    PatchInvitation,
)
from .spam import patch_spam

router = APIRouter(prefix="/accounts/{account_id}/tasks", tags=["Tasks"])


class TasksResponse(BaseModel):
    waiting_code: bool
    warm_up: bool
    join: bool
    mail: bool
    invite: bool
    contact: list[str]
    join_group: list[str]
    spam: list[str]
    invitation: str | None


@router.get("/")
async def read_tasks(account_id: int, session: SessionDep) -> TasksResponse:
    simple_tasks = (
        await session.exec(
            select(
                Account.waiting_code,
                Account.warm_up,
                Account.join,
                Account.mail,
                Account.invite,
            ).where(Account.id == account_id)
        )
    ).first()
    if not simple_tasks:
        raise HTTPException(status_code=404, detail="Account not found")

    contact_stmt = (
        select(Account.phone)
        .join(ContactTask, ContactTask.contact_id == Account.id)
        .where(ContactTask.account_id == account_id)
    )
    contact_tasks = (await session.exec(contact_stmt)).all()

    join_group_stmt = (
        select(GroupLink.link)
        .join(JoinGroupTask)
        .where(JoinGroupTask.account_id == account_id)
    )
    join_group_tasks = (await session.exec(join_group_stmt)).all()

    spam_stmt = (
        select(MessageTemplates.message)
        .join(SpammerTask)
        .where(SpammerTask.account_id == account_id)
    )
    spam_tasks = (await session.exec(spam_stmt)).all()

    invitation_stmt = select(InvitationTask.target_link).where(
        InvitationTask.account_id == account_id
    )
    invitation_tasks = (await session.exec(invitation_stmt)).first()

    return {
        "waiting_code": simple_tasks.waiting_code,
        "warm_up": simple_tasks.warm_up,
        "join": simple_tasks.join,
        "mail": simple_tasks.mail,
        "invite": simple_tasks.invite,
        "contact": contact_tasks,
        "join_group": join_group_tasks,
        "spam": spam_tasks,
        "invitation": invitation_tasks or "",
    }


#  BUG: https://github.com/fastapi/fastapi/pull/12942
class PatchBody(BaseModel):
    data: list[
        PatchWaitingCode
        | PatchWarmUp
        | PatchJoin
        | PatchMail
        | PatchInvite
        | PatchContact
        | PatchJoinGroup
        | PatchSpam
        | PatchInvitation
    ]


# https://datatracker.ietf.org/doc/html/rfc6902 but modifiend to use set-like lists
@router.patch("/", status_code=status.HTTP_204_NO_CONTENT)
async def update_tasks(account_id: int, operations: PatchBody, session: SessionDep):
    db_account = await session.get(Account, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    for operation in operations.data:
        match operation.path:
            case "/waiting_code":
                db_account.waiting_code = operation.value
                session.add(db_account)
            case "/warm_up":
                db_account.warm_up = operation.value
                session.add(db_account)
            case "/join":
                db_account.join = operation.value
                session.add(db_account)
            case "/invite":
                db_account.invite = operation.value
                session.add(db_account)
            case "/mail":
                db_account.mail = operation.value
                session.add(db_account)
            case "/contact":
                await patch_contact(account_id, operation, session)
            case "/join_group":
                await patch_join_group(account_id, operation, session)
            case "/spam":
                await patch_spam(account_id, operation, session)
            case "/invitation":
                await patch_invitation(account_id, operation, session)

    await session.commit()
