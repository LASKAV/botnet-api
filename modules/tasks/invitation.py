from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import delete

from database import SessionDep
from models.tasks.invitation_task import InvitationTask
from .model.patch_ops import PatchInvitation


async def patch_invitation(
    account_id: int, operation: PatchInvitation, session: SessionDep
):
    if operation.op == "add":
        stmt = (
            pg_insert(InvitationTask)
            .values(account_id=account_id, target_link=operation.value)
            .on_conflict_do_nothing()
        )
        return await session.exec(stmt)

    if operation.op == "remove":
        stmt = (
            delete(InvitationTask)
            .where(InvitationTask.account_id == account_id)
            .where(InvitationTask.target_link == operation.value)
        )
        return await session.exec(stmt)

    if operation.op == "replace":
        delete_stmt = delete(InvitationTask).where(
            InvitationTask.account_id == account_id
        )
        await session.exec(delete_stmt)

        if operation.value:
            stmt = (
                pg_insert(InvitationTask)
                .values(account_id=account_id, target_link=operation.value)
                .on_conflict_do_nothing()
            )
            return await session.exec(stmt)
