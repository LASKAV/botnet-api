from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import col, delete, insert, literal, select

from database import SessionDep
from models.account import Account
from models.tasks.contact_task import ContactTask

from .model.patch_ops import PatchContact


async def patch_contact(account_id: int, operation: PatchContact, session: SessionDep):
    if operation.op == "add":
        stmt = (
            pg_insert(ContactTask)
            .from_select(
                ["account_id", "contact_id"],
                select(
                    literal(account_id),
                    col(Account.id).label("contact_id"),
                ).where(
                    col(Account.phone).in_(operation.value),
                ),
            )
            .on_conflict_do_nothing()
        )
        return await session.exec(stmt)

    if operation.op == "remove":
        stmt = (
            delete(ContactTask)
            .where(ContactTask.account_id == account_id)
            .where(ContactTask.contact_id == Account.id)
            .where(col(Account.phone).in_(operation.value))
        )
        return await session.exec(stmt)

    if operation.op == "replace":
        delete_stmt = delete(ContactTask).where(ContactTask.account_id == account_id)

        await session.exec(delete_stmt)

        insert_stmt = insert(ContactTask).values(
            [ContactTask(account_id, value) for value in operation.value]
        )

        if len(operation.value) > 0:
            return await session.exec(insert_stmt)
