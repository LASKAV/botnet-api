from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import col, delete, insert, literal, select

from database import SessionDep
from models.message_templates import MessageTemplates
from models.tasks.spammer_task import SpammerTask

from .model.patch_ops import PatchSpam

async def patch_spam(account_id: int, operation: PatchSpam, session: SessionDep):
    if operation.op == "add":
        stmt = (
            pg_insert(SpammerTask)
            .from_select(
                ["account_id", "message_template_id"],
                select(
                    literal(account_id),
                    col(MessageTemplates.id).label("message_template_id"),
                ).where(
                    col(MessageTemplates.message).in_(operation.value),
                ),
            )
            .on_conflict_do_nothing()
        )
        return await session.exec(stmt)
    if operation.op == "remove":
        stmt = (
            delete(SpammerTask)
            .where(SpammerTask.account_id == account_id)
            .where(SpammerTask.message_template_id == MessageTemplates.id)
            .where(col(MessageTemplates.message).in_(operation.value))
        )
        return await session.exec(stmt)
    if operation.op == "replace":
        delete_stmt = delete(SpammerTask).where(SpammerTask.account_id == account_id)
        await session.exec(delete_stmt)
        insert_stmt = insert(SpammerTask).values(
            [SpammerTask(account_id, value) for value in operation.value]
        )
        if len(operation.value) > 0:
            return await session.exec(insert_stmt)