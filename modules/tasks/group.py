from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import col, delete, insert, literal, select

from database import SessionDep
from models.group_link import GroupLink
from models.tasks.join_group_task import JoinGroupTask

from .model.patch_ops import PatchJoinGroup

async def patch_join_group(account_id: int, operation: PatchJoinGroup, session: SessionDep):
    if operation.op == "add":
        stmt = (
            pg_insert(JoinGroupTask)
            .from_select(
                ["account_id", "group_link_id"],
                select(
                    literal(account_id),
                    col(GroupLink.id).label("group_link_id"),
                ).where(
                    col(GroupLink.link).in_(operation.value),
                ),
            )
            .on_conflict_do_nothing()
        )
        return await session.exec(stmt)
    if operation.op == "remove":
        stmt = (
            delete(JoinGroupTask)
            .where(JoinGroupTask.account_id == account_id)
            .where(JoinGroupTask.group_link_id == GroupLink.id)
            .where(col(GroupLink.link).in_(operation.value))
        )
        return await session.exec(stmt)
    if operation.op == "replace":
        delete_stmt = delete(JoinGroupTask).where(JoinGroupTask.account_id == account_id)
        await session.exec(delete_stmt)
        insert_stmt = insert(JoinGroupTask).values(
            [JoinGroupTask(account_id, value) for value in operation.value]
        )
        if len(operation.value) > 0:
            return await session.exec(insert_stmt)