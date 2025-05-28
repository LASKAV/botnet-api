from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from models.group_link import (
    GroupLink,
    LinkPublic,
    LinkCreate,
    LinkUpdate,
    GroupLinkCreate,
)
from database import SessionDep
from models.tasks.join_group_task import JoinGroupTask
from models.account import Account


from sqlmodel import SQLModel

from models.limit import Limit

router = APIRouter(prefix="/group/links", tags=["Group Links"])


@router.post("")
async def create_group_link(template: LinkCreate, session: SessionDep) -> LinkPublic:
    group_link_stmt = select(GroupLink).where(GroupLink.link == template.link)
    result = await session.exec(group_link_stmt)
    existing_link = result.first()

    if existing_link:
        raise HTTPException(
            status_code=400, detail="A group link with this URL already exists!"
        )

    db_group_link = GroupLink.model_validate(template)
    session.add(db_group_link)

    await session.commit()
    await session.refresh(db_group_link)

    return db_group_link


@router.get("")
async def read_group_links(session: SessionDep) -> list[GroupLink]:
    statement = select(GroupLink)
    group_links = await session.exec(statement)
    return group_links.all()


class BulkLinkResponse(SQLModel):
    assigned_links: list[LinkPublic]


@router.post("/bulk")
async def create_group_links_bulk(links_data: GroupLinkCreate, session: SessionDep):
    created_links = []

    # Если передан day_limit или time_limit, обновляем их в таблице Limit
    if links_data.day_limit is not None or links_data.time_limit is not None:
        for account_id in links_data.account_id:
            stmt = select(Limit).where(
                Limit.account_id == account_id,
                Limit.action_type == "join_group"
            )
            result = await session.exec(stmt)
            limit_record = result.one_or_none()
            if limit_record is not None:
                if links_data.day_limit is not None:
                    old_day_limit = limit_record.day_limit
                    limit_record.day_limit = links_data.day_limit
                    limit_record.fact_limit = limit_record.fact_limit - old_day_limit + links_data.day_limit
                
                if links_data.time_limit is not None:
                    limit_record.time_limit = links_data.time_limit

                session.add(limit_record)
        await session.commit()

    # Создание или повторное использование записей GroupLink
    for link in links_data.link:
        stmt = select(GroupLink).where(GroupLink.link == link)
        result = await session.exec(stmt)
        existing_link = result.one_or_none()
        if existing_link is not None:
            db_link = existing_link
        else:
            db_link = GroupLink(link=link)
            session.add(db_link)
        created_links.append(db_link)

    await session.commit()

    # Обновляем объекты после коммита, чтобы загрузить атрибуты (например, id)
    for db_link in created_links:
        await session.refresh(db_link)

    if not links_data.account_id:
        raise HTTPException(status_code=400, detail="No account IDs provided!")

    # Для каждого аккаунта сохраняем ссылки в том же порядке и создаем задачи (связь многие ко многим)
    for account_id in links_data.account_id:

        stmt = select(Account).where(Account.id == account_id)
        result = await session.exec(stmt)
        account = result.one_or_none()
        account.join = True
        session.add(account)

        for db_link in created_links:
            join_task = JoinGroupTask(
                account_id=account_id, 
                group_link_id=db_link.id
            )
            session.add(join_task)
    await session.commit()



@router.get("/{link_id}")
async def read_group_link(link_id: int, session: SessionDep) -> GroupLink:
    link_stmt = select(GroupLink).where(GroupLink.id == link_id)
    result = await session.exec(link_stmt)
    db_link = result.first()
    if db_link is None:
        raise HTTPException(status_code=404, detail="Group link not found")

    return db_link


@router.patch("/{link_id}")
async def update_group_link(
    link_id: int, template: LinkUpdate, session: SessionDep
) -> LinkPublic:
    template_update_stmt = select(GroupLink).where(GroupLink.id == link_id)
    result = await session.exec(template_update_stmt)
    link_result = result.first()

    if link_result is None:
        raise HTTPException(status_code=404, detail="Group link not found")

    link_data = template.model_dump(exclude_unset=True)
    for key, value in link_data.items():
        setattr(link_result, key, value)

    session.add(link_result)
    await session.commit()
    await session.refresh(link_result)

    return link_result


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group_link(link_id: int, session: SessionDep):
    link_stmt = select(GroupLink).where(GroupLink.id == link_id)
    link_delete_result = await session.exec(link_stmt)
    link_delete = link_delete_result.first()

    if link_delete is None:
        raise HTTPException(status_code=404, detail="Group link not found")

    await session.delete(link_delete)
    await session.commit()
